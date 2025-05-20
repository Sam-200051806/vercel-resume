from django import forms
from .models import Resume, ChatMessage

class ResumeUploadForm(forms.ModelForm):
    """Form for uploading a resume file"""
    class Meta:
        model = Resume
        fields = ['file']
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Only PDF files are allowed.")
            
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB.")
                
        return file

class ChatMessageForm(forms.ModelForm):
    """Form for submitting a chat message"""
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ask a question about the resume...',
                'autofocus': True
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = False
