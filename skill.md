
# SkillBridge - Peer-to-Peer Learning Platform

## Overview
SkillBridge helps college students teach each other, book
learning sessions, access class resources, and resolve doubts.

## Features
- Student directory with skills and interests
- Search for students by subject
- Class slots with seat limits
- Booking management
- Meeting-link access for enrolled students
- Tutor and class ratings
- AI transcription of recorded classes
- AI-generated summaries and shared study notes
- AI doubt chatbot for independent learning
- JSON-based persistent storage

## Technology Stack
- Python 3.10+
- FastAPI web API and static HTML/CSS/JavaScript web interface
- OpenAI Python SDK
- OpenAI audio transcription API
- OpenAI text generation API
- JSON storage
- Git and GitHub

## Project Files
- main.py: Application menu
- model.py: Student/class data and storage
- tools.py: Bookings, ratings, notes, and chatbot
- app.py: FastAPI web API and static web app server
- frontend/: Vercel-ready web interface
- render.yaml: Render API deployment blueprint
- skill.md: Project documentation

## Setup
Install Python 3.10 or later and create/activate a virtual environment.

Install the dependencies:

    python -m pip install -r requirements.txt

Start the web app locally:

    python -m uvicorn app:app --reload

Open http://127.0.0.1:8000 in your browser. The original terminal app remains
available with `python main.py`.

To run the API tests, install `requirements-dev.txt` and run `python -m pytest`.

## Deployment
- **Render:** Create a new Blueprint from this repository and select
  `render.yaml`. The free service stores its JSON data in temporary storage;
  it can be lost when the service restarts or deploys. Use a persistent disk
  or managed database for data that must survive restarts.
- **Vercel:** Import the repository and set the project root directory to
  `frontend`. After deploying the API to Render, open the web app's settings
  (gear icon) and connect its `https://<your-render-service>.onrender.com`
  base URL. The browser app appends `/api`.
- Add `OPENAI_API_KEY` as a secret environment variable in Render to enable
  the AI tutor and audio-to-notes features. Never commit this key.
- Restrict API CORS to the deployed Vercel origin using Render's
  `CORS_ORIGINS` environment variable.

## Data Storage
Application data is saved to skillbridge_data.json.
Set `SKILLBRIDGE_DATA_FILE` to change the data file location (for example, to
a Render persistent disk mount).

Back up this file before modifying or resetting the data.

## Privacy
Only use class recordings with appropriate permission.
Do not publish private meeting links or personal information.
AI-generated notes should be checked for accuracy before sharing.

## Current Limitations
This is a demonstration prototype, not a production multi-user platform.
Student names are not authenticated; do not use it for private data or publish
real meeting links until proper authentication and authorization are added.
The JSON file is local by default and is not safe for concurrent multi-instance
production use.
The meeting URL must be provided by the class tutor.
AI features require API access and internet connectivity.

## Future Improvements
- Web interface using Flask or FastAPI
- Secure login and role-based permissions
- Shared cloud database
- Calendar integration
- Real-time video conferencing integration
- Live speech transcription
- Notes search and download
- Context-aware doubt chatbot
- Unit tests and GitHub Actions
