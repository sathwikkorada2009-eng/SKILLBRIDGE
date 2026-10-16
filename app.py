import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from model import load_data, save_data
from tools import find_class, find_student


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
MAX_AUDIO_BYTES = 25 * 1024 * 1024
logger = logging.getLogger(__name__)

app = FastAPI(title="SkillBridge API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BookingRequest(BaseModel):
    student_name: str = Field(min_length=1, max_length=100)
    class_id: str = Field(min_length=1, max_length=20)


class MeetingLinkRequest(BaseModel):
    tutor_name: str = Field(min_length=1, max_length=100)
    link: str = Field(min_length=1, max_length=2048)


class RatingRequest(BaseModel):
    student_name: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=1, le=5)
    feedback: str = Field(default="", max_length=2000)


class DoubtRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)


def _data() -> dict[str, Any]:
    return load_data()


def _get_student(data: dict[str, Any], name: str) -> dict[str, Any]:
    student = find_student(data, name)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


def _get_class(data: dict[str, Any], class_id: str) -> dict[str, Any]:
    cls = find_class(data, class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found.")
    return cls


def _class_summary(cls: dict[str, Any]) -> dict[str, Any]:
    ratings = cls["ratings"]
    return {
        **cls,
        "seats_remaining": max(0, cls["capacity"] - len(cls["students"])),
        "average_rating": (
            round(sum(item["score"] for item in ratings) / len(ratings), 1)
            if ratings
            else None
        ),
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/students")
def students(skill: str = "") -> list[dict[str, Any]]:
    results = _data()["students"]
    if skill.strip():
        query = skill.strip().casefold()
        results = [
            student
            for student in results
            if any(query in item.casefold() for item in student["skills"])
        ]
    return results


@app.get("/api/classes")
def classes() -> list[dict[str, Any]]:
    return [_class_summary(cls) for cls in _data()["classes"]]


@app.get("/api/bookings")
def bookings(student_name: str) -> list[dict[str, Any]]:
    data = _data()
    student = _get_student(data, student_name)
    return [
        _class_summary(cls)
        for cls in data["classes"]
        if student["name"] in cls["students"]
    ]


@app.post("/api/bookings", status_code=201)
def book(request: BookingRequest) -> dict[str, Any]:
    data = _data()
    student = _get_student(data, request.student_name)
    cls = _get_class(data, request.class_id)

    if student["name"] == cls["tutor"]:
        raise HTTPException(status_code=400, detail="Tutors cannot book their own class.")
    if student["name"] in cls["students"]:
        raise HTTPException(status_code=409, detail="You have already booked this class.")
    if len(cls["students"]) >= cls["capacity"]:
        raise HTTPException(status_code=409, detail="Sorry, this class is full.")

    cls["students"].append(student["name"])
    save_data(data)
    return _class_summary(cls)


@app.put("/api/classes/{class_id}/meeting-link")
def update_meeting_link(
    class_id: str,
    request: MeetingLinkRequest,
) -> dict[str, str]:
    data = _data()
    cls = _get_class(data, class_id)
    if cls["tutor"].casefold() != request.tutor_name.strip().casefold():
        raise HTTPException(
            status_code=403,
            detail="Only the assigned tutor can update this link.",
        )

    parsed = urlparse(request.link.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise HTTPException(
            status_code=422,
            detail="Please enter a valid HTTPS meeting URL.",
        )

    cls["meeting_url"] = request.link.strip()
    save_data(data)
    return {"message": "Meeting link saved."}


@app.get("/api/classes/{class_id}/meeting")
def meeting(class_id: str, student_name: str) -> dict[str, str]:
    data = _data()
    student = _get_student(data, student_name)
    cls = _get_class(data, class_id)
    if student["name"] not in cls["students"]:
        raise HTTPException(status_code=403, detail="Book the class to access its meeting.")
    if not cls["meeting_url"]:
        raise HTTPException(
            status_code=404,
            detail="The tutor has not added a meeting link yet.",
        )
    return {"url": cls["meeting_url"]}


@app.get("/api/classes/{class_id}/ratings")
def ratings(class_id: str) -> list[dict[str, Any]]:
    cls = _get_class(_data(), class_id)
    return cls["ratings"]


@app.post("/api/classes/{class_id}/ratings", status_code=201)
def rate(class_id: str, request: RatingRequest) -> dict[str, Any]:
    data = _data()
    student = _get_student(data, request.student_name)
    cls = _get_class(data, class_id)

    if student["name"] not in cls["students"]:
        raise HTTPException(status_code=403, detail="Only enrolled students can rate this class.")
    if student["name"] == cls["tutor"]:
        raise HTTPException(status_code=403, detail="Tutors cannot rate their own class.")
    if any(item["student"] == student["name"] for item in cls["ratings"]):
        raise HTTPException(status_code=409, detail="You have already rated this class.")

    feedback = request.feedback.strip()
    cls["ratings"].append({
        "student": student["name"],
        "score": request.score,
        "feedback": feedback,
    })
    tutor = find_student(data, cls["tutor"])
    if tutor is not None:
        tutor["ratings"].append({
            "student": student["name"],
            "score": request.score,
            "class_id": cls["id"],
        })

    save_data(data)
    return _class_summary(cls)


@app.post("/api/classes/{class_id}/notes", status_code=201)
async def create_notes(
    class_id: str,
    tutor_name: str = Form(min_length=1, max_length=100),
    audio: UploadFile = File(...),
) -> dict[str, str]:
    data = _data()
    cls = _get_class(data, class_id)
    if cls["tutor"].casefold() != tutor_name.strip().casefold():
        raise HTTPException(
            status_code=403,
            detail="Only the assigned tutor can publish class notes.",
        )
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="AI notes are unavailable until OPENAI_API_KEY is configured.",
        )

    content = await audio.read(MAX_AUDIO_BYTES + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Choose a non-empty audio file.")
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Audio is larger than 25 MB. Split it into smaller parts.",
        )

    try:
        from openai import OpenAI

        client = OpenAI()
        transcription = client.audio.transcriptions.create(
            model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
            file=(audio.filename or "recording.mp3", content),
        )
        summary = client.responses.create(
            model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
            instructions=(
                "Create accurate study notes from this class transcript. Include a short "
                "overview, key concepts, definitions, examples, and action items. Do not "
                "invent facts. Mark unclear parts as uncertain."
            ),
            input=transcription.text,
        )
    except Exception as error:
        logger.exception("AI class-note generation failed")
        raise HTTPException(
            status_code=502,
            detail="AI note generation failed. Check the API key, connection, and audio format.",
        ) from error
    finally:
        await audio.close()

    cls["notes"].append({
        "published_at": datetime.now().isoformat(timespec="minutes"),
        "transcript": transcription.text,
        "summary": summary.output_text,
    })
    save_data(data)
    return {"message": "AI notes generated and published."}


@app.get("/api/classes/{class_id}/notes")
def notes(class_id: str, student_name: str) -> list[dict[str, str]]:
    data = _data()
    student = _get_student(data, student_name)
    cls = _get_class(data, class_id)
    if student["name"] not in cls["students"]:
        raise HTTPException(
            status_code=403,
            detail="Only enrolled students can access these notes.",
        )
    return [
        {"published_at": note["published_at"], "summary": note["summary"]}
        for note in cls["notes"]
    ]


@app.post("/api/ask")
def ask(request: DoubtRequest) -> dict[str, str]:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Please enter a question.")
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="The AI chatbot is unavailable until OPENAI_API_KEY is configured.",
        )

    try:
        from openai import OpenAI

        response = OpenAI().responses.create(
            model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
            instructions=(
                "You are SkillBridge's educational doubt assistant. Explain concepts "
                "clearly for college students, use simple examples, guide learners "
                "step by step, and admit uncertainty. Do not claim to be human."
            ),
            input=question,
        )
    except Exception as error:
        logger.exception("AI doubt response failed")
        raise HTTPException(
            status_code=502,
            detail="The AI service is unavailable right now. Please try again later.",
        ) from error
    return {"answer": response.output_text}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True, check_dir=False),
    name="frontend",
)
