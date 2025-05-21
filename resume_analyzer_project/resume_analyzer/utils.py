import os
import tempfile
from PyPDF2 import PdfReader

# Try to import pdf2image, but don't fail if it's not available
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not available. Some features may be limited.")
import hashlib
from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
import logging
import time
from functools import wraps

from .models import EmbeddingModelSingleton, PineconeSingleton

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Function {func.__name__} took {end_time - start_time:.2f} seconds to run")
        return result
    return wrapper

def load_resume(file_path):
    """Load and process a resume file"""
    try:
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            # If we got very little text, try using pdf2image if available
            if len(text.strip()) < 100 and PDF2IMAGE_AVAILABLE:
                try:
                    logger.info("Attempting to extract text using pdf2image as fallback")
                    # This part will only run if pdf2image is available
                    images = convert_from_path(file_path)
                    # Process images if needed
                except Exception as img_error:
                    logger.error(f"Error using pdf2image: {str(img_error)}")

            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def compute_file_hash(file_content):
    """Compute a hash for the file content to identify duplicate uploads"""
    return hashlib.md5(file_content).hexdigest()

@timing_decorator
def get_embeddings(resume_text, resume_id):
    """Create embeddings for the resume text and store in Pinecone"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.create_documents([resume_text])

    try:
        embedding_model = EmbeddingModelSingleton.get_instance().get_embedding_model()
    except Exception as e:
        logger.error(f"Error getting embedding model from singleton: {str(e)}")
        raise ValueError(f"Failed to get embedding model: {str(e)}")

    try:
        PineconeSingleton.get_instance().get_client()

        index_name = settings.INDEX_NAME or os.environ.get('INDEX_NAME')

        if not index_name:
            raise ValueError("Pinecone index name not found in settings or environment variables")

        namespace = f"resume_{resume_id}"

        logger.info(f"Storing vectors in Pinecone index: {index_name}, namespace: {namespace}")

        api_key = settings.PINECONE_API_KEY or os.environ.get('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("Pinecone API key not found in settings or environment variables")

        os.environ['PINECONE_API_KEY'] = api_key

        logger.info(f"Creating vector store with index: {index_name}, namespace: {namespace}")
        vector_store = PineconeVectorStore.from_documents(
            chunks,
            embedding=embedding_model,
            index_name=index_name,
            namespace=namespace
        )

        logger.info(f"Successfully stored {len(chunks)} chunks in Pinecone")
        return vector_store

    except Exception as e:
        logger.error(f"Error with Pinecone: {str(e)}")
        raise ValueError(f"Failed to create vector store: {str(e)}")

@timing_decorator
def clear_pinecone_data(index_name, namespace=None):
    """Clear existing vectors from Pinecone index"""
    if not index_name:
        logger.error("No index name provided to clear_pinecone_data")
        raise ValueError("Index name must be provided")

    try:
        pinecone_client = PineconeSingleton.get_instance().get_client()

        api_key = settings.PINECONE_API_KEY or os.environ.get('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("Pinecone API key not found in settings or environment variables")

        os.environ['PINECONE_API_KEY'] = api_key

        logger.info(f"Clearing Pinecone data from index {index_name}, namespace: {namespace}")

        try:
            index = pinecone_client.Index(index_name)
        except Exception as index_error:
            logger.error(f"Error getting Pinecone index: {str(index_error)}")
            raise ValueError(f"Could not access Pinecone index '{index_name}': {str(index_error)}")

        try:
            if namespace:
                logger.info(f"Deleting all vectors in namespace: {namespace}")
                index.delete(delete_all=True, namespace=namespace)
            else:
                logger.info("Deleting all vectors in the index (no namespace specified)")
                index.delete(delete_all=True)

            logger.info(f"Successfully cleared vectors from index {index_name}")
        except Exception as delete_error:
            logger.error(f"Error deleting vectors: {str(delete_error)}")
            raise ValueError(f"Failed to delete vectors: {str(delete_error)}")

    except Exception as e:
        logger.error(f"Error clearing Pinecone data: {str(e)}")
        raise ValueError(f"Failed to clear Pinecone data: {str(e)}")

_llm_cache = {}

@timing_decorator
def query_resume(query, vector_store, chat_history, model="llama3-8b-8192", temperature=0.0, max_tokens=1000, resume_id=None):
    """Query the resume using the vector store and LLM"""
    try:
        cache_key = f"{query}_{model}_{temperature}_{resume_id}"
        if temperature == 0.0 and cache_key in _llm_cache:
            logger.info(f"Using cached response for query: {query}")
            return _llm_cache[cache_key]
        groq_api_key = settings.GROQ_API_KEY or os.environ.get('GROQ_API_KEY')

        if not groq_api_key:
            raise ValueError("Groq API key not found in settings or environment variables")

        logger.info(f"Setting up LLM with model: {model}, temperature: {temperature}")
        llm = ChatGroq(
            api_key=groq_api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        formatted_chat_history = ""
        for message in chat_history:
            role = "User" if message["type"] == "human" else "Assistant"
            formatted_chat_history += f"{role}: {message['content']}\n"
        namespace = f"resume_{resume_id}" if resume_id else None
        logger.info(f"Creating retriever with namespace: {namespace}")
        retriever = vector_store.as_retriever(
            search_kwargs={"k": 5, "namespace": namespace}
        )
        logger.info(f"Retrieving documents for query: {query}")
        relevant_docs = retriever.get_relevant_documents(query)
        docs_content = "\n\n".join([doc.page_content for doc in relevant_docs])
        prompt = f"""
        You are an AI assistant analyzing a resume. Answer the question based on the resume content.

        Resume Content:
        {docs_content}

        Chat History:
        {formatted_chat_history}

        Question: {query}

        Answer:
        """
        logger.info("Sending query to LLM")
        response = llm.invoke(prompt)
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
        if temperature == 0.0:
            _llm_cache[cache_key] = result
            logger.info(f"Cached response for query: {query}")

        logger.info("Query completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error querying resume: {str(e)}")
        raise ValueError(f"Failed to query resume: {str(e)}")
