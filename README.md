# Resume Analyzer

A Django-based web application that analyzes resumes using AI and allows users to chat with their resume data.

## Features

- Upload and process PDF resumes
- Extract text from PDF files
- Create embeddings and store in Pinecone vector database
- Chat interface to ask questions about the resume
- Configurable AI model parameters (model, temperature, max tokens)
- Chat history persistence
- Responsive design with Bootstrap

## Tech Stack

- **Backend**: Django 4.2
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (development), PostgreSQL (production)
- **AI/ML**: LangChain, Groq, Pinecone, HuggingFace
- **Deployment**: Vercel

## Setup Instructions

### Prerequisites

- Python 3.9+
- Pinecone API key
- Groq API key

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd resume-analyzer
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:

   ```
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   GROQ_API_KEY=your-groq-api-key
   PINECONE_API_KEY=your-pinecone-api-key
   INDEX_NAME=your-pinecone-index-name
   ```

5. Run migrations:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser (optional):

   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:

   ```bash
   python manage.py runserver
   ```

8. Access the application at http://127.0.0.1:8000/

## Deployment to Vercel

1. Install Vercel CLI:

   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:

   ```bash
   vercel login
   ```

3. Deploy the application:

   ```bash
   vercel
   ```

4. Set environment variables in the Vercel dashboard.

## Usage

1. Upload a resume in PDF format
2. Wait for the processing to complete
3. Start asking questions about the resume
4. Adjust model parameters as needed for different types of responses

## Development Notes

### Version Control

The project includes a comprehensive `.gitignore` file that excludes:

- Virtual environment files
- Database files (SQLite)
- Media files (uploaded resumes)
- Compiled Python files
- Environment variable files (.env)
- Cache directories
- Log files
- Static files collected for production

This ensures that only the necessary code is committed to the repository, keeping it clean and secure.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
