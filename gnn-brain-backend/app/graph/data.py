"""Deterministic demo school, reporting lines, and node-owned records."""

from dataclasses import dataclass

SECTIONS = tuple("ABCDE")
CLASS_SIZE = 35


@dataclass(frozen=True)
class Subject:
    key: str
    label: str
    vocabulary: str
    examples: tuple[str, ...]


SUBJECTS = (
    Subject("science", "Science", "physics chemistry biology laboratory lab experiment science goggles practical",
            ("Where is the science practical?", "I have a chemistry lab question", "Physics experiment")),
    Subject("math", "Mathematics", "math maths mathematics algebra geometry calculus arithmetic assignment olympiad",
            ("When is the mathematics assignment due?", "When is the algebra deadline?", "Geometry homework")),
    Subject("english", "English", "english literature essay reading speech language debate",
            ("What is the English essay deadline?", "Where is the debate tryout?", "Literature reading")),
    Subject("computing", "Computing",
            "computer computing coding code programming robotics python software internet projector screen display password laptop portal",
            ("When is the coding workshop?", "I have a robotics question", "Python programming", "The projector is broken")),
    Subject("sports", "Physical Education", "sports football soccer cricket basketball athletics fitness pe practice trials coach kit trainers",
            ("When are football trials?", "I have a sports question", "Basketball practice")),
)
DEFAULT_SUBJECT = SUBJECTS[0]
GENERAL_EXAMPLES = ("When is Founders Day?", "Where is the assembly?", "What is the attendance policy?",
                    "I have a problem", "When is the event?", "I need help", "Is the campus open?")


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    role: str
    text: str
    section: str | None = None
    subject: str | None = None
    roll: int | None = None


@dataclass(frozen=True)
class Record:
    topic: str
    owner: str
    title: str
    aliases: tuple[str, ...]
    answer: str
    reference: str
    section: str | None = None
    example: str | None = None
    local_only: bool = False


NODES = [
    Node("director", "Dr. Leena Menon", "Director", "Oversees campus-wide policy and school operations."),
    Node("dean", "Dr. Vikram Rao", "Dean", "Owns campus events and academic notices across departments."),
]
LINKS: list[tuple[str, str]] = [("dean", "director")]
RECORDS = [
    Record("founders-day", "dean", "Founders Day schedule",
           ("founders day", "founder day", "foundersday", "foundation day", "annual day", "college fest", "school fest"),
           "Founders Day is on 11 December 2026 at 10:00 a.m. in the main auditorium. Student check-in opens at 9:30 a.m.",
           "Dean’s events bulletin"),
    Record("attendance", "director", "Attendance policy",
           ("attendance", "absences", "absent", "minimum attendance"),
           "Students need at least 75% attendance in each subject. If you expect an extended absence, ask your class in-charge how to file a leave request.",
           "Director’s student handbook"),
    Record("coding", "hod-computing", "Coding workshop",
           ("coding workshop", "coding bootcamp", "programming workshop", "robotics workshop", "coding"),
           "The coding workshop is on 4 December 2026 at 2:00 p.m. in Computer Lab 2. Sign up with your class representative.",
           "Computing department circular"),
    Record("football", "hod-sports", "Football trials",
           ("football trials", "football tryouts", "football", "soccer trials", "sports trials"),
           "Football trials start on 3 December 2026 at 4:00 p.m. on the main school field. Bring your student ID and sports shoes.",
           "Physical Education trials notice"),
]

HEAD_NAMES = ("Dr. Neha Iyer", "Dr. Arun Shah", "Dr. Meera Das", "Dr. Kabir Sethi", "Coach Asha Bose")
TEACHER_NAMES = (
    ("Ms. Priya Nair", "Mr. Rohan Sen", "Ms. Anita Rao", "Mr. Dev Patel", "Ms. Isha Mehta"),
    ("Mr. Amit Joshi", "Ms. Nisha Shah", "Ms. Sana Khan", "Mr. Adil Das", "Mr. Raj Malik"),
    ("Ms. Alia Verma", "Mr. Kunal Bose", "Mr. Ravi Nair", "Ms. Jaya Iyer", "Ms. Ruhi Sen"),
    ("Mr. Hari Rao", "Ms. Sia Sharma", "Ms. Nina David", "Mr. Kiran Gupta", "Mr. Om Desai"),
    ("Ms. Tara Mehta", "Mr. Anil Reddy", "Ms. Ira Thomas", "Ms. Veena Sethi", "Ms. Anu Singh"),
)
FIRST_NAMES = ("Myra", "Aarav", "Diya", "Vihaan", "Ananya", "Ishaan", "Kavya", "Riya", "Arjun", "Saanvi",
               "Nikhil", "Zoya", "Aditi", "Reyansh", "Sara", "Mira", "Samir", "Tara", "Neel", "Aanya")
LAST_NAMES = ("Sharma", "Chopra", "Sen", "Gupta", "Verma", "Reddy", "Iyer", "Patel", "Joshi")

for subject, name in zip(SUBJECTS, HEAD_NAMES):
    head_id = f"hod-{subject.key}"
    NODES.append(Node(head_id, name, "HOD", f"Head of {subject.label}. Handles department notices and escalations.",
                      subject=subject.key))
    LINKS.append((head_id, "dean"))

for class_index, section in enumerate(SECTIONS):
    cr_id = f"CR-{section}"
    for roll in range(1, CLASS_SIZE + 1):
        student_id = cr_id if roll == CLASS_SIZE else f"S-{section}-{roll}"
        name_index = class_index * CLASS_SIZE + roll - 1
        first = FIRST_NAMES[name_index % len(FIRST_NAMES)]
        last = LAST_NAMES[name_index // len(FIRST_NAMES)]
        name = {0: "Myra Chopra", 20: "Myra Sharma"}.get(name_index, f"{first} {last}")
        role = "CR" if student_id == cr_id else "Student"
        text = (f"Represents Class {section} and keeps its announcements."
                if role == "CR" else f"Student in Class {section}, roll {roll}.")
        NODES.append(Node(student_id, name, role, text, section=section, roll=roll))
        if role == "Student":
            LINKS.append((student_id, cr_id))

    for subject, name in zip(SUBJECTS, TEACHER_NAMES[class_index]):
        teacher_id = f"incharge-{section}-{subject.key}"
        NODES.append(Node(teacher_id, name, "In-charge",
                          f"Class {section} in-charge for {subject.label}.", section, subject.key))
        LINKS.extend(((cr_id, teacher_id), (teacher_id, f"hod-{subject.key}")))

    room = 101 + class_index
    RECORDS.extend((
        Record("assembly", cr_id, f"Class {section} assembly instructions",
               ("assembly", "morning assembly", "where do we line up", "line up"),
               f"Class {section} meets outside Room {room} at 8:15 a.m. on assembly days.",
               f"Class {section} representative notice", section),
        Record("math-assignment", f"incharge-{section}-math", f"Class {section} maths assignment",
               ("mathematics assignment", "math assignment", "maths assignment", "algebra homework",
                "algebra assignment", "assignment deadline", "assignment due", "homework due", "math homework",
                "maths homework", "algebra deadline", "submit my assignment"),
               f"Class {section}’s algebra worksheet is due on {2 + class_index} December 2026 at 3:00 p.m. "
               f"Submit it to your mathematics in-charge in Room {room}.",
               f"Class {section} mathematics assignment sheet", section),
        Record("science-practical", f"incharge-{section}-science", f"Class {section} science practical",
               ("science practical", "science lab", "chemistry practical", "physics lab", "lab practical", "lab"),
               f"Class {section}’s science practical starts at 11:00 a.m. on {7 + class_index} December 2026 in Science Lab 1.",
               f"Class {section} laboratory timetable", section),
        Record("english-essay", f"incharge-{section}-english", f"Class {section} English essay",
               ("english essay", "essay", "literature assignment", "essay deadline"),
               f"Class {section}’s English essay is due on {7 + class_index} December 2026. Submit it to your English in-charge.",
               f"Class {section} English assignment sheet", section),
        Record("classroom-equipment", f"incharge-{section}-computing", f"Class {section} classroom equipment",
               ("projector", "display is broken", "classroom screen", "classroom computer"),
               f"For classroom equipment problems, give your CR the room number and a short description. "
               f"{TEACHER_NAMES[class_index][3]}, your Computing in-charge, can arrange a repair. "
               f"Class {section} can use its assigned Room {room} whiteboard while the equipment is unavailable.",
               f"Class {section} equipment support guide", section),
    ))

SCENARIOS = (
    {"label": "Founders Day schedule", "question": "When is Founders Day?", "role": "Dean"},
    {"label": "Morning assembly", "question": "Where is our morning assembly?", "role": "CR"},
    {"label": "Maths assignment", "question": "When is the maths assignment due?", "role": "In-charge", "subject": "math"},
    {"label": "Coding workshop", "question": "When is the coding workshop?", "role": "HOD", "subject": "computing"},
    {"label": "Attendance policy", "question": "What is the attendance policy?", "role": "Director"},
    {"label": "Broken projector", "question": "Our classroom projector is broken. What should I do?", "role": "In-charge",
     "subject": "computing"},
    {"label": "Science practical", "question": "Where is the science practical?", "role": "In-charge", "subject": "science"},
    {"label": "English essay", "question": "When is the English essay due?", "role": "In-charge", "subject": "english"},
    {"label": "Football trials", "question": "When are the football trials?", "role": "HOD", "subject": "sports"},
)
