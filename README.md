# EduMentor

**Your AI-Powered Personalized Learning Assistant**

---

## Overview

**EduMentor** is an AI-driven educational assistant designed to personalize learning experiences for students and support educators with adaptive quizzes, learning path generation, and real-time analytics. Built with OpenAI's GPT models, Streamlit, and SerpAPI integration, EduMentor dynamically adapts to user needs, offering tailored quizzes, topic exploration, and intelligent learning guidance.

---

## Features

- **🖊️ Chat Assistant**: GPT-powered real-time conversation to answer queries and guide learning.
- **🔢 Adaptive Quizzes**: Dynamically generated quizzes based on user-selected topics with timers and feedback.
- **💡 Topic Explorer**: Automatically fetches topic summaries and top web resources using SerpAPI.
- **🔹 Personalized Learning Path**: Concept graphs generated for weak topics with prerequisite mapping, importance scoring, and interactive visualizations.
- **🔬 Student Analytics**: Track performance trends, quiz scores, and adaptive learning metrics.

---

## Tech Stack

- **Frontend & Framework**: [Streamlit](https://streamlit.io/)
- **AI Models**: [OpenAI GPT-4](https://openai.com/)
- **Web Search**: [SerpAPI](https://serpapi.com/)
- **Visualization**: PyVis, NetworkX, Matplotlib
- **Backend Utilities**: Python, dotenv, glob, datetime

---

## Setup Instructions

1. **Clone the Repository**
```bash
git clone https://github.com/your-username/edumentor.git
cd edumentor
```

2. **Create and Activate Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. **Install Requirements**
```bash
pip install -r requirements.txt
```

4. **Set Up Environment Variables**

Create a `.env` file and add:
```bash
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
FIREBASE_API_KEY=your_google_api_key
```

5. **Create a `serviceAccountKey.json` file**

Create the key at [link](https://console.firebase.google.com/).

After creating the key, rename it to serviceAccountKey add the json file to a new firebase folder in the streamlit_ui folder. 

Update the credentitals.Certficate with your key filename in the line: "firebase/<your_file_name>.json".

```python
# firestore_db.py 

if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "firebase/edumentor-77688-firebase-adminsdk-fbsvc-2d32c0d42b.json"))
    firebase_admin.initialize_app(cred)
```

6. **Note for Running Locally (Windows/Mac users)**

When making API requests to the backend in Mac, replace `localhost` with `127.0.0.1` in the URL inside `main.py`:

```python
# main.py (line inside Adaptive Quiz page)
response = requests.post(
    "http://127.0.0.1:5000/api/generate-quiz",
    json={"topics": selected_topics, "difficulty": random.choice(["Easy", "Medium", "Hard"]), "num_questions": 10}
)
```

7. **Run the Application**
```bash
python run.py
streamlit run streamlit_ui/main.py (In another terminal)
```

---

## Project Structure

```bash
|-- app.py
|-- pages/
|   |-- Chat Assistant
|   |-- Adaptive Quiz
|   |-- Topic Explorer
|   |-- Learning Path
|-- utils/
|   |-- quiz_generator.py
|   |-- concept_graph.py
|   |-- search_api.py
|-- chat_logs/
|-- Graphs/
|-- README.md
|-- requirements.txt
|-- .env (not committed)
```

---

## Demo Screenshots

## Chat Assistant
![chat](https://github.com/user-attachments/assets/c32b2930-e184-4505-aefb-aca180f3f8b3)

---

## Adaptive Quiz
![quiz](https://github.com/user-attachments/assets/b8f58d3f-4703-4e77-8240-a210e25a2d41)

---

## Learning Path
![path](https://github.com/user-attachments/assets/9c4eafc7-65f6-4065-b888-3b5de7714648)

---

## Knowledge Graph
![graph](https://github.com/user-attachments/assets/d3778350-6d5f-463e-8b28-dde80f787ee2)

---

## Topic Explorer
![topics](https://github.com/user-attachments/assets/9915fee9-2f72-4916-b3be-fcdf1781a858)

---

## Future Improvements

- Integrate spaced repetition for quiz questions.
- Add role-based dashboards for students and teachers.
- Enable saving and downloading of personalized learning reports.
- Add multi-language support.

---


## Acknowledgments

- [OpenAI](https://openai.com/)
- [Streamlit](https://streamlit.io/)
- [SerpAPI](https://serpapi.com/)
- [PyVis](https://pyvis.readthedocs.io/en/latest/)
- [Google Firebase Console](https://console.firebase.google.com/)

---

**Contributors:**

- Avantika Balaji

- Jashwanth Kandula

- Mohit Varma Sagi

- Palak Kakani
 
- Rakshitha Narasimhaiah

- Shreya Vyas

---

**EduMentor — Empowering Personalized Learning with AI.** 📚🔍

