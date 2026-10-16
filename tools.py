
import os
from datetime import datetime
from urllib.parse import urlparse

from model import save_data


def find_student(data, name):
    name = name.strip().casefold()
    return next(
        (s for s in data["students"]
         if s["name"].casefold() == name),
        None,
    )


def find_class(data, class_id):
    return next(
        (c for c in data["classes"]
         if c["id"].casefold() == class_id.strip().casefold()),
        None,
    )


def show_students(data):
    print("\n=== STUDENT DIRECTORY ===")

    for student in data["students"]:
        ratings = student["ratings"]
        average = (
            sum(r["score"] for r in ratings) / len(ratings)
            if ratings else 0
        )

        print(f"\n{student['name']}")
        print("Teaches:", ", ".join(student["skills"]))
        print("Wants to learn:", ", ".join(student["interests"]))
        print("Availability:", student["availability"])
        print(f"Rating: {average:.1f}/5 ({len(ratings)} ratings)")


def search_students(data, subject):
    subject = subject.strip().casefold()

    matches = [
        student for student in data["students"]
        if any(subject in skill.casefold()
               for skill in student["skills"])
    ]

    if not matches:
        print("No students found for that skill.")
        return

    print(f"\nStudents who can teach {subject}:")
    for student in matches:
        print(f"- {student['name']}: {', '.join(student['skills'])}")


def show_classes(data):
    print("\n=== AVAILABLE CLASSES ===")

    for cls in data["classes"]:
        booked = len(cls["students"])
        remaining = cls["capacity"] - booked

        print(f"\nID: {cls['id']} | {cls['title']}")
        print(f"Tutor: {cls['tutor']}")
        print(f"Subject: {cls['subject']}")
        print(f"Slot: {cls['slot']}")
        print(f"Seats remaining: {remaining}/{cls['capacity']}")


def book_class(data, student_name, class_id):
    student = find_student(data, student_name)
    cls = find_class(data, class_id)

    if not student:
        print("Student not found. Use a name in the student directory.")
        return

    if not cls:
        print("Class not found.")
        return

    if student["name"] == cls["tutor"]:
        print("Tutors cannot book their own class.")
        return

    if student["name"] in cls["students"]:
        print("You have already booked this class.")
        return

    if len(cls["students"]) >= cls["capacity"]:
        print("Sorry, this class is full.")
        return

    cls["students"].append(student["name"])
    save_data(data)
    print(f"Booking confirmed for {student['name']}!")
    print(f"Class: {cls['title']} | Slot: {cls['slot']}")


def show_bookings(data, student_name):
    student = find_student(data, student_name)

    if not student:
        print("Student not found.")
        return

    found = False
    print(f"\n=== BOOKINGS FOR {student['name']} ===")

    for cls in data["classes"]:
        if student["name"] in cls["students"]:
            found = True
            print(
                f"{cls['id']} - {cls['title']} "
                f"| {cls['slot']}"
            )

    if not found:
        print("No bookings found.")


def set_meeting_link(data, class_id, tutor_name, link):
    cls = find_class(data, class_id)

    if not cls:
        print("Class not found.")
        return

    if cls["tutor"].casefold() != tutor_name.strip().casefold():
        print("Only the assigned tutor can update this link.")
        return

    parsed = urlparse(link.strip())

    if parsed.scheme != "https" or not parsed.netloc:
        print("Please enter a valid HTTPS meeting URL.")
        return

    cls["meeting_url"] = link.strip()
    save_data(data)
    print("Meeting link saved.")


def access_meeting(data, student_name, class_id):
    student = find_student(data, student_name)
    cls = find_class(data, class_id)

    if not student or not cls:
        print("Student or class not found.")
        return

    if student["name"] not in cls["students"]:
        print("Access denied. Book the class first.")
        return

    if not cls["meeting_url"]:
        print("The tutor has not added a meeting link yet.")
        return

    print(f"Meeting link for {cls['title']}:")
    print(cls["meeting_url"])
    print("Open the link in your browser to join.")


def rate_class(data, student_name, class_id, score, feedback):
    student = find_student(data, student_name)
    cls = find_class(data, class_id)

    if not student or not cls:
        print("Student or class not found.")
        return

    if student["name"] not in cls["students"]:
        print("Only enrolled students can rate this class.")
        return

    if student["name"] == cls["tutor"]:
        print("Tutors cannot rate their own class.")
        return

    if not isinstance(score, int) or not 1 <= score <= 5:
        print("Rating must be a whole number from 1 to 5.")
        return

    if any(r["student"] == student["name"] for r in cls["ratings"]):
        print("You have already rated this class.")
        return

    cls["ratings"].append({
        "student": student["name"],
        "score": score,
        "feedback": feedback.strip(),
    })

    tutor = find_student(data, cls["tutor"])
    if tutor:
        tutor["ratings"].append({
            "student": student["name"],
            "score": score,
            "class_id": cls["id"],
        })

    save_data(data)
    print("Thank you! Your rating has been saved.")


def show_class_ratings(data, class_id):
    cls = find_class(data, class_id)

    if not cls:
        print("Class not found.")
        return

    ratings = cls["ratings"]

    if not ratings:
        print("This class has no ratings yet.")
        return

    average = sum(r["score"] for r in ratings) / len(ratings)
    print(f"\n{cls['title']}: {average:.1f}/5")
    print(f"Total ratings: {len(ratings)}")

    for rating in ratings:
        print(f"- {rating['score']}/5: {rating['feedback']}")


def summarize_transcript(transcript):
    """Use an AI model to create concise class notes."""
    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")

    response = client.responses.create(
        model=model,
        instructions=(
            "Create accurate study notes from the class transcript. "
            "Include a short overview, key concepts, definitions, "
            "examples, and action items. Use headings and bullet points. "
            "Do not invent facts. Mark unclear parts as uncertain."
        ),
        input=transcript,
    )

    return response.output_text


def create_class_notes(data, tutor_name, class_id, audio_path):
    """Transcribe a class recording and publish shared notes."""
    cls = find_class(data, class_id)

    if not cls:
        print("Class not found.")
        return

    if cls["tutor"].casefold() != tutor_name.strip().casefold():
        print("Only the assigned tutor can publish class notes.")
        return

    if not os.path.isfile(audio_path):
        print("Audio file not found.")
        return

    if os.path.getsize(audio_path) > 25 * 1024 * 1024:
        print("Audio is larger than 25 MB. Split it into smaller parts.")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to enable AI transcription.")
        return

    try:
        from openai import OpenAI

        client = OpenAI()
        transcription_model = os.getenv(
            "OPENAI_TRANSCRIBE_MODEL",
            "gpt-4o-mini-transcribe",
        )

        with open(audio_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=transcription_model,
                file=audio_file,
            )

        transcript = result.text
        notes = summarize_transcript(transcript)

        cls["notes"].append({
            "published_at": datetime.now().isoformat(timespec="minutes"),
            "transcript": transcript,
            "summary": notes,
        })

        save_data(data)

        print("\nAI notes generated and published!")
        print("All enrolled students can access these notes.")

    except Exception as error:
        print("AI note generation failed.")
        print("Check your API key, internet connection, and audio format.")
        print(f"Technical detail: {error}")


def view_class_notes(data, student_name, class_id):
    student = find_student(data, student_name)
    cls = find_class(data, class_id)

    if not student or not cls:
        print("Student or class not found.")
        return

    if student["name"] not in cls["students"]:
        print("Only enrolled students can access these notes.")
        return

    if not cls["notes"]:
        print("No notes have been published for this class yet.")
        return

    for index, note in enumerate(cls["notes"], start=1):
        print(f"\n=== CLASS NOTES {index} ===")
        print("Published:", note["published_at"])
        print(note["summary"])


def ask_doubt_bot(question, class_id=None):
    """Answer doubts with AI, or use a simple fallback offline."""
    question = question.strip()

    if not question:
        print("Please enter a question.")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "AI chatbot is not configured. "
            "Add an API key to enable AI answers."
        )
        print("For now, try searching the class notes or student directory.")
        return

    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(
            model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
            instructions=(
                "You are SkillBridge's educational doubt assistant. "
                "Explain concepts clearly for college students. "
                "Use simple examples, guide the learner step by step, "
                "and admit when you are uncertain. Do not claim to be "
                "a human tutor."
            ),
            input=question,
        )

        print("\nSkillBridge AI:", response.output_text)

    except Exception as error:
        print("The AI service is unavailable right now.")
        print("Please try again later or consult the published notes.")
        print(f"Technical detail: {error}")
