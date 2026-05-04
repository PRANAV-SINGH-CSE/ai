# SmartPrep AI 🚀

SmartPrep AI is an intelligent study platform for JEE/NEET aspirants. It uses Machine Learning and Rule-based engines to analyze your performance and dictate exactly what you should study today.

## 🧠 Core Intelligence
- **Autonomous Planner**: AI picks 2 topics and 40 questions daily.
- **Adaptive Quiz Engine**: Real-time difficulty scaling based on speed and accuracy.
- **Deep Analysis**: Classifies mistakes into Conceptual, Calculation, Guess, or Time Inefficiency.
- **Weakness Detection**: ML model (RandomForest) predicts topics you need to focus on.
- **Gamification**: XP system, daily streaks, and a global leaderboard.

---

## 📋 Prerequisites

Make sure you have these installed before starting:

| Tool | Version | Check Command |
|------|---------|---------------|
| Python | 3.8+ | `python --version` |
| Node.js | 16+ | `node --version` |
| npm | 8+ | `npm --version` |
| pip | Latest | `pip --version` |

---

## ⚙️ How to Run the Project

> **Important**: All backend commands must be run from the **project root directory** (`Jee Neet AiDriven/`), NOT from inside `backend/`.

### Step 1: Clone / Open the Project

```bash
cd "Jee Neet AiDriven"
```

### Step 2: Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 3: Generate the Question Dataset

```bash
python data/generate_gold_data.py
```

This creates `data/questions_dataset.csv` with 240+ curated JEE/NEET questions across Physics, Chemistry, Mathematics, and Biology.

### Step 4: Train the ML Models

```bash
python backend/ml/train_models.py
```

This trains two RandomForest models and saves them:
- `backend/ml/weakness_model.pkl` — Detects weak topics based on accuracy, time, and attempts
- `backend/ml/recommendation_model.pkl` — Recommends next difficulty level

### Step 5: (Optional) Seed the Database with Test Data

```bash
cd backend
python seed_history.py
cd ..
```

This creates a test user (`test_aspirant`) with 20 sample quiz history records for demo purposes.

### Step 6: Start the Backend Server

```bash
uvicorn backend.main:app --reload
```

The FastAPI server will start at: **http://localhost:8000**

- API Docs (Swagger UI): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Step 7: Start the Frontend

Open a **new terminal** and run:

```bash
cd frontend
npm install
npm start
```

The React app will start at: **http://localhost:3000**

---

## 🚀 Quick Start (All Commands)

```bash
# Terminal 1 — Backend (run from project root)
pip install -r backend/requirements.txt
python data/generate_gold_data.py
python backend/ml/train_models.py
uvicorn backend.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm start
```

Open **http://localhost:3000** in your browser, enter a username, and start learning!

---

## 📁 Project Structure

```
Jee Neet AiDriven/
├── backend/
│   ├── main.py                  # FastAPI app with all API routes
│   ├── database.py              # SQLAlchemy models (User, QuestionAttempt, DailyPlan)
│   ├── requirements.txt         # Python dependencies
│   ├── seed_history.py          # Database seeder with test data
│   ├── ml/
│   │   ├── train_models.py      # ML model training script
│   │   ├── weakness_model.pkl   # Trained weakness detection model
│   │   └── recommendation_model.pkl  # Trained recommendation model
│   └── services/
│       ├── analysis_engine.py   # Mistake classification & XP calculation
│       ├── adaptive_engine.py   # Real-time difficulty adjustment
│       └── planner.py           # AI daily study plan generator
├── frontend/
│   ├── package.json             # React dependencies
│   └── src/
│       ├── App.js               # Main React component (all views)
│       ├── index.js             # React entry point
│       └── index.css            # Dark-themed CSS design system
├── data/
│   ├── generate_gold_data.py    # Gold-standard question generator
│   └── questions_dataset.csv    # 240+ curated JEE/NEET questions
├── smartprep.db                 # SQLite database (auto-created)
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register / login a user |
| GET | `/get-dashboard/{user_id}` | Dashboard with daily plan & weak topics |
| GET | `/start-quiz/{user_id}?topic=X` | Start an adaptive quiz |
| POST | `/submit-answer` | Submit answer → get analysis + next question |
| GET | `/leaderboard` | Top 10 users by XP |
| GET | `/analytics/{user_id}` | Subject-wise performance & mistake breakdown |
| GET | `/get-recommendations/{user_id}` | AI-based topic recommendations |

## 📊 Data Storage
- Uses **SQLite** for performance tracking and user profiles.
- Performance logs stored in `question_attempts` table for ML retraining.
- Database file (`smartprep.db`) is auto-created on first server startup.

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'backend'` | You're running from inside `backend/`. Run from the **project root** instead. |
| `FileNotFoundError: data/questions_dataset.csv` | Run `python data/generate_gold_data.py` first. |
| `FileNotFoundError: weakness_model.pkl` | Run `python backend/ml/train_models.py` first. |
| Frontend can't connect to backend | Make sure backend is running on port 8000. Check CORS settings. |
| `npm start` fails | Run `npm install` first inside the `frontend/` folder. |
