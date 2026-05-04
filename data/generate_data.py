import pandas as pd
import random

topics = {
    "Physics": ["Mechanics", "Electrodynamics", "Thermodynamics", "Optics", "Modern Physics"],
    "Chemistry": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry"],
    "Mathematics": ["Calculus", "Algebra", "Coordinate Geometry", "Trigonometry"],
    "Biology": ["Botany", "Zoology", "Genetics", "Ecology"]
}

questions = []

for subject, sub_topics in topics.items():
    for topic in sub_topics:
        for i in range(1, 31):  # 30 questions per topic
            difficulty = random.choice(["Easy", "Medium", "Hard"])
            questions.append({
                "question_id": len(questions) + 1,
                "subject": subject,
                "topic": topic,
                "question_text": f"Sample question {i} about {topic} in {subject}",
                "option_a": "Option A",
                "option_b": "Option B",
                "option_c": "Option C",
                "option_d": "Option D",
                "correct_option": random.choice(["A", "B", "C", "D"]),
                "difficulty": difficulty,
                "explanation": f"Explanation for question {i} in {topic}"
            })

df = pd.DataFrame(questions)
df.to_csv("data/questions_dataset.csv", index=False)
print(f"Generated {len(questions)} questions in data/questions_dataset.csv")
