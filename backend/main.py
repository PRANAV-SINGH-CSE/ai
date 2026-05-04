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
        
    return {
        "subject_performance": formatted_subjects,
        "mistake_breakdown": [{"type": k, "count": v} for k, v in mistake_stats.items()],
        "total_questions": len(attempts)
    }
