"""Fictional school notices and individual student knowledge for the demo graph."""

from app.graph.data import NODES, RECORDS, SCENARIOS, SECTIONS, Record

CAMPUS_NOTICES = (
    Record("library-hours", "dean", "Library hours",
           ("library hours", "library open", "library opening", "when does the library open", "when does the library close"),
           "The library is open on school days from 8:00 a.m. to 4:30 p.m., including lunch. Bring your school ID.",
           "Dean’s library notice", example="When does the library open?"),
    Record("library-loans", "dean", "Library borrowing and renewals",
           ("library book", "library books", "borrow a book", "borrow books", "renew my book", "book renewal", "overdue book"),
           "Take your school ID to the library desk to borrow up to two books for 14 days. You can renew once if nobody has reserved the book. Bring overdue or damaged books back to the desk so staff can help.",
           "Dean’s library notice", example="How do I borrow or renew a library book?"),
    Record("exam-timetable", "dean", "Term exam timetable",
           ("exam timetable", "exam schedule", "exam dates", "term exams", "when are exams", "exam start"),
           "The demo term exams start on 14 December 2026. Check the Term Exams notice on the school portal for your subject, room and reporting time.",
           "Dean’s examinations bulletin", example="When do the term exams start?"),
    Record("exam-admit-card", "dean", "Exam admit cards",
           ("admit card", "admit cards", "exam hall ticket", "hall ticket", "exam admission slip"),
           "Collect your term exam admit card from the academic office during lunch from 9 December 2026. Check your name and subjects before you leave the desk.",
           "Dean’s examinations bulletin", example="Where do I collect my exam admit card?"),
    Record("missed-exam", "dean", "Missed term exam",
           ("missed an exam", "missed my exam", "missed the exam", "miss my exam", "make up exam", "makeup exam", "exam reschedule"),
           "Ask your guardian to notify the academic office and tell your class in-charge which paper you missed. The academic office will confirm whether a make-up exam is available and give you the date.",
           "Dean’s make-up assessment procedure", example="What happens if I miss my exam?"),
    Record("field-trip", "dean", "Museum trip permission",
           ("field trip", "museum trip", "school trip", "permission slip", "excursion"),
           "For the museum trip on 8 December 2026, have a guardian sign the permission form and give it to your class in-charge by 3 December. The meeting point is the main gate at 8:00 a.m.",
           "Dean’s museum trip circular", example="Who takes the field trip permission slip?"),
    Record("parent-conference", "dean", "Parent–teacher conferences",
           ("parent teacher meeting", "parent teacher conference", "parent teacher conferences", "ptm", "parent meeting"),
           "Parent–teacher conferences run from 9:00 a.m. to noon on 12 December 2026. A guardian can request a 10-minute appointment through the school portal or the academic office.",
           "Dean’s family conference notice", example="How do parents book a parent–teacher meeting?"),
    Record("clubs", "dean", "After-school clubs",
           ("school club", "school clubs", "after school club", "after school clubs", "join a club", "club sign up"),
           "Ask your CR for the club list. Submit your preferred club and a parent or guardian’s consent through the activity form. The activity office will confirm your place and the first meeting.",
           "Dean’s activities guide", example="How do I join an after-school club?"),
    Record("leave-request", "director", "Student leave requests",
           ("leave request", "leave application", "apply for leave", "sick leave", "report an absence",
            "report my absence", "report absence", "call in sick", "tell the school i am sick"),
           "A parent or guardian should notify the attendance office before 9:00 a.m. on the first day of an absence. For planned leave, send a written request through the school office in advance and tell your class in-charge.",
           "Director’s attendance and leave handbook", example="How do I apply for sick leave?"),
    Record("student-id", "director", "Student ID replacement",
           ("lost my id", "lost student id", "lost school id", "lost my student id", "lost my school id",
            "student id replacement", "replacement id", "replace my id", "id card replacement"),
           "Report your missing school ID to the front office. Give your name and class so staff can issue a temporary pass and explain how to collect a replacement.",
           "Director’s student services guide", example="What should I do if I lost my student ID?"),
    Record("bus", "director", "School bus changes",
           ("school bus", "bus stop", "bus route", "bus pass", "transport office", "change my bus"),
           "Ask a guardian to contact the transport office with your class and current route number. Wait for the office to confirm any stop or route change before using it.",
           "Director’s transport guide", example="How do I change my school bus stop?"),
    Record("early-pickup", "director", "Early pickup",
           ("early pickup", "early dismissal", "leave school early", "pick me up early", "leave campus early"),
           "A parent or guardian should arrange early pickup with the front office in advance. On the day, the authorized adult signs the student out at reception.",
           "Director’s dismissal procedure", example="Can a parent pick me up early?"),
    Record("science-fair", "hod-science", "Science fair registration",
           ("science fair", "science exhibition", "science project fair"),
           "Submit a one-paragraph project proposal to your science in-charge by 2 December 2026. Entries may be individual or in pairs. The fair is on 10 December in the activity hall.",
           "Science department fair circular", example="How do I register for the science fair?"),
    Record("math-olympiad", "hod-math", "Mathematics Olympiad",
           ("math olympiad", "maths olympiad", "mathematics olympiad", "math competition", "maths competition"),
           "Tell your mathematics in-charge by 4 December 2026 if you want to enter the school maths olympiad. The practice session is on 7 December at 3:15 p.m. in Room 204.",
           "Mathematics department competitions notice", example="How do I sign up for the maths olympiad?"),
    Record("debate-tryouts", "hod-english", "English debate tryouts",
           ("debate tryout", "debate tryouts", "debate team", "debate club", "debate sign up"),
           "Debate tryouts are on 4 December 2026 at 3:30 p.m. in the library seminar room. Prepare a one-minute opening argument on a school topic.",
           "English department activities notice", example="Where are the debate tryouts?"),
    Record("laptop-loan", "hod-computing", "School laptop loan",
           ("laptop loan", "borrow a laptop", "loan laptop", "borrow a school laptop", "loaner laptop"),
           "Ask your Computing in-charge for the equipment loan form. The IT desk approves short loans based on available devices and gives you a return date.",
           "Computing department equipment notice", example="Can I borrow a school laptop?"),
    Record("sports-day", "hod-sports", "Sports Day registration",
           ("sports day", "sportsday", "athletics meet", "track meet"),
           "Sports Day is on 9 December 2026 on the main field. Sign up for up to two events with your Physical Education in-charge by 2 December.",
           "Physical Education events bulletin", example="How do I sign up for Sports Day?"),
)

def class_notices(section, room):
    return (
        Record("class-notes", f"CR-{section}", f"Class {section} shared notes",
               ("class notes", "missed notes", "missed class", "catch up on class", "shared notes"),
               f"Open the Class {section} folder on the school portal for this week’s lesson summaries. If a file is missing, ask your CR by the end of the day.",
               f"Class {section} representative notice", section, "Where can I find my class notes?"),
        Record("lost-found", f"CR-{section}", f"Class {section} lost property",
               ("lost and found", "lost property", "lost my water bottle", "lost my bag", "lost my jacket"),
               f"Check the classroom shelf near Room {room} first. The CR can direct you to the main lost-and-found shelf beside reception. Describe the item when you collect it.",
               f"Class {section} representative notice", section, "Where is lost and found?"),
        Record("lab-safety", f"incharge-{section}-science", f"Class {section} lab preparation",
               ("lab safety", "lab rules", "lab kit", "goggles", "bring to my practical", "bring to the practical"),
               "Bring your practical notebook and wear closed shoes. The teacher provides eye protection when needed. Wait for the teacher’s instructions before touching equipment.",
               f"Class {section} laboratory preparation sheet", section, "What should I bring to the practical?"),
        Record("math-retake", f"incharge-{section}-math", f"Class {section} maths quiz make-up",
               ("missed my maths quiz", "maths quiz retake", "missed the math quiz", "algebra quiz retake",
                "make up my maths quiz", "math make up quiz", "maths retest"),
               f"Tell your mathematics in-charge which quiz you missed. The class make-up slot is Thursday at 3:15 p.m. in Room {room}; confirm your slot with the teacher first.",
               f"Class {section} mathematics class notice", section, "How do I make up my maths quiz?"),
        Record("essay-extension", f"incharge-{section}-english", f"Class {section} essay extension",
               ("essay extension", "extension on my essay", "english essay extension", "submit my essay late",
                "need more time for my english essay", "late essay"),
               "Ask your English in-charge before the due date. Explain why you need more time and suggest a new submission date. The teacher will confirm whether the extension is approved.",
               f"Class {section} English assignment guidance", section, "Can I get an extension on my essay?"),
        Record("portal-password", f"incharge-{section}-computing", f"Class {section} school portal access",
               ("forgot my portal password", "school portal password", "reset my password", "forgot my password",
                "reset my school password", "cant log in", "cannot log in", "password reset"),
               "Try the school portal’s password reset option. If you cannot use it, tell your Computing in-charge your username and class so they can direct you to the IT desk. Keep your password private.",
               f"Class {section} Computing support guide", section, "How do I reset my school portal password?"),
        Record("pe-kit", f"incharge-{section}-sports", f"Class {section} P.E. kit",
               ("pe kit", "p e kit", "pe uniform", "sports kit", "bring to pe", "bring for pe", "bring for p e",
                "wear for pe", "wear for p e"),
               "Bring trainers, your school P.E. kit and a water bottle. If you forgot your kit, tell your Physical Education in-charge before the lesson starts.",
               f"Class {section} Physical Education class notice", section, "What should I bring for P.E.?"),
    )


CLASS_NOTICES = tuple(notice for index, section in enumerate(SECTIONS) for notice in class_notices(section, 101 + index))

INTERESTS = (
    ("science", "a model of the water cycle", "science club"),
    ("mathematics", "a survey about travel to school", "maths club"),
    ("English", "a short story set in the library", "debate club"),
    ("computing", "a simple timetable app", "coding club"),
    ("physical education", "a class warm-up plan", "football"),
    ("art", "a set of posters for the school fair", "art club"),
    ("music", "a rhythm arrangement for assembly", "school choir"),
)


def student_profile(node):
    subject, project, activity = INTERESTS[(node.roll - 1 + 2 * SECTIONS.index(node.section)) % len(INTERESTS)]
    return Record(
        "student-profile", node.id, f"{node.label}’s student profile",
        ("your favorite subject", "your favourite subject", "what is your favourite subject", "student profile",
         "what are you working on", "what are your hobbies", "your project", "your interests", "what clubs are you in",
         "your roll number", "my roll number"),
        f"I’m in Class {node.section}, roll {node.roll}. My favourite subject is {subject}. "
        f"I’m working on {project}, and I take part in {activity}.",
        "Fictional student profile", node.section, "What are you working on?", local_only=True,
    )


STUDENT_PROFILES = tuple(student_profile(node) for node in NODES if node.roll is not None)
SCHOOL_RECORDS = (*RECORDS, *CAMPUS_NOTICES, *CLASS_NOTICES, *STUDENT_PROFILES)
OWNER_BY_ID = {node.id: node for node in NODES}


def school_scenarios():
    yield from SCENARIOS
    seen = set()
    for record in SCHOOL_RECORDS:
        if not record.example or record.topic in seen:
            continue
        seen.add(record.topic)
        owner = OWNER_BY_ID[record.owner]
        yield {"label": "Student profile" if record.local_only else record.title.removeprefix(f"Class {record.section} "),
               "question": record.example, "role": owner.role, "subject": owner.subject}


SCHOOL_SCENARIOS = tuple(school_scenarios())
