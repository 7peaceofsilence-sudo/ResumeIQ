
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from resume_engine import (
    GroqResumeEngine,
    extract_text_from_file,
    ResumeEngineError,
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

# Maximum combined upload size: 100 MB
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILES = 200


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def concise_error(exc: Exception) -> str:
    message = str(exc)
    return message[:220] + ("..." if len(message) > 220 else "")


def unique_filename(filename: str, index: int) -> str:
    """Create a safe filename that avoids collisions."""
    safe_name = secure_filename(Path(filename).name)

    if not safe_name:
        safe_name = f"resume_{index}.pdf"

    return f"{index}_{safe_name}"


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/")
def index():
    return render_template("index.html")


# --------------------------------------------------
# RESUME ANALYSIS
# --------------------------------------------------

@app.post("/analyze")
def analyze():
    job_description = request.form.get(
        "job_description", ""
    ).strip()

    all_uploads = [
        file
        for file in request.files.getlist("resumes")
        if file and file.filename
    ]

    errors = []
    results = []

    # Keep only supported resume formats.
    uploaded_files = [
        file for file in all_uploads
        if allowed_file(file.filename)
    ]

    unsupported_files = [
        file.filename for file in all_uploads
        if not allowed_file(file.filename)
    ]

    if not job_description:
        errors.append("Please paste the job description.")

    if not uploaded_files:
        errors.append(
            "Please select a folder containing PDF or DOCX resumes."
        )

    if len(uploaded_files) > MAX_FILES:
        errors.append(
            f"Please upload no more than {MAX_FILES} resumes at a time."
        )

    if unsupported_files:
        errors.append(
            "Skipped unsupported files: "
            + ", ".join(unsupported_files[:10])
            + (
                f" and {len(unsupported_files) - 10} more."
                if len(unsupported_files) > 10
                else ""
            )
        )

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        errors.append(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    if errors and (
        not job_description
        or not uploaded_files
        or len(uploaded_files) > MAX_FILES
        or not api_key
    ):
        return render_template(
            "index.html",
            errors=errors,
            job_description=job_description,
            results=results,
        ), 400

    # Initialize the AI engine.
    try:
        engine = GroqResumeEngine(
            api_key=api_key,
            model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-120b",
            ).strip(),
        )
    except Exception as exc:
        errors.append(f"Could not initialize AI engine: {concise_error(exc)}")
        return render_template(
            "index.html",
            errors=errors,
            job_description=job_description,
            results=results,
        ), 500

    # Parse the job description only once.
    try:
        parsed_job = engine.parse_job_description(job_description)
    except Exception as exc:
        errors.append(
            f"Job description analysis failed: {concise_error(exc)}"
        )
        return render_template(
            "index.html",
            errors=errors,
            job_description=job_description,
            results=results,
        ), 400

    # Process files in a temporary directory.
    with tempfile.TemporaryDirectory(prefix="resumeiq_") as temp_dir:
        temp_path = Path(temp_dir)

        for index, upload in enumerate(uploaded_files, start=1):
            safe_name = unique_filename(upload.filename, index)
            saved_path = temp_path / safe_name

            try:
                upload.save(saved_path)

                # Extract resume text.
                resume_text = extract_text_from_file(saved_path)

                if not resume_text or not resume_text.strip():
                    raise ResumeEngineError(
                        "No readable text found. Scanned PDFs may require OCR."
                    )

                # Parse resume into its structured model.
                parsed_resume = engine.parse_resume(resume_text)

                # Pass parsed models, not raw strings.
                match_result = engine.final_score(
                    parsed_job,
                    parsed_resume,
                )

                details = match_result.details or {}

                score = max(
                    0.0,
                    min(100.0, float(match_result.score)),
                )

                results.append({
                    "filename": upload.filename,
                    "name": (
                        parsed_resume.name
                        or details.get("candidate_name")
                        or details.get("name")
                        or Path(upload.filename).stem
                    ),
                    "score": score,
                    "details": details,
                    "skills": parsed_resume.skills,
                    "education": parsed_resume.education,
                    "experience_years": (
                        parsed_resume.total_experience_years
                    ),
                })

            except Exception as exc:
                errors.append(
                    f"{upload.filename}: {concise_error(exc)}"
                )

            finally:
                # Remove each temporary file after processing.
                saved_path.unlink(missing_ok=True)

    # Highest score first.
    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return render_template(
        "index.html",
        errors=errors,
        job_description=job_description,
        results=results,
        analyzed=True,
    )


# --------------------------------------------------
# UPLOAD SIZE ERROR
# --------------------------------------------------

@app.errorhandler(413)
def too_large(_error):
    return render_template(
        "index.html",
        errors=[
            "Upload exceeds 100 MB. Please choose a smaller folder."
        ],
        results=[],
    ), 413


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
