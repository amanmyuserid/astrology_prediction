# ✨ Astrology Chatbot - Personalized Astrological Predictions

Welcome to the **Astrology Chatbot**, an interactive web application that delivers personalized astrological predictions based on **Vedic principles**. This intelligent system combines rule-based logic with **Google Gemini AI** to offer relevant, accurate insights in real-time.

Whether you're curious about your **love life**, **career**, **health**, or **financial future**, the chatbot uses your birth chart and predefined Excel rules to guide you meaningfully.

---

## 🌟 Features

- **🔮 Personalized Predictions**: Accurate insights based on DOB, TOB, POB, and planetary placements.
- **🧠 Intelligent Data Collection**: Gemini AI dynamically requests only essential missing info like relationship status, ensuring minimal user friction.
- **📚 Rule-Based Reasoning**: Predictions are derived strictly from an Excel-based knowledge bank containing structured astrological rules.
- **🌐 Multilingual Support**: Understands English, Romanized Hindi (Hinglish), and Devanagari scripts.
- **💾 Persistent User Data**: Stores user profiles and interaction history in `user_data.sqlite` using `aiosqlite`.
- **⚡ Real-Time Interaction**: WebSocket-powered communication for live conversations via FastAPI.
- **🧩 Modular Design**: Cleanly separated backend, UI, database, and logic components.

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.8+
- pip (Python package installer)
- Google Gemini API Key (set as `GEMINI_API_KEY` environment variable)

---

### 1. Clone the Repository

```bash
git clone https://github.com/amanmyuserid/astrology_prediction.git
cd astrology_prediction


⸻

2. Install Dependencies

pip install -r requirements.txt

Your requirements.txt should include:

fastapi
uvicorn[standard]
pydantic
pytz
pandas
openpyxl
google-generativeai
aiosqlite


⸻

3. Prepare the Knowledge Base

Ensure Refined_Knowledge_Bank (1).xlsx is present in the root directory. This contains the astrological rules.

⸻

4. Set the Google Gemini API Key

On Linux/macOS:

export GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"

On Windows CMD:

set GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"

On Windows PowerShell:

$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"


⸻

💻 Running the Application

Step 1: Start the FastAPI Backend

uvicorn app:app --host 0.0.0.0 --port 8000 --ws websockets --ws-ping-interval 3 --ws-ping-timeout 10

Runs at: http://0.0.0.0:8000

⸻

Step 2: Start the Frontend (Static Server)

Open a second terminal:

python -m http.server 8001

Access in browser: http://127.0.0.1:8001/ui.html

⸻

Step 3: Connect UI to Backend

Make sure the following line exists in your ui.html file:

const API_WS_URL = 'ws://127.0.0.1:8000/ws';


⸻

📸 Screenshot


⸻

📁 Project Structure

astrology_prediction/
├── app.py
├── check_data_needs.py
├── prediction_of_user_query.py
├── retrieve_astro_chart.py
├── retrieve_index_of_similar_question.py
├── retrieve_index_on_birth_chart.py
├── Refined_Knowledge_Bank (1).xlsx
├── requirements.txt
├── ui.html
├── ui_screenshot.jpg
└── user_data.sqlite  # (auto-generated after first run)


⸻

🧠 How It Works
	1.	User Connects: UI establishes WebSocket connection with backend.
	2.	User Details: Basic info (DOB, TOB, POB) is collected and stored.
	3.	Query Evaluation:
	•	Gemini checks if more info is required.
	•	If so, it prompts dynamically and updates the DB.
	4.	Rule Retrieval:
	•	Chart-based and question-based rule filtering is applied.
	5.	Prediction:
	•	Gemini generates a response strictly based on matched Excel rules.
	6.	Final Output: Prediction is shown on the frontend and stored.

⸻

🛠 Troubleshooting

Issue	Fix
WebSocket disconnects	Use --ws websockets --ws-ping-interval 3 --ws-ping-timeout 10 in Uvicorn
Page reloads on submit	Ensure e.preventDefault() is used in onsubmit handlers
JS ReferenceError	Define all helper functions before calling
coroutine not serializable	Use await with all async function calls
Wrong prediction language	Review prompt formatting in prediction_of_user_query.py
Bot doesn’t ask for missing info	Tweak check_data_needs.py prompt for better inference


⸻

🤝 Contributions

Pull requests, bug reports, and feature suggestions are welcome.
Let’s build the smartest astrology chatbot together!

⸻


Let me know if you want to add a **badge section**, **demo video**, or **license info** at the bottom.