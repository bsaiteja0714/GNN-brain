import random

sections = ["A", "B", "C"]

first_names = ["Aarav", "Vihaan", "Aditya", "Sai", "Reyansh", "Arjun", "Vivaan", "Rohan", "Ishaan", "Diya", "Ananya", "Aadhya", "Pari", "Saanvi", "Myra", "Riya", "Kavya", "Anika"]
last_names = ["Sharma", "Verma", "Gupta", "Malhotra", "Bhatia", "Saxena", "Mehta", "Chopra", "Desai", "Joshi", "Patel", "Reddy", "Nair", "Iyer"]
interests = ["Machine Learning", "Graph Theory", "Web Development", "Blockchain", "Quantum Computing", "Cybersecurity", "IoT", "Robotics", "Cloud Computing"]
concerns = ["exam stress", "hostel food quality", "placement worries", "attendance shortage", "library access", "sports facilities", "coding club events"]

def get_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

RAW_NODES = []

RAW_NODES.append({
    "node_id": "Dean",
    "text": "I am Dean Dr. Rao. I focus on the strategic vision of the institute, accreditation, and research funding. I approve major policy changes.",
    "type": "Dean",
    "embedding": None,
    "connections": [],
    "label": "Dean Dr. Rao",
    "importance": 5
})

RAW_NODES.append({
    "node_id": "HOD",
    "text": "I am Prof. Kumar, the Head of Department. I handle faculty allocation, curriculum updates, and serious disciplinary issues. I report directly to the Dean.",
    "type": "HOD",
    "embedding": None,
    "connections": ["Dean"],
    "label": "HOD Prof. Kumar",
    "importance": 4
})

RAW_NODES.extend([
    {
        "node_id": "Placement",
        "text": "I am the Placement Officer. I help students to get placed in top companies and solve placement worries.",
        "type": "Admin",
        "embedding": None,
        "connections": ["Dean"],
        "label": "Placement Officer",
        "importance": 4
    },
    {
        "node_id": "HostelWarden",
        "text": "I am the Hostel Warden. I oversee hostel food quality and dormitory issues.",
        "type": "Admin",
        "embedding": None,
        "connections": ["Dean"],
        "label": "Hostel Warden",
        "importance": 3
    },
    {
        "node_id": "Librarian",
        "text": "I am the Institute Librarian. I manage library access and the digital catalog.",
        "type": "Admin",
        "embedding": None,
        "connections": ["HOD"],
        "label": "Librarian",
        "importance": 2
    },
    {
        "node_id": "SportsCoach",
        "text": "I am the Sports Coach. I handle sports facilities and athletic events.",
        "type": "Admin",
        "embedding": None,
        "connections": ["HOD"],
        "label": "Sports Coach",
        "importance": 2
    }
])

projects_data = [
    {"id": "project_ai_chatbot", "label": "AI Chatbot", "text": "AI Chatbot using GNN and FastAPI"},
    {"id": "project_smart_home", "label": "Smart Home IoT", "text": "Home Automation using IoT devices"},
    {"id": "project_crypto", "label": "Crypto Trading Bot", "text": "Automated trading using Machine Learning"},
    {"id": "project_health", "label": "Healthcare Dashboard", "text": "Analytics dashboard for hospital data"}
]

for p in projects_data:
    RAW_NODES.append({
        "node_id": p["id"],
        "text": p["text"],
        "type": "project",
        "embedding": None,
        "connections": [],
        "label": p["label"],
        "importance": 3
    })

for section in sections:
    cr_id = f"CR-{section}"
    teacher_id = f"Teacher-{section}"
    
    cr_name = get_name()
    teacher_name = f"Prof. {random.choice(last_names)}"
    t_project = random.choice(projects_data)["id"]

    RAW_NODES.extend([
        {
            "node_id": cr_id,
            "text": f"I am {cr_name}, the Class Representative for Section {section}. I collect assignments and represent the class in meetings. I'm interested in leadership and {random.choice(interests)}.",
            "type": "CR",
            "embedding": None,
            "connections": [teacher_id],
            "section": section,
            "label": f"CR {cr_name}",
            "importance": 2
        },
        {
            "node_id": teacher_id,
            "text": f"I am {teacher_name}, the Class Teacher for Section {section}. I teach {random.choice(interests)} and mentor students. I ensure syllabus completion. I mentor the project {t_project}.",
            "type": "Teacher",
            "embedding": None,
            "connections": ["HOD", t_project],
            "section": section,
            "label": f"{teacher_name}",
            "importance": 3
        }
    ])

    for i in range(1, 16):
        sid = f"S-{section}-{i}"
        s_name = get_name()
        s_interest = random.choice(interests)
        s_concern = random.choice(concerns)
        s_project = random.choice(projects_data)["id"]
        
        conns = [cr_id, s_project]
        if "placement" in s_concern:
            conns.append("Placement")
        elif "hostel" in s_concern:
            conns.append("HostelWarden")
        elif "library" in s_concern:
            conns.append("Librarian")
        elif "sports" in s_concern:
            conns.append("SportsCoach")
            
        RAW_NODES.append({
            "node_id": sid,
            "text": f"I am {s_name} from Section {section}. I am passionate about {s_interest}. Currently, I am worried about {s_concern}. I often talk to my CR. I am working on the project {s_project}.",
            "type": "Student",
            "embedding": None,
            "connections": conns,
            "section": section,
            "label": s_name,
            "importance": 1
        })
