from database import SessionLocal, User, QuestionAttempt, DailyPlan, init_db
import datetime
import random

def seed():
    db = SessionLocal()
    init_db()
    
    # Create a test user if not exists
    user = db.query(User).filter(User.username == "test_aspirant").first()
    if not user:
        user = User(
            username="test_aspirant",
            user_class="12",
            exam="JEE",
            target_year=2026,
            xp=1250,
            streak=5,
            profile_data={
                "weak_topics": ["Electrodynamics", "Organic Chemistry", "Calculus"],
                "strong_topics": ["Mechanics", "Thermodynamics", "Algebra"]
            }
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Add some history
    topics = ["Mechanics", "Electrodynamics", "Calculus", "Organic Chemistry"]
    mistakes = ["Conceptual Mistake", "Calculation/Careless Mistake", "Guess", "Mastered"]
    
    for _ in range(20):
        topic = random.choice(topics)
        is_correct = random.choice([0, 1])
        mistake = random.choice(mistakes) if not is_correct else "Mastered"
        
        attempt = QuestionAttempt(
            user_id=user.id,
            question_id=random.randint(1, 400),
            topic=topic,
            subject="General",
            is_correct=is_correct,
            time_taken=random.uniform(20, 180),
            difficulty=random.randint(1, 5),
            mistake_type=mistake,
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 7))
        )
        db.add(attempt)
    
    db.commit()
    print("Seeded database with test user and 20 history records.")

if __name__ == "__main__":
    seed()
