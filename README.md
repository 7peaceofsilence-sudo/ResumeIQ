# ResumeIQ — Resume Match Analyzer

A Flask web interface for your Groq + Pydantic resume analysis workflow. Upload multiple PDF/DOCX resumes, paste a job description, and view AI-generated match scores, matching skills, skill gaps, verdicts, and suggestions.

## Requirements
- Python 3.12 recommended
- A Groq API key
- Internet access for Groq API calls

## Setup (Windows PowerShell)

Activate your existing environment, from the project folder:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Put your API key in `.env`:

```dotenv
GROQ_API_KEY=your_actual_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

If `.env` already exists, do not overwrite it; simply add or update these entries.

Run:

```powershell
python app.py
```

Open http://127.0.0.1:5000

## Project structure

```text
Resume reader/
├── app.py
├── resume_engine.py
├── requirements.txt
├── .env
├── .env.example
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## Notes
- Uploaded files are held in a temporary directory and deleted after processing.
- The app currently accepts PDF and DOCX, up to 10 files and 10 MB per request.
- Scanned PDFs may need OCR; `pypdf` extracts embedded text, not text from images.
- Each resume uses two Groq model calls: parse resume and score against the job. The job description is parsed for each candidate in this starter implementation, which can increase latency/cost; it can be optimized by parsing the job once per batch.
- The output is an AI-assisted estimate, not a definitive hiring decision. Review results and avoid making decisions based only on an automated score.
- Do not commit `.env` or expose the API key.
- For local development, Flask debug mode is enabled. Turn it off before public deployment.
