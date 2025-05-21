from django.db import models
import hashlib
import os
from django.conf import settings
from django.utils import timezone
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
import logging

logger = logging.getLogger(__name__)

class EmbeddingModelSingleton:
    """Singleton class for the embedding model to avoid reloading it for each request"""
    _instance = None
    _model = None
    _model_load_attempted = False
    _fallback_mode = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_embedding_model(self):
        # If we've already tried and failed to load the model, use fallback mode
        if self._fallback_mode:
            logger.warning("Using fallback embedding function due to previous model loading failure")
            return self._get_fallback_embedding_model()

        # If model is already loaded, return it
        if self._model is not None:
            return self._model

        # If we haven't tried loading the model yet, try now
        if not self._model_load_attempted:
            self._model_load_attempted = True
            logger.info("Loading embedding model (singleton instance)")

            try:
                # Try to load with lower memory footprint
                import os
                # Set environment variables to reduce memory usage
                os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
                os.environ['TORCH_HOME'] = '/tmp/torch_home'

                # Try to load the model with a smaller, more efficient version
                self._model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True}
                )
                logger.info("Embedding model loaded successfully")
                return self._model
            except Exception as e:
                logger.error(f"Error loading embedding model: {str(e)}")
                logger.warning("Switching to fallback embedding function")
                self._fallback_mode = True
                return self._get_fallback_embedding_model()

        # This should not happen, but just in case
        logger.warning("Unexpected state in embedding model loading, using fallback")
        self._fallback_mode = True
        return self._get_fallback_embedding_model()

    def _get_fallback_embedding_model(self):
        """Provide a simple fallback embedding function that doesn't require heavy ML libraries"""
        class FallbackEmbeddings:
            def embed_documents(self, texts):
                """Simple fallback embedding function using hash-based approach"""
                import hashlib
                import numpy as np

                # Create a simple embedding based on hash of text
                # This is not semantically meaningful but allows the app to function
                def hash_embed(text):
                    hash_obj = hashlib.md5(text.encode())
                    hash_bytes = hash_obj.digest()
                    # Convert 16 bytes to 64 floats (dimension of 64)
                    embedding = np.zeros(64, dtype=np.float32)
                    for i, byte in enumerate(hash_bytes):
                        if i < 16:  # Use each byte to set 4 values
                            for j in range(4):
                                idx = i * 4 + j
                                embedding[idx] = (byte & (1 << j)) / 255.0
                    # Normalize
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    return embedding.tolist()

                return [hash_embed(text) for text in texts]

            def embed_query(self, text):
                """Embed a single query text"""
                return self.embed_documents([text])[0]

        logger.info("Created fallback embedding model")
        return FallbackEmbeddings()

class PineconeSingleton:
    """Singleton class for the Pinecone client to avoid creating new connections for each request"""
    _instance = None
    _client = None
    _initialized = False
    _client_load_attempted = False
    _fallback_mode = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self):
        # If we're in fallback mode, return the mock client
        if self._fallback_mode:
            logger.warning("Using fallback Pinecone client due to previous initialization failure")
            return self._get_fallback_client()

        # If client is already initialized, return it
        if self._client is not None:
            return self._client

        # If we haven't tried initializing the client yet, try now
        if not self._client_load_attempted:
            self._client_load_attempted = True

            try:
                api_key = settings.PINECONE_API_KEY or os.environ.get('PINECONE_API_KEY')
                if not api_key:
                    logger.error("Pinecone API key not found in settings or environment variables")
                    self._fallback_mode = True
                    return self._get_fallback_client()

                logger.info("Initializing Pinecone client (singleton instance)")
                self._client = Pinecone(api_key=api_key)
                os.environ['PINECONE_API_KEY'] = api_key
                logger.info("Pinecone client initialized successfully")
                self._initialized = True
                return self._client
            except Exception as e:
                logger.error(f"Error initializing Pinecone client: {str(e)}")
                logger.warning("Switching to fallback Pinecone client")
                self._fallback_mode = True
                return self._get_fallback_client()

        # This should not happen, but just in case
        logger.warning("Unexpected state in Pinecone client initialization, using fallback")
        self._fallback_mode = True
        return self._get_fallback_client()

    def is_initialized(self):
        return self._initialized or self._fallback_mode

    def _get_fallback_client(self):
        """Provide a simple fallback Pinecone client that doesn't require actual Pinecone service"""
        class FallbackPineconeIndex:
            def __init__(self):
                self.vectors = {}

            def upsert(self, vectors, namespace=None, **kwargs):
                """Mock upsert method that stores vectors in memory"""
                namespace = namespace or ""
                if namespace not in self.vectors:
                    self.vectors[namespace] = {}

                for vector in vectors:
                    self.vectors[namespace][vector['id']] = {
                        'id': vector['id'],
                        'values': vector['values'],
                        'metadata': vector.get('metadata', {})
                    }
                return {"upserted_count": len(vectors)}

            def query(self, vector, namespace=None, top_k=10, **kwargs):
                """Mock query method that returns random results"""
                import random
                namespace = namespace or ""
                if namespace not in self.vectors or not self.vectors[namespace]:
                    return {"matches": []}

                # Get available vectors
                available = list(self.vectors[namespace].values())
                # Select random subset (up to top_k)
                count = min(top_k, len(available))
                selected = random.sample(available, count) if count > 0 else []

                # Create mock scores
                matches = []
                for i, item in enumerate(selected):
                    score = 1.0 - (i * 0.1)  # Decreasing scores
                    matches.append({
                        "id": item["id"],
                        "score": max(0.1, score),
                        "metadata": item.get("metadata", {})
                    })

                return {"matches": matches}

            def delete(self, ids=None, namespace=None, **kwargs):
                """Mock delete method"""
                namespace = namespace or ""
                if namespace not in self.vectors:
                    return

                if ids:
                    for id in ids:
                        if id in self.vectors[namespace]:
                            del self.vectors[namespace][id]
                else:
                    # Delete all in namespace
                    self.vectors[namespace] = {}

        class FallbackPineconeClient:
            def __init__(self):
                self.indexes = {}

            def Index(self, name):
                """Return a mock index"""
                if name not in self.indexes:
                    self.indexes[name] = FallbackPineconeIndex()
                return self.indexes[name]

        logger.info("Created fallback Pinecone client")
        return FallbackPineconeClient()



def resume_upload_path(instance, filename):
    """Generate a unique path for uploaded resumes"""
    hash_obj = hashlib.md5(f"{filename}{timezone.now()}".encode())
    hashed_name = hash_obj.hexdigest()
    ext = filename.split('.')[-1]
    return os.path.join('resumes', f"{hashed_name}.{ext}")

class Resume(models.Model):
    """Model to store uploaded resume files and their metadata"""
    file = models.FileField(upload_to=resume_upload_path)
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    vector_namespace = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.original_filename

    def save(self, *args, **kwargs):
        if not self.file_hash and self.file:
            file_content = self.file.read()
            self.file_hash = hashlib.md5(file_content).hexdigest()
            self.file.seek(0)

            self.vector_namespace = f"resume_{self.file_hash}"

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            if self.file and hasattr(self.file, 'path'):
                file_path = self.file.path
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Successfully deleted file: {file_path}")
                else:
                    logger.warning(f"File not found for deletion: {file_path}")
            else:
                logger.warning("No file associated with this resume or file path not available")
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")

        super().delete(*args, **kwargs)

class ChatMessage(models.Model):
    """Model to store chat messages for a resume"""
    HUMAN = 'human'
    AI = 'ai'

    MESSAGE_TYPES = [
        (HUMAN, 'Human'),
        (AI, 'AI'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='chat_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."
