
import json
import os
from pathlib import Path

DATA_FILE = Path(
    os.getenv("SKILLBRIDGE_DATA_FILE", Path(__file__).with_name("skillbridge_data.json"))
)

STUDENT_NAMES = [
    "Aarav Sharma", "Priya Reddy", "Rahul Kumar", "Ananya Patel",
    "Arjun Rao", "Sneha Verma", "Vikram Singh", "Meera Nair",
    "Kiran Das", "Ishita Gupta", "Rohan Mehta", "Divya Iyer",
    "Aditya Joshi", "Pooja Shah", "Sai Krishna", "Neha Kapoor",
    "Varun Malhotra", "Kavya Menon", "Nikhil Jain", "Sana Khan",
    "Manoj Reddy", "Aditi Bose", "Harish Kumar", "Tanya Roy",
    "Abhishek Rao",
]

SKILLS = [
    ["Python", "SQL"], ["Java", "Python"], ["HTML", "CSS"],
    ["JavaScript", "React"], ["Python", "Machine Learning"],
    ["C++", "Data Structures"], ["SQL", "Excel"],
    ["Java", "Data Structures"], ["Python", "Flask"],
    ["HTML", "CSS", "JavaScript"], ["React", "JavaScript"],
    ["Python", "Statistics"], ["C++", "Algorithms"],
    ["UI Design", "HTML"], ["Java", "Spring Boot"],
    ["Python", "SQL"], ["Machine Learning", "Python"],
    ["CSS", "JavaScript"], ["Data Structures", "Java"],
    ["Communication", "Presentation"], ["Python", "Django"],
    ["SQL", "Database Design"], ["C++", "Python"],
    ["UI Design", "Figma"], ["JavaScript", "Node.js"],
]

INTERESTS = [
    ["Machine Learning"], ["Web Development"], ["Python"],
    ["Backend Development"], ["Statistics"], ["Java"],
    ["Python"], ["Web Development"], ["Data Science"],
    ["React"], ["Python"], ["Machine Learning"],
    ["Web Development"], ["JavaScript"], ["SQL"],
    ["Data Science"], ["AI"], ["React"],
    ["Algorithms"], ["Python"], ["Web Development"],
    ["Data Science"], ["Java"], ["UI Design"],
    ["Python"],
]


def create_initial_data():
    students = []

    for i, name in enumerate(STUDENT_NAMES):
        students.append({
            "name": name,
            "skills": SKILLS[i],
            "interests": INTERESTS[i],
            "availability": "Evenings" if i % 2 else "Weekends",
            "ratings": [],
        })

    classes = [
        {
            "id": "C101",
            "title": "Python Programming Basics",
            "subject": "Python",
            "tutor": "Aarav Sharma",
            "slot": "Saturday 10:00 AM",
            "capacity": 10,
            "students": [],
            "meeting_url": "",
            "notes": [],
            "ratings": [],
        },
        {
            "id": "C102",
            "title": "Web Development Fundamentals",
            "subject": "HTML",
            "tutor": "Priya Reddy",
            "slot": "Saturday 2:00 PM",
            "capacity": 12,
            "students": [],
            "meeting_url": "",
            "notes": [],
            "ratings": [],
        },
        {
            "id": "C103",
            "title": "Data Structures and Algorithms",
            "subject": "Data Structures",
            "tutor": "Vikram Singh",
            "slot": "Sunday 10:00 AM",
            "capacity": 8,
            "students": [],
            "meeting_url": "",
            "notes": [],
            "ratings": [],
        },
        {
            "id": "C104",
            "title": "Introduction to Machine Learning",
            "subject": "Machine Learning",
            "tutor": "Ananya Patel",
            "slot": "Sunday 2:00 PM",
            "capacity": 10,
            "students": [],
            "meeting_url": "",
            "notes": [],
            "ratings": [],
        },
        {
            "id": "C105",
            "title": "SQL and Database Basics",
            "subject": "SQL",
            "tutor": "Meera Nair",
            "slot": "Monday 5:00 PM",
            "capacity": 15,
            "students": [],
            "meeting_url": "",
            "notes": [],
            "ratings": [],
        },
    ]

    return {
        "students": students,
        "classes": classes,
        "requests": [],
    }


def load_data():
    if not DATA_FILE.exists():
        data = create_initial_data()
        save_data(data)
        return data

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for key in ("students", "classes", "requests"):
            if key not in data:
                raise ValueError(f"Missing data section: {key}")

        return data

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Cannot read {DATA_FILE.name}. "
            "Restore a valid backup before continuing."
        ) from error


def save_data(data):
    temporary_file = DATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temporary_file.replace(DATA_FILE)
