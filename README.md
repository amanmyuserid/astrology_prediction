Here’s your well-structured and production-grade README.md file for the Astrology Chatbot, including the correct Markdown formatting and screenshot reference:

⸻


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

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd astrology-chatbot

2. Install Dependencies

pip install -r requirements.txt

Your requirements.txt should contain:

fastapi
uvicorn[standard]
pydantic
pytz
pandas
openpyxl
google-generativeai
aiosqlite

3. Place the Knowledge Base

Ensure the file Refined_Knowledge_Bank (1).xlsx is present in the root folder.

4. Set Google Gemini API Key

On Linux/macOS:

export GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"

On Windows CMD:

set GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"

On Windows PowerShell:

$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"


⸻

💻 Running the Application

Step 1: Start Backend (FastAPI WebSocket)

uvicorn app:app --host 0.0.0.0 --port 8000 --ws websockets --ws-ping-interval 3 --ws-ping-timeout 10

	•	WebSocket pings keep the LLM session alive during long processing.
	•	Server will be available at: http://0.0.0.0:8000

Step 2: Start Frontend (Python HTTP Server)

In another terminal:

python -m http.server 8001

	•	Open in browser: http://127.0.0.1:8001/ui.html

Step 3: Check JavaScript Connection

Ensure this line in ui.html is present:

const API_WS_URL = 'ws://127.0.0.1:8000/ws';


⸻

📸 Screenshot


⸻

📁 Project Structure

astrology-chatbot/
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
└── user_data.sqlite  # (auto-created)


⸻

🧠 How It Works
	1.	User connects: UI opens and connects via WebSocket.
	2.	User profile creation: If new, the bot asks DOB, TOB, POB, etc., and saves them.
	3.	Query processing:
	•	Gemini checks if more info (e.g., relationship status) is needed → prompts the user.
	•	Retrieved rules (matching chart + query) are prepared from Excel.
	•	Gemini answers strictly based on matched rules and user style.
	4.	Prediction delivery: Displayed in chat with dynamic language/script handling.
	5.	Data saved: All updates persist in user_data.sqlite.

⸻

🛠 Troubleshooting

Problem	Solution
WebSocket Disconnect	Ensure Uvicorn has correct --ws flags.
Page refreshes on form submit	Make sure e.preventDefault() is in place in all form handlers.
ReferenceError in JS	Move all helper functions above usage inside <script>.
TypeError: coroutine not serializable	Missing await on an async function.
Wrong language in prediction	Adjust prompt in prediction_of_user_query.py to enforce desired style.
No extra questions asked	Adjust prompt in check_data_needs.py to make Gemini more aggressive in asking for key info.


⸻

🤝 Contributions

All contributions, bug reports, and suggestions are welcome!
Feel free to fork and enhance this project for your own astrology-powered applications.

⸻


---

To complete the setup:

- Save your **chatbot UI screenshot** as `ui_screenshot.jpg` in the same root folder as `README.md`.
- This Markdown file can be directly saved as `README.md`.

Let me know if you'd like a GitHub-flavored version with badges or contributors' section.