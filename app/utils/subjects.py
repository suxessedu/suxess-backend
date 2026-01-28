
SUBJECT_CATEGORIES = {
    "General Subjects (Across Levels)": [
        "English Language",
        "Mathematics",
        "Basic Science",
        "Social Studies",
        "Computer / Digital Literacy",
        "Nigerian Language (Hausa, Yoruba, Igbo, etc.)",
        "French",
        "Arabic",
        "Physical & Health Education",
        "Creative / Visual Arts",
        "Music"
    ],
    "Secondary School — Junior (JSS 1-3)": [
        "English Language",
        "Mathematics",
        "Basic / Intermediate Science",
        "Social & Citizenship Studies",
        "Nigerian Language (Yoruba, Hausa, Igbo, etc.)",
        "Physical & Health Education",
        "Cultural & Creative Arts",
        "Christian Religious Studies",
        "Islamic Studies",
        "Business Studies",
        "Digital Technologies / Basic ICT",
        "Pre-vocational Subjects"
    ],
    "Secondary School — Senior (SSS 1-3)": [
        "English Language",
        "General Mathematics",
        "Digital Technologies / ICT",
        "Citizenship & Heritage Studies",
        "Biology",
        "Chemistry",
        "Physics",
        "Further Mathematics",
        "Agriculture",
        "Technical Drawing",
        "Geography",
        "Health / Physical Education",
        "Foods & Nutrition",
        "Computer Studies (Advanced)",
        "Nigerian History",
        "Government",
        "Literature in English",
        "Christian Religious Studies",
        "Islamic Studies",
        "One Nigerian Language",
        "French",
        "Arabic",
        "Visual Arts",
        "Music",
        "Home Management",
        "Catering Craft Practice",
        "Accounting",
        "Commerce",
        "Economics",
        "Marketing",
        "Business Studies"
    ],
    "Adult Education Subjects": [
        "English Literacy (Adult)",
        "Adult Mathematics / Numeracy",
        "Functional Communication",
        "Nigerian Languages (Adult Learners)",
        "Financial Literacy",
        "Entrepreneurship / Business Basics",
        "Workplace Communication",
        "Career Development & Leadership",
        "Personal / Family Health",
        "Nutrition Basics",
        "Mental Well-being Fundamentals",
        "Civic & Legal Awareness"
    ],
    "Tech Skills & Vocational Skills": [
        "Microsoft Word",
        "Microsoft Excel",
        "Microsoft PowerPoint",
        "Basic Computer Skills (Windows, Internet, Email)",
        "Digital Literacy & Online Safety",
        "HTML & CSS",
        "JavaScript",
        "Python",
        "React (or React Native)",
        "Node.js",
        "Mobile App Development (Flutter / React Native)",
        "Backend Development Principles",
        "SQL / Databases",
        "Data Analysis (Excel, SQL, Python)",
        "Data Visualization",
        "Machine Learning Basics",
        "AI Fundamentals",
        "UI/UX Design",
        "Graphic Design (Figma, Adobe)",
        "Video Editing & Motion Graphics",
        "Photography",
        "Computer Hardware Fundamentals",
        "Network Fundamentals",
        "Cybersecurity Basics",
        "Digital Marketing",
        "SEO Basics",
        "Project Management Tools",
        "E-commerce Fundamentals",
        "Solar Installation & Maintenance",
        "Basic Electrical Skills",
        "Electronics Fundamentals",
        "Automobile Basics"
    ],
    "Bonus — Popular Tutoring Demand Tags": [
        "Exam Prep (WAEC / NECO / JAMB / UTME)",
        "Public Speaking",
        "Problem-Solving Skills",
        "Study Skills / Time Management"
    ]
}

def get_all_subjects():
    """Returns the structured dictionary of subjects."""
    return SUBJECT_CATEGORIES

def get_flat_subject_list():
    """Returns a flat list of all unique subjects for validation."""
    all_subjects = set()
    for category in SUBJECT_CATEGORIES.values():
        for subject in category:
            all_subjects.add(subject)
    return sorted(list(all_subjects))

def normalize_subject_list(subjects_string):
    """Takes a comma-separated string of subjects and returns a list of cleaned names."""
    if not subjects_string:
        return []
    # Simple splitting and stripping to satisfy existing route logic
    return [s.strip() for s in subjects_string.split(',') if s.strip()]
