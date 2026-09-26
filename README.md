
# Student AI — BIC 2.0 Prototype

A Streamlit + SQLite prototype for an adaptive student learning platform.

## Included
- Student profile: class, board, exam, subjects, hobbies, goals, sports/activity preferences
- Dashboard
- Syllabus tracker
- To-Do
- Study sessions
- AI doubt solver
- AI question generator
- AI answer evaluation
- Weak/strong topic analysis
- Adaptive study plan
- Parent progress code
- Study Mode prototype
- Local SQLite persistence

## 1. Install
Open CMD in this folder:

```text
python -m pip install -r requirements.txt
```

## 2. Configure AI
Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`.

Put your OpenAI API key in `secrets.toml`.

Do NOT publish the key to GitHub or put it inside `app.py`.

## 3. Run
```text
python -m streamlit run app.py
```

The database file `studentai.db` is created automatically.

## Demo
Create a demo student, add a few syllabus items/tasks, generate AI questions, answer them, then open Performance and Study Plan.

## Important prototype limitations
- Login is a prototype using phone/student ID, not real SMS OTP.
- Study Mode is a web focus prototype; it cannot block other phone apps.
- Parent sharing is a private demo code, not production-grade identity verification.
- Before public deployment, add secure authentication, consent/privacy controls, server-side database, rate limits, logging, and proper data protection.
