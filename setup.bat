@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Creating Django project...
django-admin startproject resume_analyzer_project .

echo Creating Django apps...
cd resume_analyzer_project
django-admin startapp core
django-admin startapp resume_analyzer

echo Setup complete!
echo To activate the virtual environment, run: venv\Scripts\activate
echo To start the development server, run: python manage.py runserver
