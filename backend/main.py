from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import joblib
import datetime
import os
import random
import numpy as np

from backend.database import SessionLocal, init_db, User, QuestionAttempt, DailyPlan
from backend.services.analysis_engine import AnalysisEngine
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.planner import Planner

app = FastAPI(title="SmartPrep AI API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models and Data (Updated with Gold Standard Dataset)
questions_df = pd.read_csv("data/questions_dataset.csv")
weakness_model = joblib.load("backend/ml/weakness_model.pkl")
recommendation_model = joblib.load("backend/ml/recommendation_model.pkl")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    init_db()

# --- Routes ---

@app.post("/register")
def register(username: str, user_class: str, exam: str, target_year: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    new_user = User(
        username=username, 
        user_class=user_class, 
        exam=exam, 
        target_year=target_year,
        profile_data={"confidence": {}, "weak_topics": [], "strong_topics": []}
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    top_users = db.query(User).order_by(User.xp.desc()).limit(10).all()
    return [{
        "username": u.username,
        "xp": u.xp,
        "streak": u.streak,
        "rank": i + 1
    } for i, u in enumerate(top_users)]

@app.get("/get-dashboard/{user_id}")
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent performance
    attempts = db.query(QuestionAttempt).filter(QuestionAttempt.user_id == user_id).all()
    
    # Get daily plan
    today = datetime.datetime.utcnow().date()
    plan = db.query(DailyPlan).filter(
        DailyPlan.user_id == user_id, 
        DailyPlan.date >= today
    ).first()
    
    if not plan:
        # Generate new plan
        all_topics = questions_df["topic"].unique().tolist()
        weak_topics = user.profile_data.get("weak_topics", [])
        strong_topics = user.profile_data.get("strong_topics", [])
        
        generated_plan = Planner.generate_daily_plan(user.__dict__, weak_topics, strong_topics, all_topics)
        plan = DailyPlan(user_id=user_id, plan_json=generated_plan)
        db.add(plan)
        db.commit()
        db.refresh(plan)

    return {
        "user": {
            "username": user.username,
            "xp": user.xp,
            "streak": user.streak,
            "rank_prediction": "AIR ~" + str(random_rank(user.xp))
        },
        "daily_plan": plan.plan_json,
        "weak_topics": user.profile_data.get("weak_topics", []),
        "recent_performance": [a.__dict__ for a in attempts[-5:]]
    }

def random_rank(xp):
    # Mock rank prediction
    if xp > 5000: return np.random.randint(100, 1000)
    if xp > 2000: return np.random.randint(1000, 5000)
    return np.random.randint(5000, 50000)

@app.get("/start-quiz/{user_id}")
def start_quiz(user_id: int, topic: str, difficulty: int = 2):
    # Fetch first question
    question = AdaptiveEngine.select_next_question(questions_df, topic, difficulty)
    return question

@app.post("/submit-answer")
def submit_answer(user_id: int, question_id: int, selected_option: str, time_taken: float, db: Session = Depends(get_db)):
    # Find question
    q_row = questions_df[questions_df["question_id"] == question_id].iloc[0]
    is_correct = 1 if selected_option == q_row["correct_option"] else 0
    
    # Map difficulty string to integer
    diff_map = {"Easy": 2, "Medium": 3, "Hard": 4}
    q_diff_num = diff_map.get(q_row["difficulty"], 3)

    # Analyze mistake
    avg_time = 60.0 # Mock average time for topic
    mistake_type = AnalysisEngine.classify_mistake(is_correct, time_taken, avg_time, q_row["difficulty"])
    xp_earned = AnalysisEngine.calculate_xp(is_correct, time_taken, avg_time, q_diff_num)
    
    # Save attempt
    attempt = QuestionAttempt(
        user_id=user_id,
        question_id=question_id,
        topic=q_row["topic"],
        subject=q_row["subject"],
        is_correct=is_correct,
        time_taken=time_taken,
        difficulty=q_diff_num,
        mistake_type=mistake_type
    )
    db.add(attempt)
    
    # Update user XP
    user = db.query(User).filter(User.id == user_id).first()
    user.xp += xp_earned
    
    # Update profile if needed (Simplified weakness logic)
    # In real app, we would run the ML model here
    
    db.commit()
    
    # Select next question adaptively
    next_difficulty = AdaptiveEngine.adjust_difficulty(q_diff_num, is_correct, time_taken, avg_time)
    
    # Avoid repeating the same question by excluding the current one
    next_q = AdaptiveEngine.select_next_question(questions_df, q_row["topic"], next_difficulty)
    
    # If it happens to pick the same question (rare but possible), retry once
    if next_q and next_q["question_id"] == question_id:
        next_q = AdaptiveEngine.select_next_question(questions_df, q_row["topic"], next_difficulty)
    
    return {
        "result": "Correct" if is_correct else "Incorrect",
        "mistake_analysis": mistake_type,
        "xp_earned": xp_earned,
        "next_question": next_q,
        "question_text": q_row["question_text"],
        "selected_option": selected_option,
        "correct_option": q_row["correct_option"],
        "explanation": q_row["explanation"]
    }

@app.get("/get-recommendations/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    # Mock recommendation using model
    # X = [[accuracy, avg_time]]
    # rec = recommendation_model.predict(X)
    return {
        "next_topic": "Modern Physics",
        "difficulty_suggested": "Medium",
        "reason": "You struggled with conceptual questions in Electrodynamics."
    }

@app.get("/analytics/{user_id}")
def get_analytics(user_id: int, db: Session = Depends(get_db)):
    attempts = db.query(QuestionAttempt).filter(QuestionAttempt.user_id == user_id).all()
    
    if not attempts:
        return {"subject_performance": [], "mistake_breakdown": [], "total_questions": 0}
        
    subject_stats = {}
    mistake_stats = {}
    
    for a in attempts:
        if a.subject not in subject_stats:
            subject_stats[a.subject] = {"total": 0, "correct": 0, "time": 0}
        subject_stats[a.subject]["total"] += 1
        subject_stats[a.subject]["correct"] += a.is_correct
        subject_stats[a.subject]["time"] += a.time_taken
        
        if not a.is_correct and a.mistake_type:
            mistake_stats[a.mistake_type] = mistake_stats.get(a.mistake_type, 0) + 1
            
    formatted_subjects = []
    for subj, stats in subject_stats.items():
        formatted_subjects.append({
            "subject": subj,
            "accuracy": round((stats["correct"] / stats["total"]) * 100, 1),
            "avg_time": round(stats["time"] / stats["total"], 1),
            "total_attempts": stats["total"]
        })
        
    attempt_details = []
    for a in attempts:
        q_rows = questions_df[questions_df["question_id"] == a.question_id]
        q_row = q_rows.iloc[0] if not q_rows.empty else None
        attempt_details.append({
            "question_id": a.question_id,
            "question_text": q_row["question_text"] if q_row is not None else None,
            "topic": a.topic,
            "subject": a.subject,
            "difficulty": a.difficulty,
            "is_correct": bool(a.is_correct),
            "mistake_type": a.mistake_type,
            "time_taken": a.time_taken,
            "timestamp": a.timestamp,
        })

    attempt_details.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "subject_performance": formatted_subjects,
        "mistake_breakdown": [{"type": k, "count": v} for k, v in mistake_stats.items()],
        "total_questions": len(attempts),
        "attempt_details": attempt_details
    }

@app.get("/detailed-analysis/{user_id}")
def get_detailed_analysis(user_id: int, db: Session = Depends(get_db)):
    """
    Comprehensive AI performance analysis with patterns, insights, and personalized suggestions.
    """
    attempts = db.query(QuestionAttempt).filter(QuestionAttempt.user_id == user_id).all()
    
    if not attempts:
        return {
            "overall_performance": {"total_questions": 0, "accuracy": 0, "avg_time": 0},
            "strengths": [],
            "weaknesses": [],
            "patterns": [],
            "suggestions": [],
            "time_management": {},
            "difficulty_analysis": {}
        }
    
    # Overall stats
    total = len(attempts)
    correct = sum(1 for a in attempts if a.is_correct)
    overall_accuracy = round((correct / total) * 100, 1)
    overall_avg_time = round(sum(a.time_taken for a in attempts) / total, 1)
    
    # Topic-wise analysis
    topic_stats = {}
    subject_stats = {}
    difficulty_breakdown = {2: {}, 3: {}, 4: {}}  # Easy, Medium, Hard
    time_patterns = {"fast": 0, "moderate": 0, "slow": 0}
    mistake_types = {}
    
    for a in attempts:
        # Topic stats
        if a.topic not in topic_stats:
            topic_stats[a.topic] = {"total": 0, "correct": 0, "time": 0, "mistakes": {}}
        topic_stats[a.topic]["total"] += 1
        topic_stats[a.topic]["correct"] += a.is_correct
        topic_stats[a.topic]["time"] += a.time_taken
        
        # Mistake tracking
        if a.mistake_type:
            if a.mistake_type not in topic_stats[a.topic]["mistakes"]:
                topic_stats[a.topic]["mistakes"][a.mistake_type] = 0
            topic_stats[a.topic]["mistakes"][a.mistake_type] += 1
        
        # Subject stats
        if a.subject not in subject_stats:
            subject_stats[a.subject] = {"total": 0, "correct": 0}
        subject_stats[a.subject]["total"] += 1
        subject_stats[a.subject]["correct"] += a.is_correct
        
        # Difficulty analysis
        if a.difficulty not in difficulty_breakdown[a.difficulty]:
            difficulty_breakdown[a.difficulty][a.difficulty] = {"total": 0, "correct": 0}
        difficulty_breakdown[a.difficulty][a.difficulty]["total"] += 1
        difficulty_breakdown[a.difficulty][a.difficulty]["correct"] += a.is_correct
        
        # Time patterns
        if a.time_taken < 30:
            time_patterns["fast"] += 1
        elif a.time_taken < 60:
            time_patterns["moderate"] += 1
        else:
            time_patterns["slow"] += 1
        
        # Mistake types
        if a.mistake_type:
            mistake_types[a.mistake_type] = mistake_types.get(a.mistake_type, 0) + 1
    
    # Calculate topic accuracies and identify strengths/weaknesses
    topic_accuracies = []
    for topic, stats in topic_stats.items():
        acc = round((stats["correct"] / stats["total"]) * 100, 1)
        topic_accuracies.append({
            "topic": topic,
            "accuracy": acc,
            "attempts": stats["total"],
            "avg_time": round(stats["time"] / stats["total"], 1),
            "dominant_mistake": max(stats["mistakes"].items(), key=lambda x: x[1])[0] if stats["mistakes"] else None
        })
    
    topic_accuracies.sort(key=lambda x: x["accuracy"], reverse=True)
    
    # Identify strengths (accuracy >= 75%)
    strengths = [t for t in topic_accuracies if t["accuracy"] >= 75]
    
    # Identify weaknesses (accuracy < 50%)
    weaknesses = [t for t in topic_accuracies if t["accuracy"] < 50]
    
    # Detect patterns
    patterns = []
    
    # Pattern 1: Conceptual weakness
    conceptual_mistakes = mistake_types.get("Conceptual Mistake", 0)
    if conceptual_mistakes > (total * 0.2):  # >20% conceptual mistakes
        patterns.append({
            "type": "Conceptual Weakness",
            "description": f"You have {conceptual_mistakes} conceptual mistakes (~{round(conceptual_mistakes/total*100)}% of attempts). You understand the basics but struggle with deeper concepts.",
            "severity": "high" if conceptual_mistakes > (total * 0.3) else "medium"
        })
    
    # Pattern 2: Time inefficiency
    time_inefficiency = mistake_types.get("Time Inefficiency", 0)
    if time_inefficiency > (total * 0.15):
        patterns.append({
            "type": "Speed vs Accuracy",
            "description": f"You have {time_inefficiency} questions with time inefficiency. You're correct but taking too long (~{round(overall_avg_time)}s avg).",
            "severity": "medium"
        })
    
    # Pattern 3: Guessing
    guesses = mistake_types.get("Guess", 0)
    if guesses > (total * 0.1):
        patterns.append({
            "type": "Guessing Detected",
            "description": f"You guessed on {guesses} questions and got lucky. This won't work in the actual exam.",
            "severity": "high" if guesses > (total * 0.2) else "medium"
        })
    
    # Pattern 4: Careless mistakes
    careless = mistake_types.get("Calculation/Careless Mistake", 0)
    if careless > (total * 0.15):
        patterns.append({
            "type": "Careless Errors",
            "description": f"You made {careless} calculation/careless mistakes. Double-check your work.",
            "severity": "medium"
        })
    
    # Pattern 5: Difficulty struggle
    easy_acc = round((difficulty_breakdown[2][2]["correct"] / difficulty_breakdown[2][2]["total"]) * 100, 1) if 2 in difficulty_breakdown[2] else 0
    hard_acc = round((difficulty_breakdown[4][4]["correct"] / difficulty_breakdown[4][4]["total"]) * 100, 1) if 4 in difficulty_breakdown[4] else 0
    
    if hard_acc < easy_acc - 20:
        patterns.append({
            "type": "Difficulty Gap",
            "description": f"You score {easy_acc}% on easy questions but only {hard_acc}% on hard ones. Focus on harder topics.",
            "severity": "medium"
        })
    
    # Generate personalized suggestions
    suggestions = []
    
    if weaknesses:
        weak_topics = ", ".join([w["topic"] for w in weaknesses[:2]])
        suggestions.append(f"🔴 URGENT: Revise {weak_topics} - accuracy is below 50%. Watch concept videos and practice 15+ questions each.")
    
    if strengths:
        strong_topics = ", ".join([s["topic"] for s in strengths[:2]])
        suggestions.append(f"✅ Great work on {strong_topics}! Maintain this level. Move to harder difficulty in these topics.")
    
    if overall_avg_time > 75:
        suggestions.append("⏱️ TIME MANAGEMENT: You're taking too long per question. Practice speed drills - aim for <45s average.")
    
    if conceptual_mistakes > 0:
        suggestions.append("🧠 CONCEPTUAL GAP: Read theory carefully before attempting. Use YouTube playlists to reinforce concepts.")
    
    if guesses > 0:
        suggestions.append("🎯 STOP GUESSING: Attempt fewer questions per test but with certainty. Quality > Quantity.")
    
    if careless > 0:
        suggestions.append("✏️ REDUCE ERRORS: Take 5 extra seconds to verify calculations. Use scratch paper wisely.")
    
    # Time management breakdown
    total_time_pct = {
        "fast": round(time_patterns["fast"] / total * 100, 1),
        "moderate": round(time_patterns["moderate"] / total * 100, 1),
        "slow": round(time_patterns["slow"] / total * 100, 1)
    }
    
    # Difficulty analysis
    diff_names = {2: "Easy", 3: "Medium", 4: "Hard"}
    difficulty_analysis = {}
    for diff, label in diff_names.items():
        if diff in difficulty_breakdown and diff in difficulty_breakdown[diff]:
            stats = difficulty_breakdown[diff][diff]
            if stats["total"] > 0:
                difficulty_analysis[label] = {
                    "accuracy": round(stats["correct"] / stats["total"] * 100, 1),
                    "attempts": stats["total"]
                }
    
    return {
        "overall_performance": {
            "total_questions": total,
            "correct_answers": correct,
            "incorrect_answers": total - correct,
            "accuracy": overall_accuracy,
            "avg_time_per_question": overall_avg_time
        },
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "patterns": patterns,
        "suggestions": suggestions,
        "time_management": {
            "distribution": total_time_pct,
            "average_seconds": overall_avg_time,
            "fastest_avg": round(min([a.time_taken for a in attempts if a.time_taken < 30], default=0), 1),
            "slowest_avg": round(max([a.time_taken for a in attempts if a.time_taken > 60], default=0), 1)
        },
        "difficulty_analysis": difficulty_analysis,
        "topic_accuracy_sorted": topic_accuracies,
        "mistake_breakdown": [{"type": k, "count": v, "percentage": round(v/total*100, 1)} for k, v in mistake_types.items()]
    }
