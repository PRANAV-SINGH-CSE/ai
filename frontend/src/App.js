import React, { useState } from 'react';
import './index.css';

const API_BASE = "http://localhost:8000";

function App() {
  const [view, setView] = useState('login'); // login, dashboard, quiz, results
  const [user, setUser] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [quizResults, setQuizResults] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);

  // Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    const username = e.target.username.value;
    const res = await fetch(`${API_BASE}/register?username=${username}&user_class=12&exam=JEE&target_year=2026`, { method: 'POST' });
    const data = await res.json();
    setUser(data);
    fetchDashboard(data.id);
  };

  const fetchDashboard = async (userId) => {
    const res = await fetch(`${API_BASE}/get-dashboard/${userId}`);
    const data = await res.json();
    setDashboardData(data);
    setUser(prev => ({ ...prev, ...data.user })); // Sync user state with latest data
    setView('dashboard');
  };

  const fetchLeaderboard = async () => {
    const res = await fetch(`${API_BASE}/leaderboard`);
    const data = await res.json();
    setLeaderboard(data);
    setView('leaderboard');
  };

  const fetchAnalytics = async () => {
    const res = await fetch(`${API_BASE}/analytics/${user.id}`);
    const data = await res.json();
    setAnalyticsData(data);
    setView('analytics');
  };

  const startQuiz = async (topic) => {
    const res = await fetch(`${API_BASE}/start-quiz/${user.id}?topic=${topic}`);
    const data = await res.json();
    setCurrentQuestion(data);
    setCurrentQuiz({ topic, questionsCount: 0 });
    setView('quiz');
  };

  const submitAnswer = async (option) => {
    const res = await fetch(`${API_BASE}/submit-answer?user_id=${user.id}&question_id=${currentQuestion.question_id}&selected_option=${option}&time_taken=45`, { method: 'POST' });
    const data = await res.json();
    
    setQuizResults([...quizResults, data]);
    
    // Update local user XP
    if (data.xp_earned) {
      setUser(prev => ({ ...prev, xp: prev.xp + data.xp_earned }));
    }
    
    if (currentQuiz.questionsCount < 4) { // Mock 5 questions
      setCurrentQuestion(data.next_question);
      setCurrentQuiz({...currentQuiz, questionsCount: currentQuiz.questionsCount + 1});
    } else {
      setView('results');
    }
  };

  return (
    <div className="App">
      <nav className="container" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem 2rem'}}>
        <h1 className="gradient-text" style={{fontSize: '1.5rem', cursor: 'pointer'}} onClick={() => user && fetchDashboard(user.id)}>SmartPrep AI</h1>
        <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          {user && (
            <>
              <button className="btn" style={{background: 'transparent', color: 'var(--text-muted)'}} onClick={fetchAnalytics}>Analytics</button>
              <button className="btn" style={{background: 'transparent', color: 'var(--text-muted)'}} onClick={fetchLeaderboard}>Leaderboard</button>
              <div className="badge" style={{background: 'var(--card)'}}>XP: {user.xp}</div>
            </>
          )}
        </div>
      </nav>

      <main className="container animate-fade">
        {view === 'login' && (
          <div className="card" style={{maxWidth: '400px', margin: '4rem auto', textAlign: 'center'}}>
            <h2 style={{marginBottom: '1.5rem'}}>Welcome to the Future of Learning</h2>
            <form onSubmit={handleLogin}>
              <input name="username" type="text" placeholder="Enter Username" className="btn" style={{width: '100%', background: '#0f172a', border: '1px solid #334155', marginBottom: '1rem', color: 'white'}} required />
              <button type="submit" className="btn btn-primary" style={{width: '100%'}}>Start My AI Journey</button>
            </form>
          </div>
        )}

        {view === 'dashboard' && dashboardData && (
          <div>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem'}}>
              <div>
                <h2 style={{fontSize: '2rem'}}>Hello, {user.username}</h2>
                <p style={{color: 'var(--text-muted)'}}>AI Status: Analyzing your performance...</p>
              </div>
              <div className="card" style={{padding: '0.5rem 1rem'}}>
                <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Predicted Rank</span>
                <div style={{fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--secondary)'}}>{dashboardData.user.rank_prediction}</div>
              </div>
            </div>

            <div className="grid">
              <div className="card">
                <h3 style={{marginBottom: '1rem', color: 'var(--primary)'}}>Today's AI Targets</h3>
                {dashboardData.daily_plan.targets.map((t, i) => (
                  <div key={i} style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: '0.5rem'}}>
                    <div>
                      <div style={{fontWeight: 'bold'}}>{t.topic}</div>
                      <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{t.questions} Questions • {t.type}</div>
                    </div>
                    <button className="btn btn-primary" style={{padding: '0.25rem 1rem', fontSize: '0.8rem'}} onClick={() => startQuiz(t.topic)}>Start</button>
                  </div>
                ))}
              </div>

              <div className="card">
                <h3 style={{marginBottom: '1rem', color: 'var(--secondary)'}}>Focus Areas (Weak Topics)</h3>
                <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                  {["Organic Chemistry", "Calculus", "Mechanics"].map(t => (
                    <span key={t} className="badge badge-weak">{t}</span>
                  ))}
                </div>
                <h3 style={{marginTop: '2rem', marginBottom: '1rem', color: 'var(--success)'}}>Mastered Topics</h3>
                <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                  {["Thermodynamics", "Algebra"].map(t => (
                    <span key={t} className="badge badge-strong">{t}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'quiz' && currentQuestion && (
          <div className="card" style={{maxWidth: '800px', margin: '0 auto'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '2rem'}}>
              <span className="badge" style={{background: 'var(--primary)'}}>{currentQuiz.topic}</span>
              <span style={{color: 'var(--text-muted)'}}>Question {currentQuiz.questionsCount + 1}/5</span>
            </div>
            <h3 style={{fontSize: '1.5rem', marginBottom: '2rem'}}>{currentQuestion.question_text}</h3>
            <div className="grid" style={{gridTemplateColumns: '1fr 1fr'}}>
              {['A', 'B', 'C', 'D'].map(opt => (
                <button key={opt} className="btn" style={{background: 'rgba(255,255,255,0.05)', textAlign: 'left', border: '1px solid rgba(255,255,255,0.1)', color: 'white'}} onClick={() => submitAnswer(opt)}>
                  <strong>{opt}:</strong> {currentQuestion[`option_${opt.toLowerCase()}`]}
                </button>
              ))}
            </div>
          </div>
        )}

        {view === 'results' && (
          <div className="card" style={{textAlign: 'center', maxWidth: '600px', margin: '0 auto'}}>
            <h2 className="gradient-text" style={{fontSize: '2.5rem', marginBottom: '1rem'}}>Quiz Complete!</h2>
            <p style={{fontSize: '1.2rem', marginBottom: '2rem'}}>AI analysis shows you've improved in <strong>{currentQuiz.topic}</strong></p>
            
            <div style={{textAlign: 'left', marginBottom: '2rem'}}>
              <h4 style={{marginBottom: '1rem'}}>Mistake Breakdown:</h4>
              {quizResults.map((r, i) => (
                <div key={i} style={{padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between'}}>
                  <span>Question {i+1}</span>
                  <span style={{color: r.result === 'Correct' ? 'var(--success)' : 'var(--accent)'}}>{r.mistake_analysis}</span>
                </div>
              ))}
            </div>

            <button className="btn btn-primary" onClick={() => fetchDashboard(user.id)}>Return to Dashboard</button>
          </div>
        )}

        {view === 'leaderboard' && (
          <div className="animate-fade">
            <h2 style={{fontSize: '2rem', marginBottom: '2rem', textAlign: 'center'}}><span className="gradient-text">Global</span> Hall of Fame</h2>
            <div className="card" style={{maxWidth: '800px', margin: '0 auto'}}>
              <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                <div style={{display: 'flex', padding: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', fontWeight: 'bold', color: 'var(--text-muted)'}}>
                  <span style={{width: '60px'}}>Rank</span>
                  <span style={{flex: 1}}>Aspirant</span>
                  <span style={{width: '100px', textAlign: 'right'}}>XP</span>
                </div>
                {leaderboard.map((u, i) => (
                  <div key={i} style={{
                    display: 'flex', 
                    padding: '1.2rem 1rem', 
                    background: u.username === user.username ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                    borderRadius: '0.5rem',
                    border: u.username === user.username ? '1px solid var(--primary)' : 'none',
                    alignItems: 'center'
                  }}>
                    <span style={{width: '60px', fontWeight: 'bold', fontSize: '1.2rem'}}>
                      {u.rank === 1 ? '🥇' : u.rank === 2 ? '🥈' : u.rank === 3 ? '🥉' : `#${u.rank}`}
                    </span>
                    <span style={{flex: 1, fontWeight: 'bold'}}>{u.username} {u.username === user.username && <span className="badge badge-strong" style={{marginLeft: '0.5rem'}}>You</span>}</span>
                    <span style={{width: '100px', textAlign: 'right', fontWeight: 'bold', color: 'var(--secondary)'}}>{u.xp}</span>
                  </div>
                ))}
              </div>
              <button className="btn btn-primary" style={{marginTop: '2rem', width: '100%'}} onClick={() => fetchDashboard(user.id)}>Back to Dashboard</button>
            </div>
          </div>
        )}

        {view === 'analytics' && analyticsData && (
          <div className="animate-fade">
            <h2 style={{fontSize: '2rem', marginBottom: '2rem', textAlign: 'center'}}><span className="gradient-text">Performance</span> Analytics</h2>
            <div className="grid">
              <div className="card">
                <h3 style={{marginBottom: '1rem', color: 'var(--primary)'}}>Subject Mastery</h3>
                {analyticsData.subject_performance.map((sub, i) => (
                  <div key={i} style={{marginBottom: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '0.5rem'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
                      <span style={{fontWeight: 'bold'}}>{sub.subject}</span>
                      <span style={{color: 'var(--secondary)'}}>{sub.accuracy}% Accuracy</span>
                    </div>
                    <div style={{width: '100%', background: 'rgba(255,255,255,0.1)', height: '8px', borderRadius: '4px'}}>
                      <div style={{width: `${sub.accuracy}%`, background: 'var(--primary)', height: '100%', borderRadius: '4px'}}></div>
                    </div>
                    <div style={{marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)'}}>
                      Avg Time: {sub.avg_time}s | Attempts: {sub.total_attempts}
                    </div>
                  </div>
                ))}
              </div>
              <div className="card">
                <h3 style={{marginBottom: '1rem', color: 'var(--accent)'}}>Mistake Analysis</h3>
                {analyticsData.mistake_breakdown.length > 0 ? (
                  analyticsData.mistake_breakdown.map((m, i) => (
                    <div key={i} style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)'}}>
                      <span>{m.type}</span>
                      <span className="badge badge-weak">{m.count}</span>
                    </div>
                  ))
                ) : (
                  <p style={{color: 'var(--text-muted)'}}>No mistakes recorded yet. Keep learning!</p>
                )}
                <div style={{marginTop: '2rem', textAlign: 'center'}}>
                  <div style={{fontSize: '3rem', fontWeight: 'bold', color: 'var(--success)'}}>{analyticsData.total_questions}</div>
                  <div style={{color: 'var(--text-muted)'}}>Total Questions Practiced</div>
                </div>
              </div>
            </div>
            <div style={{textAlign: 'center', marginTop: '2rem'}}>
              <button className="btn btn-primary" onClick={() => fetchDashboard(user.id)}>Back to Dashboard</button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
