
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import (
    init_database, create_student, get_student_by_phone, get_student,
    update_student, add_task, get_tasks, set_task_completed, delete_task,
    add_syllabus_item, get_syllabus, set_syllabus_completed,
    add_session, get_sessions, add_question_result, get_question_results,
    get_or_create_parent_code, get_student_by_parent_code
)
from ai import (
    ai_available, generate_question, evaluate_answer, solve_doubt,
    build_study_plan
)

st.set_page_config(page_title="Student AI", page_icon="🎓", layout="wide")
init_database()

if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "generated_question" not in st.session_state:
    st.session_state.generated_question = None
if "generated_question_meta" not in st.session_state:
    st.session_state.generated_question_meta = None

st.markdown("""
<style>
.block-container {max-width: 1250px; padding-top: 1.5rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 18px; border: 1px solid rgba(128,128,128,.25);
       background: linear-gradient(135deg, rgba(90,90,255,.12), rgba(0,190,170,.08));}
.small-muted {color: #777; font-size: .9rem;}
.card {padding: 1rem; border: 1px solid rgba(128,128,128,.25); border-radius: 14px;}
</style>
""", unsafe_allow_html=True)

def profile():
    return get_student(st.session_state.student_id)

def logout():
    st.session_state.student_id = None
    st.session_state.generated_question = None
    st.session_state.generated_question_meta = None
    st.rerun()

def login_page():
    st.markdown('<div class="hero"><h1>🎓 Student AI</h1><p>Adaptive learning for the whole student — not just the textbook.</p></div>', unsafe_allow_html=True)
    st.write("")
    tab1, tab2 = st.tabs(["Login", "Create Student Profile"])

    with tab1:
        phone = st.text_input("Phone / Student ID", key="login_phone")
        if st.button("Login", type="primary"):
            if not phone.strip():
                st.error("Enter your phone/student ID.")
            else:
                student = get_student_by_phone(phone.strip())
                if not student:
                    st.error("No profile found. Create one in the next tab.")
                else:
                    st.session_state.student_id = student["id"]
                    st.rerun()

    with tab2:
        with st.form("register"):
            name = st.text_input("Name")
            phone = st.text_input("Phone / Student ID")
            c1, c2 = st.columns(2)
            class_level = c1.selectbox("Class", [str(i) for i in range(8, 13)])
            board = c2.selectbox("Board / Curriculum", ["CBSE", "ICSE", "State Board", "Other / Custom"])
            exam = st.selectbox("Main exam / goal", ["School", "JEE", "NEET", "UPSC", "B.Tech", "Other"])
            subjects = st.text_input("Subjects (comma separated)", placeholder="Physics, Chemistry, Maths")
            hobbies = st.text_input("Hobbies / interests", placeholder="Coding, basketball, music")
            long_term_goal = st.text_input("Long-term goal", placeholder="Computer Science / Athlete / Researcher")
            sports = st.text_input("Sports / activities", placeholder="Basketball, running")
            activity_level = st.selectbox("Activity level", ["Low", "Moderate", "High"])
            study_hours = st.number_input("Usual available study hours/day", 0.5, 12.0, 2.0, 0.5)
            submitted = st.form_submit_button("Create Profile", type="primary")
        if submitted:
            if not name.strip() or not phone.strip():
                st.error("Name and phone/student ID are required.")
            elif get_student_by_phone(phone.strip()):
                st.error("That phone/student ID is already registered.")
            else:
                sid = create_student({
                    "name": name.strip(), "phone": phone.strip(),
                    "class_level": class_level, "board": board, "exam": exam,
                    "subjects": subjects, "hobbies": hobbies,
                    "long_term_goal": long_term_goal, "sports": sports,
                    "activity_level": activity_level, "study_hours": study_hours
                })
                st.session_state.student_id = sid
                st.success("Profile created!")
                st.rerun()

if st.session_state.student_id is None:
    login_page()
    st.stop()

p = profile()
st.sidebar.title("🎓 Student AI")
st.sidebar.caption(f"Hi, {p['name']}!")
page = st.sidebar.radio("Navigate", [
    "Dashboard", "Profile", "Syllabus", "To-Do", "Study Sessions",
    "AI Doubt Solver", "AI Question Lab", "Performance", "Study Plan",
    "Parent View", "Study Mode"
])
if st.sidebar.button("Logout"):
    logout()

if not ai_available():
    st.sidebar.warning("AI API key not configured. Add it to .streamlit/secrets.toml to enable real AI.")

tasks = get_tasks(p["id"])
syllabus = get_syllabus(p["id"])
results = get_question_results(p["id"])
sessions = get_sessions(p["id"])

if page == "Dashboard":
    st.title("Dashboard")
    st.markdown(f"### Welcome back, {p['name']} 👋")
    c1,c2,c3,c4 = st.columns(4)
    completed = sum(x["completed"] for x in tasks)
    accuracy = round(100*sum(x["is_correct"] or 0 for x in results)/len(results),1) if results else 0
    chapters_done = sum(x["completed"] for x in syllabus)
    total_minutes = sum(x["minutes"] for x in sessions)
    c1.metric("Tasks done", f"{completed}/{len(tasks)}")
    c2.metric("Question accuracy", f"{accuracy}%")
    c3.metric("Syllabus items done", f"{chapters_done}/{len(syllabus)}")
    c4.metric("Study time", f"{total_minutes//60}h {total_minutes%60}m")
    st.info("Your core loop: Learn → Practice → Get evaluated → Find weak topics → Adapt your plan.")
    st.subheader("Today's priorities")
    pending = [x for x in tasks if not x["completed"]][:5]
    if pending:
        for t in pending:
            st.write(f"• **{t['task']}** — {t['subject'] or 'General'} · {t['priority']}")
    else:
        st.success("No pending tasks. Add your next target in To-Do.")
    st.subheader("Student context")
    st.write(f"**Goal:** {p['long_term_goal'] or 'Not set'}")
    st.write(f"**Interests:** {p['hobbies'] or 'Not set'}")
    st.write(f"**Activities:** {p['sports'] or 'Not set'}")

elif page == "Profile":
    st.title("👤 Student Profile")
    with st.form("edit_profile"):
        name = st.text_input("Name", p["name"])
        c1,c2 = st.columns(2)
        class_level = c1.selectbox("Class", [str(i) for i in range(8,13)], index=[str(i) for i in range(8,13)].index(p["class_level"]))
        boards = ["CBSE","ICSE","State Board","Other / Custom"]
        board = c2.selectbox("Board", boards, index=boards.index(p["board"]) if p["board"] in boards else 0)
        exams = ["School","JEE","NEET","UPSC","B.Tech","Other"]
        exam = st.selectbox("Exam / goal", exams, index=exams.index(p["exam"]) if p["exam"] in exams else 0)
        subjects = st.text_input("Subjects", p["subjects"] or "")
        hobbies = st.text_input("Hobbies / interests", p["hobbies"] or "")
        goal = st.text_input("Long-term goal", p["long_term_goal"] or "")
        sports = st.text_input("Sports / activities", p["sports"] or "")
        levels = ["Low","Moderate","High"]
        activity = st.selectbox("Activity level", levels, index=levels.index(p["activity_level"]) if p["activity_level"] in levels else 1)
        hours = st.number_input("Available study hours/day", .5, 12., float(p["study_hours"] or 2), .5)
        if st.form_submit_button("Save Profile", type="primary"):
            update_student(p["id"], {
                "name":name, "class_level":class_level, "board":board, "exam":exam,
                "subjects":subjects, "hobbies":hobbies, "long_term_goal":goal,
                "sports":sports, "activity_level":activity, "study_hours":hours
            })
            st.success("Profile updated.")
            st.rerun()

elif page == "Syllabus":
    st.title("📚 Syllabus")
    with st.form("add_syllabus"):
        c1,c2,c3 = st.columns(3)
        subject = c1.text_input("Subject")
        chapter = c2.text_input("Chapter")
        topic = c3.text_input("Topic (optional)")
        if st.form_submit_button("Add"):
            if subject and chapter:
                add_syllabus_item(p["id"], subject, chapter, topic)
                st.rerun()
    for item in syllabus:
        label = f"{item['subject']} — {item['chapter']}" + (f" — {item['topic']}" if item["topic"] else "")
        checked = st.checkbox(label, value=bool(item["completed"]), key=f"sy_{item['id']}")
        if checked != bool(item["completed"]):
            set_syllabus_completed(item["id"], checked)
            st.rerun()

elif page == "To-Do":
    st.title("✅ To-Do")
    with st.form("new_task"):
        task = st.text_input("Task")
        c1,c2,c3 = st.columns(3)
        subject = c1.text_input("Subject")
        due = c2.date_input("Due date", date.today())
        priority = c3.selectbox("Priority", ["High","Medium","Low"])
        if st.form_submit_button("Add Task", type="primary"):
            if task.strip():
                add_task(p["id"], task.strip(), subject, str(due), priority)
                st.rerun()
    for t in tasks:
        c1,c2,c3 = st.columns([6,2,1])
        checked = c1.checkbox(f"{t['task']}  ·  {t['subject'] or 'General'}  ·  {t['priority']}", bool(t["completed"]), key=f"task_{t['id']}")
        if checked != bool(t["completed"]):
            set_task_completed(t["id"], checked)
            st.rerun()
        if c3.button("🗑️", key=f"del_{t['id']}"):
            delete_task(t["id"])
            st.rerun()

elif page == "Study Sessions":
    st.title("⏱️ Study Sessions")
    with st.form("session"):
        c1,c2 = st.columns(2)
        subject = c1.text_input("Subject")
        minutes = c2.number_input("Minutes", 5, 600, 45, 5)
        if st.form_submit_button("Log Session"):
            add_session(p["id"], subject, int(minutes), str(date.today()))
            st.success("Session logged.")
    if sessions:
        df = pd.DataFrame(sessions)
        st.dataframe(df[["session_date","subject","minutes"]], use_container_width=True, hide_index=True)

elif page == "AI Doubt Solver":
    st.title("🤖 Clear My Doubt")
    doubt = st.text_area("Ask your academic doubt", height=150)
    if st.button("Explain", type="primary"):
        if not doubt.strip():
            st.warning("Enter a doubt first.")
        else:
            with st.spinner("Thinking..."):
                answer, err = solve_doubt(p, doubt)
            if err:
                st.error(err)
            else:
                st.markdown(answer)

elif page == "AI Question Lab":
    st.title("🧪 AI Question Lab")
    c1,c2,c3 = st.columns(3)
    subject = c1.text_input("Subject", "Physics")
    chapter = c2.text_input("Chapter", "Laws of Motion")
    topic = c3.text_input("Topic", "Newton's laws")
    c1,c2,c3 = st.columns(3)
    difficulty = c1.selectbox("Difficulty", ["Easy","Medium","Hard"])
    qtype = c2.selectbox("Type", ["MCQ","Short Answer","Conceptual"])
    if st.button("Generate Question", type="primary"):
        with st.spinner("Generating..."):
            q, err = generate_question(p, subject, chapter, topic, difficulty, qtype)
        if err:
            st.error(err)
        else:
            st.session_state.generated_question = q
            st.session_state.generated_question_meta = (subject, chapter, topic, difficulty)
            st.rerun()

    q = st.session_state.generated_question
    meta = st.session_state.generated_question_meta
    if q and meta:
        st.divider()
        st.subheader(q.get("question",""))
        options = q.get("options") or []
        if options:
            answer = st.radio("Choose your answer", options, key="mcq_answer")
        else:
            answer = st.text_area("Your answer", key="open_answer")
        if st.button("Submit Answer"):
            with st.spinner("Evaluating..."):
                ev, err = evaluate_answer(p, q.get("question",""), q.get("correct_answer",""), answer)
            if err:
                st.error(err)
            else:
                is_correct = bool(ev.get("is_correct"))
                add_question_result(
                    p["id"], meta[0], meta[1], meta[2], meta[3],
                    q.get("question",""), q.get("correct_answer",""),
                    answer, is_correct, ev.get("explanation","")
                )
                if is_correct:
                    st.success(f"Correct! Score: {ev.get('score', 100)}")
                else:
                    st.warning(f"Needs review. Score: {ev.get('score', 0)}")
                st.write(ev.get("feedback",""))
                st.info(ev.get("explanation",""))

elif page == "Performance":
    st.title("📈 Performance")
    if not results:
        st.info("Complete some AI questions to see your performance.")
    else:
        df = pd.DataFrame(results)
        accuracy = 100 * df["is_correct"].mean()
        c1,c2 = st.columns(2)
        c1.metric("Overall accuracy", f"{accuracy:.1f}%")
        c2.metric("Questions attempted", len(df))
        topic_df = df.groupby(["subject","chapter","topic"], dropna=False)["is_correct"].mean().reset_index()
        topic_df["accuracy"] = (topic_df["is_correct"]*100).round(1)
        st.subheader("Topic performance")
        st.dataframe(topic_df[["subject","chapter","topic","accuracy"]].sort_values("accuracy"), use_container_width=True, hide_index=True)
        weak = topic_df[topic_df["accuracy"] < 60]
        strong = topic_df[topic_df["accuracy"] >= 80]
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("🔴 Needs practice")
            if weak.empty: st.write("No weak topic detected yet.")
            else: st.dataframe(weak[["subject","chapter","topic","accuracy"]], hide_index=True)
        with c2:
            st.subheader("🟢 Strong areas")
            if strong.empty: st.write("Keep practicing to build evidence.")
            else: st.dataframe(strong[["subject","chapter","topic","accuracy"]], hide_index=True)

elif page == "Study Plan":
    st.title("🧠 Adaptive Study Plan")
    weak = []
    if results:
        df = pd.DataFrame(results)
        topic_df = df.groupby(["subject","chapter","topic"], dropna=False)["is_correct"].mean().reset_index()
        for _, r in topic_df[topic_df["is_correct"] < .6].iterrows():
            weak.append(f"{r['subject']} — {r['chapter']} — {r['topic']}")
    if st.button("Generate My Plan", type="primary"):
        with st.spinner("Building your plan..."):
            plan, err = build_study_plan(p, weak, tasks, p["study_hours"])
        if err:
            st.error(err)
        else:
            for item in plan.get("plan", []):
                st.markdown(f"**{item.get('time','')} — {item.get('activity','')}**")
                st.write(item.get("reason",""))

elif page == "Parent View":
    st.title("👨‍👩‍👧 Parent Progress Sharing")
    st.write("Generate a private code that a parent can enter in the Parent View.")
    if st.button("Generate / Show Parent Code", type="primary"):
        code = get_or_create_parent_code(p["id"])
        st.code(code)
        st.caption("Only share this code with the intended parent/guardian.")

    st.divider()
    st.subheader("Parent access demo")
    code = st.text_input("Enter parent code")
    if st.button("Open Parent Summary"):
        parent_student = get_student_by_parent_code(code)
        if not parent_student:
            st.error("Invalid code.")
        else:
            parent_tasks = get_tasks(parent_student["id"])
            parent_results = get_question_results(parent_student["id"])
            st.success(f"Progress for {parent_student['name']}")
            done = sum(x["completed"] for x in parent_tasks)
            acc = round(100*sum(x["is_correct"] or 0 for x in parent_results)/len(parent_results),1) if parent_results else 0
            c1,c2 = st.columns(2)
            c1.metric("Tasks completed", f"{done}/{len(parent_tasks)}")
            c2.metric("Question accuracy", f"{acc}%")
            st.write("This view intentionally shows progress summaries rather than private doubt text.")

elif page == "Study Mode":
    st.title("🎯 Study Mode")
    st.info("Prototype focus mode: use the timer and stay on the current task. Real phone-level app blocking requires a dedicated Android implementation; this web prototype does not claim to block other apps.")
    task_text = st.text_input("Current focus task", "Study one topic")
    minutes = st.slider("Focus duration (minutes)", 5, 120, 25)
    st.markdown(f"### Focus target: {task_text}")
    st.markdown(f"### Session: {minutes} minutes")
    if st.button("Start Focus Session", type="primary"):
        st.success("Focus session started. When finished, log the session in Study Sessions.")

st.sidebar.divider()
st.sidebar.caption("Student AI • BIC prototype")
