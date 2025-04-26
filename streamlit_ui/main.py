import streamlit as st # type: ignore
import requests # type: ignore
import random
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt # type: ignore
import pandas as pd # type: ignore
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from rag_learning_path import fetch_web_links # type: ignore
import glob
import json 
from datetime import datetime, timedelta
import time
import uuid
import networkx as nx # type: ignore
from pyvis.network import Network # type: ignore
from streamlit.components.v1 import html # type: ignore
import streamlit.components.v1 as components # type: ignore
from dotenv import load_dotenv # type: ignore
from openai import OpenAI # type: ignore
from streamlit_chat import message # type: ignore

from login_page import show_login
from register_page import show_register


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_API_KEY = os.getenv("SERP_API_KEY")

st.set_page_config(page_title="EduMentor", layout="wide")
st.title("EduMentor – Smart Learning Assistant")

def save_quiz_result(name, score, total, answers, topics):
    result = {
        "name": name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "topics": topics,   # ✅ Add this
        "answers": answers
    }

    filepath = os.path.join(os.path.dirname(__file__), "student_quiz_attempts.json")

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(result)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Auto-save the quiz if user leaves the page
def auto_save_quiz(current_page):
    if st.session_state.get("quiz_confirmed", False) and not st.session_state.get("quiz_submitted", False) and current_page != "🧠 Adaptive Quiz":
        st.session_state.quiz_submitted = True

        # Calculate partial score
        score = 0
        for i in range(1, len(st.session_state.quiz_questions) + 1):
            answer = st.session_state.quiz_answers.get(f"q{i}", {})
            selected = answer.get("selected", None)
            correct = answer.get("correct", "")
            if selected:
                user_answer = selected.split(".")[0].strip()
                if user_answer == correct:
                    score += 1

        save_quiz_result(
            st.session_state.get("student_name", "Unknown"),
            score,
            len(st.session_state.quiz_questions),
            st.session_state.quiz_answers,
            st.session_state.get("topic_input", "Unknown Topics")  # ✅ Add topics here
        )
        st.session_state.quiz_saved = True

        # Clear quiz session state
        for key in [
            "raw_quiz", "quiz_questions", "quiz_answers", "quiz_submitted",
            "quiz_saved", "quiz_generated", "quiz_timer_start", "quiz_confirmed",
            "topic_input", "student_name"
        ]:
            st.session_state.pop(key, None)

        # 🚀 Optional: show a message that it was auto-saved
        st.success("✅ Quiz auto-saved because you left the page!")
        st.rerun()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    auth_choice = st.sidebar.selectbox("Select", ["Login", "Register"])
    if auth_choice == "Login":
        show_login()
    else:
        show_register()
    st.stop()
else:
    # Add Logout option
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    role = st.session_state.get("user_role", "Student")  # default fallback

    if role == "Student":
        page = st.sidebar.radio("Pages", ["👤 Profile", "💬 Chat Assistant", "📘 Learning Path", "🧠 Adaptive Quiz", "📚 Topic Explorer", "📈 My Results"])
    else:
        page = st.sidebar.radio("Pages", ["👤 Profile", "💬 Chat Assistant", "📊 Student Evaluations"])

    auto_save_quiz(page)

# ----------------------------
# 💬 Chat Assistant (Sidebar Panel First)
# ----------------------------
if page == "💬 Chat Assistant":
    # Sidebar: Load saved chats for the user
    with st.sidebar.expander("💾 Saved Chat Logs", expanded=False):
        user_identifier = st.session_state.user.get("email", "unknown_user").split("@")[0]
        user_folder = os.path.join("chat_logs", user_identifier)
        os.makedirs(user_folder, exist_ok=True)  # Ensure folder exists

        chat_files = sorted(glob.glob(os.path.join(user_folder, "chat_*.json")))

        if chat_files:
            for idx, file_path in enumerate(chat_files, start=1):
                fname = os.path.basename(file_path)
                try:
                    dt_part = fname.replace("chat_", "").replace(".json", "")
                    ts = datetime.strptime(dt_part, "%Y%m%d_%H%M%S").strftime("%b %d, %Y %I:%M %p")
                except:
                    ts = "Unknown time"

                st.markdown(f"**🗂️ Chat {idx} ({ts})**")

                with open(file_path, "r", encoding="utf-8") as f:
                    chat_data = json.load(f)
                    preview = ""
                    for msg in chat_data[-2:]:
                        prefix = "🧑‍🎓" if msg["role"] == "user" else "🤖"
                        preview += f"{prefix} {msg['content'][:80]}...\n"
                    st.text(preview.strip())

                if st.button(f"🔁 Continue Chat {idx}", key=f"continue_{file_path}"):
                    st.session_state.chat_history = chat_data
                    st.session_state.chat_log_path = file_path  # ✅ Reset log path to loaded file
                    st.rerun()
                st.markdown("---")
        else:
            st.info("No previous chats found.")

    # Main Chat Panel
    st.title("💬 Interactive AI Chat Assistant")

    # Initialize session state if missing
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "chat_log_path" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_identifier = st.session_state.user.get("email", "unknown_user").split("@")[0]
        user_folder = os.path.join("chat_logs", user_identifier)
        os.makedirs(user_folder, exist_ok=True)

        log_path = os.path.join(user_folder, f"chat_{timestamp}.json")
        st.session_state.chat_log_path = log_path

        # Create an empty file immediately
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

    # Display existing chat history
    for i, msg in enumerate(st.session_state.chat_history):
        is_user = msg["role"] == "user"
        message(msg["content"], is_user=is_user, key=f"chat_msg_{i}")

    # Inline Chat Input Form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Type your question here:",
            key="chat_input_bottom",
            label_visibility="visible",
            placeholder="Ask a question..."
        )
        send_clicked = st.form_submit_button("Send")

    # Process the Message
    if send_clicked and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # ✅ If chat_log_path is None, create a new file now
        if not st.session_state.get("chat_log_path"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_identifier = st.session_state.user.get("email", "unknown_user").split("@")[0]
            user_folder = os.path.join("chat_logs", user_identifier)
            os.makedirs(user_folder, exist_ok=True)
            log_path = os.path.join(user_folder, f"chat_{timestamp}.json")
            st.session_state.chat_log_path = log_path

        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an intelligent assistant for the EduMentor app. You can answer questions about any technical concept irrespective of the domain and generalized questions."}
                    ] + st.session_state.chat_history
                )
                reply = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error: {e}")

        # ✅ Now save after user and assistant both have spoken
        with open(st.session_state.chat_log_path, "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        st.rerun()

    st.markdown("---")

    # Clear chat manually
    if st.button("🗑️ Clear Current Chat"):
        st.session_state.chat_history = []
        st.session_state.chat_log_path = None  # ✅ Important: reset log path to None
        st.rerun()

    if page != "💬 Chat Assistant" and st.session_state.get("chat_history") and not st.session_state.get("chat_saved", False):
        os.makedirs("chat_logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_identifier = st.session_state.user.get("email", "unknown_user").split("@")[0] 
        log_path = f"chat_logs/chat_{user_identifier}_{timestamp}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, indent=2)
        st.session_state.chat_saved = True

    if page != "💬 Chat Assistant" and "chat_history" in st.session_state:
        st.session_state.chat_history = []

# ----------------------------
# 📘 Learning Path
# ----------------------------
elif page == "📘 Learning Path":
    st.header("📘 Personalized Learning Path")
    st.markdown("Enter the topics you're struggling with. Concept graphs and explanations will be generated for each topic and overall.")

    weak_input = st.text_input("Enter weak topics (comma-separated):", placeholder="e.g., CNN, Transformers, Reinforcement Learning")
    weak_topics = [t.strip() for t in weak_input.split(",") if t.strip()]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_edges_with_importance(topic):
        prompt = f"""
        You are a domain expert building a concept graph for learners.

        For the topic **"{topic}"**, list 8-10 prerequisite concepts that are important to learn before this topic.
        For each prerequisite:
        - Use this format: Prerequisite -> {topic} : Explanation : Score
        - Score must be 1 (Low), 2 (Medium), or 3 (High)
        - Importance is based on how essential the prerequisite is to understand the topic.
        
        Ensure that at least one concept is scored 1, one is scored 2, and one is scored 3.

        Example:
        Linear Algebra -> CNN : Needed for understanding matrix operations in convolutions : 3  
        Calculus -> CNN : Helps with understanding gradient descent and backpropagation : 2  
        Image Basics -> CNN : Provides intuition about pixels and image structure : 1  

        Now generate for: "{topic}"
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content
        edges = []
        for line in content.strip().split("\n"):
            if "->" in line and line.count(":") >= 2:
                try:
                    prereq_to_target, explanation, score_str = line.split(":", 2)
                    src, dst = [s.strip() for s in prereq_to_target.split("->")]
                    explanation = explanation.strip()
                    score = int(score_str.strip())
                    if score in [1, 2, 3]:
                        edges.append((src, dst, explanation, score))
                except:
                    continue
        return edges

    def draw_graph_pyvis_with_tooltips(edges, target_topics=None):
        if target_topics is None:
            target_topics = []

        net = Network(height="550px", width="100%", directed=True, notebook=False)
        net.force_atlas_2based()

        colors = {"prerequisite": "#1f77b4", "target": "#d62728"}
        edge_colors = {1: "#999", 2: "#f39c12", 3: "#e74c3c"}
        edge_weights = {1: 1, 2: 3, 3: 5}

        nodes = {}
        for src, dst, explanation, score in edges:
            if src not in nodes:
                nodes[src] = {"color": colors["prerequisite"], "title": explanation}
            if dst not in nodes:
                nodes[dst] = {
                    "color": colors["target"] if dst in target_topics else colors["prerequisite"],
                    "title": "Target Topic" if dst in target_topics else "Related Topic"
                }

        for node, props in nodes.items():
            if node in target_topics:
                net.add_node(
                    node,
                    label=node,
                    color=props["color"],
                    title=props["title"],
                    shape="circle",
                    font={"size": 30, "bold": True, "vadjust": 0}
                )
            else:
                net.add_node(
                    node,
                    label=node,
                    color=props["color"],
                    title=props["title"]
                )

        for src, dst, _, score in edges:
            net.add_edge(src, dst, color=edge_colors.get(score, "#999"), width=edge_weights.get(score, 2))

        # ✅ Create "Graphs" folder if not exists
        graph_dir = os.path.join(os.getcwd(), "Graphs")
        os.makedirs(graph_dir, exist_ok=True)

        # ✅ Save to full path
        filename = f"{'_'.join(target_topics)}_graph.html" if target_topics else "combined_graph.html"
        filepath = os.path.join(graph_dir, filename)
        net.save_graph(filepath)

        # ✅ Inject legend box into the saved HTML
        legend_html = """
        <div style="
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: white;
            border: 1px solid #ccc;
            padding: 10px;
            font-size: 14px;
            font-family: sans-serif;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
            border-radius: 8px;
            z-index: 9999;">
            <b>Legend (Edge Importance)</b><br>
            <span style='color:#e74c3c;'>⬤ High Importance</span><br>
            <span style='color:#f39c12;'>⬤ Medium Importance</span><br>
            <span style='color:#999;'>⬤ Low Importance</span>
        </div>
        """

        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()

        html_with_legend = html_content.replace("</body>", legend_html + "\n</body>")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_with_legend)

        return html_with_legend

    if st.button("🔍 Generate Learning Path"):
        if not weak_topics:
            st.warning("Please enter at least one weak topic.")
        else:
            all_edges = []
            st.subheader("📌 Individual Topic Graphs")
            for topic in weak_topics:
                with st.spinner(f"Generating graph for {topic}..."):
                    topic_edges = get_edges_with_importance(topic)
                    all_edges.extend(topic_edges)
                    html_graph = draw_graph_pyvis_with_tooltips(topic_edges, [topic])
                    st.markdown(f"**Concept Graph for {topic}**")
                    components.html(html_graph, height=600, scrolling=True)

            st.subheader("🔗 Combined Concept Graph")
            combined_html = draw_graph_pyvis_with_tooltips(all_edges, weak_topics)
            components.html(combined_html, height=650, scrolling=True)

# ----------------------------
# 🧠 Adaptive Quiz
# ----------------------------
elif page == "🧠 Adaptive Quiz":
    st.header("🧠 Adaptive Quiz Generator")

    # ✅ Fetch student name from login session automatically
    student_name = st.session_state.get("full_name", "Unknown")
    st.session_state.student_name = student_name
    st.markdown(f"👤 **Student Name:** {student_name}")

    # ✅ Topic input
    st.text_input("Enter one or more quiz topics (comma-separated):", key="topic_input", placeholder="e.g., CNN, Reinforcement Learning, LSTMs")
    raw_input = st.session_state.get("topic_input", "")
    selected_topics = [t.strip() for t in raw_input.split(",") if t.strip()]

    # ✅ Initialize session state
    for key in ["quiz_confirmed", "quiz_generated", "quiz_questions", "quiz_answers", "quiz_submitted", "quiz_saved", "quiz_timer_start"]:
        if key not in st.session_state:
            st.session_state[key] = False if key not in ["quiz_questions", "quiz_answers"] else ([] if key == "quiz_questions" else {})

    # 🔥 AUTOSAVE if user leaves quiz page
    if st.session_state.get("quiz_confirmed", False) and not st.session_state.get("quiz_submitted", False) and page != "🧠 Adaptive Quiz":
        st.session_state.quiz_submitted = True
        score = 0
        for i in range(1, len(st.session_state.quiz_questions) + 1):
            answer = st.session_state.quiz_answers.get(f"q{i}", {})
            selected = answer.get("selected", None)
            correct = answer.get("correct", "")
            if selected:
                user_answer = selected.split(".")[0].strip()
                if user_answer == correct:
                    score += 1
        save_quiz_result(st.session_state.get("student_name", "Unknown"), score, len(st.session_state.quiz_questions), st.session_state.quiz_answers, st.session_state.get("topic_input", "Unknown Topics"))
        st.session_state.quiz_saved = True

        # Clear quiz session
        for key in ["raw_quiz", "quiz_questions", "quiz_answers", "quiz_submitted", "quiz_saved", "quiz_generated", "quiz_timer_start", "quiz_confirmed", "topic_input", "student_name"]:
            st.session_state.pop(key, None)
        st.rerun()

    # ✅ Detect JS-triggered auto-submit (timer expiry)
    if st.session_state.quiz_confirmed and st.session_state.quiz_questions and not st.session_state.quiz_submitted:
        if "autosubmit" in st.query_params:
            st.session_state.quiz_submitted = True
            st.session_state.quiz_saved = False

    # ✅ Confirm Topics and Start Quiz
    if st.button("✅ Confirm Topics and Start Quiz", key="confirm_topics"):
        if not selected_topics:
            st.warning("⚠️ Please enter at least one topic before starting the quiz.")
        else:
            st.session_state.quiz_confirmed = True
            st.session_state.quiz_generated = False
            st.session_state.quiz_questions = []
            st.session_state.quiz_submitted = False
            st.session_state.quiz_saved = False

    # ✅ Generate Quiz
    if st.session_state.quiz_confirmed and selected_topics and not st.session_state.quiz_generated:
        try:
            response = requests.post(
                "http://localhost:5000/api/generate-quiz",
                json={"topics": selected_topics, "difficulty": random.choice(["Easy", "Medium", "Hard"]), "num_questions": 10}
            )
            result = response.json()
            st.session_state.raw_quiz = result["quiz"]
            st.session_state.quiz_questions = [q.strip() for q in result["quiz"].split("---") if q.strip()]
            st.session_state.quiz_generated = True
            st.session_state.quiz_timer_start = datetime.now()
        except Exception as e:
            st.error("Quiz generation failed.")
            st.exception(e)

    # ✅ Timer bar display
    if st.session_state.quiz_timer_start and st.session_state.quiz_questions and not st.session_state.quiz_submitted:
        html(f"""
        <div id="timer-container" style="position: fixed; top: 0; left: 0; width: 100%; background-color: #000; color: #fff; font-size: 28px; font-weight: bold; text-align: center; padding: 20px 0; z-index: 9999; box-shadow: 0 2px 10px rgba(0,0,0,0.5); font-family: 'Segoe UI', sans-serif;">
            ⏳ Time left: <span id="time-display">10:00</span>
            <div style="margin-top: 10px; height: 14px; background: #555; width: 80%; margin-left: auto; margin-right: auto; border-radius: 8px; overflow: hidden;">
                <div id="progress-bar" style="height: 100%; width: 100%; background: #ffcc00;"></div>
            </div>
        </div>

        <form id="auto-submit-form"><input type="hidden" name="autosubmit" value="1"/></form>

        <script>
            let duration = 600;
            let endTime = Date.now() + duration * 1000;
            function updateTimer() {{
                const now = Date.now();
                const timeLeft = Math.max(0, endTime - now);
                const secondsLeft = Math.floor(timeLeft / 1000);
                const minutes = Math.floor(secondsLeft / 60);
                const seconds = secondsLeft % 60;
                const formatted = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
                document.getElementById("time-display").innerText = formatted;
                const progress = Math.max(0, (timeLeft / (duration * 1000)) * 100);
                document.getElementById("progress-bar").style.width = progress + "%";
                if (timeLeft > 0) {{
                    requestAnimationFrame(updateTimer);
                }} else {{
                    document.getElementById("timer-container").innerText = "⏰ Time is up! Auto-submitting...";
                    document.forms["auto-submit-form"].submit();
                }}
            }}
            requestAnimationFrame(updateTimer);
        </script>
        """, height=100)
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # ✅ Render the Quiz
    if st.session_state.quiz_questions and not st.session_state.quiz_submitted:
        st.markdown("### 📝 Your Adaptive Quiz:")
        for i, qblock in enumerate(st.session_state.quiz_questions, 1):
            lines = qblock.strip().split("\n")
            question_line = lines[0]
            options = lines[1:5]
            answer_line = next((l for l in lines if l.lower().startswith("answer:")), "")
            explanation_line = next((l for l in lines if l.lower().startswith("explanation:")), "")
            correct_answer = answer_line.split(":")[-1].strip()

            st.markdown(f"**Q{i}:** {question_line.replace(f'Q{i}:', '').strip()}")
            selected = st.radio("Choose your answer:", options, key=f"q{i}_option", index=None, label_visibility="collapsed")

            st.session_state.quiz_answers[f"q{i}"] = {
                "selected": selected,
                "correct": correct_answer,
                "explanation": explanation_line
            }

        # ✅ Manual submit
        if st.button("Submit Quiz", key="submit_quiz") and not st.session_state.quiz_submitted:
            st.session_state.quiz_submitted = True

    # ✅ Save and Show Results
    if st.session_state.quiz_submitted and not st.session_state.quiz_saved:
        score = 0
        for i in range(1, len(st.session_state.quiz_questions) + 1):
            answer = st.session_state.quiz_answers.get(f"q{i}", {})
            selected = answer.get("selected", None)
            correct = answer.get("correct", "")
            if selected:
                user_answer = selected.split(".")[0].strip()
                if user_answer == correct:
                    score += 1
        save_quiz_result(st.session_state.get("student_name", "Unknown"), score, len(st.session_state.quiz_questions), st.session_state.quiz_answers, st.session_state.get("topic_input", "Unknown Topics"))
        st.session_state.quiz_saved = True

    if st.session_state.quiz_submitted:
        st.markdown("### ✅ Quiz Results")
        score = 0
        for i in range(1, len(st.session_state.quiz_questions) + 1):
            answer = st.session_state.quiz_answers.get(f"q{i}", {})
            selected = answer.get("selected", None)
            correct = answer.get("correct", "")
            explanation = answer.get("explanation", "")
            if not selected:
                st.warning(f"Q{i}: No answer selected.")
                continue
            user_answer = selected.split(".")[0].strip()
            if user_answer == correct:
                score += 1
                st.success(f"Q{i}: Correct ✅")
            else:
                st.error(f"Q{i}: Incorrect ❌ | Correct Answer: {correct}")
            st.info(explanation)

        st.markdown(f"### 🏁 Final Score: **{score} / {len(st.session_state.quiz_questions)}**")

        if st.button("Finish", key="finish_quiz"):
            for key in ["raw_quiz", "quiz_questions", "quiz_answers", "quiz_submitted", "quiz_saved", "quiz_generated", "quiz_timer_start", "quiz_confirmed", "topic_input", "student_name"]:
                st.session_state.pop(key, None)
            st.rerun()

# ----------------------------
# 📊 Student Evaluations
# ----------------------------
elif page == "📊 Student Evaluations":
    st.header("📊 Student Quiz Attempts")

    filepath = os.path.join(os.path.dirname(__file__), "student_quiz_attempts.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        student_names = sorted(str(name) for name in df["name"].unique())
        selected_name = st.selectbox("Filter by student name:", ["All"] + student_names)

        if selected_name != "All":
            df = df[df["name"] == selected_name]

        st.dataframe(df[["name", "timestamp", "score", "total"]])

        st.subheader("📊 Score Trend Over Time")
        st.line_chart(df.set_index("timestamp")[["score"]])

        st.subheader("📊 Total Scores")
        df_plot = df.set_index("topics")
        st.bar_chart(df_plot["score"])

    else:
        st.info("No quiz attempts found yet.")

# ----------------------------
# 📚 Topic Explorer
# ----------------------------
elif page == "📚 Topic Explorer":
    st.header("📚 Topic Explorer – Learn Before You Quiz")

    raw_input = st.text_input("Enter one or more topics to explore (comma-separated):", placeholder="e.g., Support Vector Machines, GANs, Deep Learning")

    selected = [t.strip() for t in raw_input.split(",") if t.strip()]

    def get_gpt_summary(topic):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful tutor specialised in all the technical domains."},
                    {"role": "user", "content": f"Give a 6-8 sentence description about '{topic}' in respective domain for students, including a technical and non-technical explanation."}
                ]
            )
            return response.choices[0].message.content
        except Exception:
            return "AI summary unavailable."

    for topic in selected:
        st.subheader(f"🔹 {topic}")
        with st.spinner("Generating AI summary..."):
            summary = get_gpt_summary(topic)
        st.markdown(f"**🧠 AI Summary:** {summary}")

        with st.spinner("🔗 Fetching web links..."):
            web_links = fetch_web_links(topic)
            import logging
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            logging.debug(f"🔍 Fetched links for topic '{topic}': {web_links}")

        if web_links:
            st.markdown("**📘 External Resources:**")
            for i, link in enumerate(web_links, 1):
                st.markdown(f"- **Source {i}:** [{link}]({link})")
        else:
            st.warning("⚠️ No relevant web links found.")

# ----------------------------
# 👤 Profile Page
# ----------------------------
elif page == "👤 Profile":
    st.header("👤 My Profile")

    # Fetch details from session_state
    full_name = st.session_state.get("full_name", "Not Available")
    email = st.session_state.user.get("email", "Not Available")
    university_id = st.session_state.get("university_id", "Not Available")
    department = st.session_state.get("department", "Not Available")
    phone = st.session_state.get("phone", "Not Provided")
    bio = st.session_state.get("bio", "No bio yet")
    role = st.session_state.get("user_role", "Unknown")

    # Profile Card
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px;">
        <h2 style="color: #333;">{full_name}</h2>
        <h4 style="color: #333;">{role}</h4>
         <p style="color: black;"><strong>Email:</strong> {email}</p>
        <p style="color: black;"><strong>University ID:</strong> {university_id}</p>
        <p style="color: black;"><strong>Department:</strong> {department}</p>
        <p style="color: black;"><strong>Phone:</strong> {phone}</p>
        <p style="color: black;"><strong>Bio:</strong> {bio}</p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# 📈 My Results (Student Only)
# ----------------------------
elif page == "📈 My Results":
    st.header("📈 My Quiz Results")

    # Load student's quiz attempts
    filepath = os.path.join(os.path.dirname(__file__), "student_quiz_attempts.json")
    
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Filter only this student's attempts
        student_name = st.session_state.get("full_name", "Unknown")
        df = df[df["name"] == student_name]

        if not df.empty:
            st.dataframe(df[["timestamp", "topics", "score", "total"]]) 

            st.subheader("📈 Score Trend Over Time")
            st.line_chart(df.set_index("timestamp")[["score"]])

            st.subheader("📊 Score Distribution")
            df_plot = df.set_index("topics")
            st.bar_chart(df_plot["score"])

        else:
            st.info("You have not attempted any quizzes yet.")
    else:
        st.info("No quiz attempts found yet.")