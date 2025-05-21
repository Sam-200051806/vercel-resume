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

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_embedding_model(self):
        if self._model is None:
            logger.info("Loading embedding model (singleton instance)")
            try:
                self._model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-MiniLM-L3-v2"
                )
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading embedding model: {str(e)}")
                raise
        return self._model

class PineconeSingleton:
    """Singleton class for the Pinecone client to avoid creating new connections for each request"""
    _instance = None
    _client = None
    _initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self):
        if self._client is None:
            api_key = settings.PINECONE_API_KEY or os.environ.get('PINECONE_API_KEY')
            if not api_key:
                raise ValueError("Pinecone API key not found in settings or environment variables")

            logger.info("Initializing Pinecone client (singleton instance)")
            self._client = Pinecone(api_key=api_key)

            os.environ['PINECONE_API_KEY'] = api_key

            logger.info("Pinecone client initialized successfully")
            self._initialized = True
        return self._client

    def is_initialized(self):
        return self._initialized



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
