import os
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .models import Resume, ChatMessage
from .forms import ResumeUploadForm, ChatMessageForm
from .utils import (
    load_resume,
    compute_file_hash,
    get_embeddings,
    clear_pinecone_data,
    query_resume
)

def home(request):
    """Home page view"""
    form = ResumeUploadForm()
    resumes = Resume.objects.all().order_by('-uploaded_at')

    return render(request, 'resume_analyzer/home.html', {
        'form': form,
        'resumes': resumes
    })

def upload_resume(request):
    """Handle resume upload"""
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']

            file_content = file.read()
            file_hash = compute_file_hash(file_content)
            file.seek(0)

            existing_resume = Resume.objects.filter(file_hash=file_hash).first()
            if existing_resume:
                messages.info(request, "This resume has already been uploaded. Using existing data.")
                return redirect('resume_detail', pk=existing_resume.pk)

            resume = form.save(commit=False)
            resume.original_filename = file.name
            resume.file_hash = file_hash
            resume.save()

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(file_content)
                    temp_path = temp_file.name

                resume_text = load_resume(temp_path)

                os.unlink(temp_path)

                if not resume_text or len(resume_text) < 10:
                    messages.error(request, "Could not extract text from this PDF. Please try another file.")
                    resume.delete()
                    return redirect('home')

                vector_store = get_embeddings(resume_text, resume.file_hash)

                messages.success(request, "Resume uploaded and processed successfully!")
                return redirect('resume_detail', pk=resume.pk)

            except Exception as e:
                messages.error(request, f"Error processing resume: {str(e)}")
                resume.delete()
                return redirect('home')
        else:
            messages.error(request, "There was an error with your submission. Please check the form.")
    else:
        form = ResumeUploadForm()

    return render(request, 'resume_analyzer/upload.html', {'form': form})

def resume_detail(request, pk):
    """Display resume details and chat interface"""
    import logging
    logger = logging.getLogger(__name__)

    resume = get_object_or_404(Resume, pk=pk)
    chat_form = ChatMessageForm()
    chat_messages = resume.chat_messages.all().order_by('timestamp')
    models = [
        {"id": "llama3-8b-8192", "name": "Llama 3 (8B)"},
        {"id": "llama3-70b-8192", "name": "Llama 3 (70B)"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"}
    ]

    try:
        if not request.session.get(f'resume_{pk}_preloaded', False):
            from langchain_pinecone import PineconeVectorStore
            import os
            from .models import EmbeddingModelSingleton, PineconeSingleton
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("Silently preloading resources for resume detail page")
            embedding_model = EmbeddingModelSingleton.get_instance().get_embedding_model()
            PineconeSingleton.get_instance().get_client()
            index_name = settings.INDEX_NAME or os.environ.get('INDEX_NAME')
            api_key = settings.PINECONE_API_KEY or os.environ.get('PINECONE_API_KEY')

            if index_name and api_key:
                os.environ['PINECONE_API_KEY'] = api_key
                namespace = resume.vector_namespace if resume.vector_namespace.strip() else None
                vector_store = PineconeVectorStore(
                    index_name=index_name,
                    embedding=embedding_model,
                    namespace=namespace
                )
                _ = vector_store.as_retriever()
                request.session[f'resume_{pk}_preloaded'] = True
                request.session.modified = True

                logger.info("Resources successfully preloaded")
        else:
            logger.info(f"Resume {pk} already preloaded according to session")

    except Exception as e:
        logger.error(f"Error preloading resources: {str(e)}")

    return render(request, 'resume_analyzer/detail.html', {
        'resume': resume,
        'chat_form': chat_form,
        'chat_messages': chat_messages,
        'models': models
    })

@require_POST
def chat_message(request, pk):
    """Handle chat message submission"""
    import logging
    logger = logging.getLogger(__name__)
    from dotenv import load_dotenv
    load_dotenv()

    resume = get_object_or_404(Resume, pk=pk)

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            # Save the user's message
            user_message = form.save(commit=False)
            user_message.resume = resume
            user_message.message_type = ChatMessage.HUMAN
            user_message.save()
            model = request.POST.get('model', 'llama3-8b-8192')
            temperature = float(request.POST.get('temperature', 0.0))
            max_tokens = int(request.POST.get('max_tokens', 1000))

            logger.info(f"Processing chat message for resume {pk} with model {model}")

            try:
                chat_history = []
                for msg in resume.chat_messages.all().order_by('timestamp'):
                    if msg.id != user_message.id:
                        chat_history.append({
                            "type": msg.message_type,
                            "content": msg.content
                        })

                from langchain_pinecone import PineconeVectorStore
                import os
                from .models import EmbeddingModelSingleton, PineconeSingleton

                index_name = settings.INDEX_NAME or os.environ.get('INDEX_NAME')

                if not index_name:
                    raise ValueError("Pinecone index name not found in settings or environment variables")
                if request.session.get(f'resume_{pk}_preloaded', False):
                    logger.info(f"Resume {pk} already preloaded according to session")
                else:
                    logger.info(f"Resume {pk} not marked as preloaded in session, setting flag")
                    request.session[f'resume_{pk}_preloaded'] = True
                    request.session.modified = True
                logger.info("Getting embedding model from singleton (should be preloaded)")
                embedding_model = EmbeddingModelSingleton.get_instance().get_embedding_model()
                logger.info("Getting Pinecone client from singleton (should be preloaded)")
                PineconeSingleton.get_instance().get_client()

                api_key = settings.PINECONE_API_KEY or os.environ.get('PINECONE_API_KEY')
                if not api_key:
                    raise ValueError("Pinecone API key not found in settings or environment variables")

                os.environ['PINECONE_API_KEY'] = api_key

                namespace = resume.vector_namespace if resume.vector_namespace.strip() else None
                logger.info(f"Using Pinecone index: {index_name}, namespace: {namespace}")
                logger.info(f"Creating vector store with index: {index_name}, namespace: {namespace}")
                vector_store = PineconeVectorStore(
                    index_name=index_name,
                    embedding=embedding_model,
                    namespace=namespace
                )
                response = query_resume(
                    query=user_message.content,
                    vector_store=vector_store,
                    chat_history=chat_history,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    resume_id=resume.file_hash
                )
                ai_message = ChatMessage(
                    resume=resume,
                    message_type=ChatMessage.AI,
                    content=response
                )
                ai_message.save()

                logger.info("Successfully processed chat message")
                return JsonResponse({
                    'status': 'success',
                    'user_message': user_message.content,
                    'ai_message': response
                })

            except Exception as e:
                logger.error(f"Error processing chat message: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
        else:
            logger.warning("Invalid form submission")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form submission'
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

def delete_resume(request, pk):
    """Delete a resume and its associated data"""
    import logging
    logger = logging.getLogger(__name__)

    resume = get_object_or_404(Resume, pk=pk)

    if request.method == 'POST':
        try:
            logger.info(f"Attempting to delete resume {pk}: {resume.original_filename}")

            namespace = resume.vector_namespace

            try:
                if namespace:
                    logger.info(f"Clearing Pinecone data for namespace: {namespace}")
                    clear_pinecone_data(settings.INDEX_NAME, namespace)
                else:
                    logger.warning("No namespace found for this resume, skipping Pinecone data clearing")
            except Exception as pinecone_error:
                logger.error(f"Error clearing Pinecone data: {str(pinecone_error)}")
                messages.warning(request, f"Warning: Could not clear vector data: {str(pinecone_error)}")

            logger.info(f"Deleting resume from database: {resume.original_filename}")
            resume.delete()

            messages.success(request, "Resume deleted successfully!")
            return redirect('home')
        except Exception as e:
            logger.error(f"Error deleting resume: {str(e)}")
            messages.error(request, f"Error deleting resume: {str(e)}")

    return render(request, 'resume_analyzer/delete.html', {'resume': resume})
