import os
import json


def get_api_key():
    try:
        import streamlit as st

        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


def ai_available():
    return bool(get_api_key())


def _client():
    from google import genai

    return genai.Client(api_key=get_api_key())


def _clean_json(text):
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def ask_ai(instructions, user_input, model=None):
    if not ai_available():
        return None, "Gemini API key is not configured yet."

    try:
        client = _client()

        model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        prompt = f"""
{instructions}

Student input:
{user_input}
"""

        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        return response.text, None

    except Exception as e:
        return None, f"AI request failed: {e}"


def generate_question(profile, subject, chapter, topic, difficulty, qtype):
    instructions = """You are Student AI, an educational tutor.

Generate one age-appropriate academic question.

Return valid JSON only with these keys:
question
correct_answer
explanation
options

For MCQ, options must contain exactly four strings.
For non-MCQ, options must be [].

Keep the question suitable for the student's class and exam level."""

    user_input = json.dumps({
        "student_class": profile.get("class_level"),
        "board": profile.get("board"),
        "exam": profile.get("exam"),
        "subject": subject,
        "chapter": chapter,
        "topic": topic,
        "difficulty": difficulty,
        "question_type": qtype
    }, ensure_ascii=False)

    text, err = ask_ai(instructions, user_input)

    if err:
        return None, err

    try:
        return json.loads(_clean_json(text)), None
    except Exception:
        return None, "AI returned an unexpected format."


def evaluate_answer(profile, question, correct_answer, student_answer):
    instructions = """You are an educational answer evaluator.

Evaluate the student's answer fairly.

Return valid JSON only with:
is_correct (boolean)
score (number from 0 to 100)
feedback (string)
explanation (string)

For open-ended answers, allow partially correct reasoning
and explain what is missing."""

    user_input = json.dumps({
        "student_class": profile.get("class_level"),
        "question": question,
        "correct_answer": correct_answer,
        "student_answer": student_answer
    }, ensure_ascii=False)

    text, err = ask_ai(instructions, user_input)

    if err:
        return None, err

    try:
        return json.loads(_clean_json(text)), None
    except Exception:
        return None, "AI returned an unexpected format."


def solve_doubt(profile, doubt):
    instructions = """You are a patient school tutor.

Explain the student's doubt clearly and age-appropriately.

Use this structure:

1. Short answer
2. Explanation
3. Example
4. Quick check question

Do not diagnose medical conditions or provide medical treatment."""

    return ask_ai(
        instructions,
        json.dumps({
            "student_class": profile.get("class_level"),
            "board": profile.get("board"),
            "exam": profile.get("exam"),
            "doubt": doubt
        }, ensure_ascii=False)
    )


def build_study_plan(profile, weak_topics, tasks, available_hours):
    instructions = """You are a study-planning assistant.

Create a realistic one-day study plan using the student's
available time.

Prioritize weak topics, upcoming tasks and the student's schedule.
Include breaks.
Do not recommend extreme study schedules.

Return valid JSON with key 'plan'.

'plan' must be an array of objects containing:
time
activity
reason"""

    user_input = json.dumps({
        "profile": profile,
        "weak_topics": weak_topics,
        "existing_tasks": tasks,
        "available_hours": available_hours
    }, ensure_ascii=False)

    text, err = ask_ai(instructions, user_input)

    if err:
        return None, err

    try:
        return json.loads(_clean_json(text)), None
    except Exception:
        return None, "AI returned an unexpected format."
