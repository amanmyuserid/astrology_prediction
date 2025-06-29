import google.generativeai as genai
import os
import json
from datetime import datetime
import pytz # For IST timezone

# --- Configure Gemini API ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Using the specified model for text generation
# Ensure 'gemini-2.5-flash-lite-preview-06-17' is available. If not, use 'gemini-1.5-flash-latest'
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17") 

# Define IST timezone globally or import it if already defined elsewhere
try:
    IST = pytz.timezone('Asia/Kolkata')
except ImportError:
    # Fallback for IST if pytz is not installed or available
    import datetime # Need to import datetime again for timezone
    IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def predict_user_query(
    user_data: dict,
    current_time_in_IST: datetime,
    retrieved_rules_text: str,
    user_question: str
) -> str:
    """
    Generates a personalized astrological prediction based on user data,
    current time, and provided astrological rules, using an LLM.

    The prediction MUST be derived ONLY from the content of retrieved_rules_text.

    Args:
        user_data (dict): A dictionary containing user's astrological data
                          (e.g., basic_data, on_demand_data, planets).
                          Expected to have 'basic_data' (with date_of_birth),
                          'planets' (with house positions), and 'on_demand_data'.
        current_time_in_IST (datetime): The current time in IST timezone.
        retrieved_rules_text (str): A string containing astrological rules
                                    in "Condition: ...\nResult: ..." format.
                                    The prediction must be based ONLY on these rules.
        user_question (str): The original question asked by the user.

    Returns:
        str: The final astrological prediction in text format.
    """
    
    # Extract relevant user data for the prompt
    basic_data = user_data.get("basic_data", {})
    on_demand_data = user_data.get("on_demand_data", {})
    planets_data = user_data.get("planets", {})

    # Calculate user's current age for the prompt, if DOB is available
    user_dob_str = basic_data.get("date_of_birth")
    current_age = "N/A"
    if user_dob_str and len(user_dob_str.split('/')) == 3: # Basic validation for YYYY/MM/DD
        try:
            # Adjust DOB format for datetime.strptime if needed (e.g., 'YYYY/MM/DD' to 'YYYY-MM-DD')
            dob_parts = user_dob_str.split('/')
            # Safely create the formatted DOB string, ensuring month/day are 2 digits
            dob_formatted = f"{dob_parts[0]}-{dob_parts[1].zfill(2)}-{dob_parts[2].zfill(2)}"
            
            dob_obj = datetime.strptime(dob_formatted, "%Y-%m-%d")
            today = current_time_in_IST.date()
            age = today.year - dob_obj.year - ((today.month, today.day) < (dob_obj.month, dob_obj.day))
            current_age = age
        except (ValueError, IndexError): # Catch both ValueError for bad format and IndexError for not enough parts
            current_age = "Invalid/Malformed DOB format"

    # Format user's astrological data for the prompt
    formatted_user_astrology = {
        "Name": basic_data.get("name", "N/A"),
        "Date of Birth": basic_data.get("date_of_birth", "N/A"),
        "Current Age": current_age, # This will now contain the calculated age or error message
        "Time of Birth": basic_data.get("time_of_birth", "N/A"),
        "Place of Birth": basic_data.get("place_of_birth", "N/A"),
        "Natal Planet Positions (House)": {
            planet: house for planet, house in planets_data.items()
        },
        "Additional User Details (from interaction)": on_demand_data
    }

    # Construct the prompt for the LLM
    prompt = f"""
You are a highly skilled and compassionate Vedic astrologer. Your task is to provide a concise and clear astrological prediction to the user, based *ONLY* on the provided astrological rules.

**STRICT RULE:** You MUST base your prediction SOLELY on the "Result" sections of the "Retrieved Astrological Rules" provided below. Do NOT introduce external astrological knowledge, personal opinions, or information not explicitly present in the provided rules. If multiple rules apply, synthesize their "Result" sections into a coherent prediction. If no rules are provided (i.e., "Retrieved Astrological Rules" is empty or states no rules), state that you cannot give a prediction based on the given rules.

**TEXT STYLE AND LANGUAGE RULE:** The prediction MUST strictly match the exact textual style, script, and language of the "User Question" (e.g., Romanized Hindi, Devanagari, English). No translation, transcription, or mixing scripts.

**PREDICTION STRUCTURE AND FORMATTING:**
-   Start the prediction with a polite and respectful salutation directly addressing the user by their name.
-   Do not mention retrieve rules or astrological data directly in the prediction.
-   Use a friendly and professional tone throughout the prediction.
-   Introduce the prediction clearly, providing astrological insights relevant to their query.
-   Present the core prediction in one or two well-structured paragraphs for readability.
-   Use line breaks to separate paragraphs.
-   Use always small paragraphs (2-3 sentences max) for clarity.
-   If the prediction is negative or uncertain, do so with sensitivity and care.
-   If the prediction is positive, express it with optimism and encouragement.
-   Ensure the prediction is culturally appropriate and sensitive to the user's background.
-   Conclude with a polite closing remark.


**Context Information for Prediction:**

User Question: "{user_question}"

User Astrological Data:
```json
{json.dumps(formatted_user_astrology, indent=2, ensure_ascii=False)}
```

Current Time (IST): {current_time_in_IST.isoformat()}

Retrieved Astrological Rules (Use ONLY these rules for the prediction):
```
{retrieved_rules_text}
```

Based on the above, provide your astrological prediction.
"""
    
    # Optional: Print prompt for debugging
    # print("--- Gemini Prediction Prompt ---")
    # print(prompt)
    # print("-------------------------------")

    try:
        # Call the Gemini model
        # Using await as `model.generate_content` is now assumed to be async (or wrapped via asyncio.to_thread)
        response = model.generate_content(prompt)
        prediction_text = response.text.strip()
        
        # Post-process for "No rules" scenario if LLM doesn't follow strictly
        # If the retrieved_rules_text is empty or explicitly says no rules,
        # ensure the prediction also reflects that.
        if "No matching rules found" in retrieved_rules_text or not retrieved_rules_text.strip():
            # Check if the LLM's response contains a clear "cannot predict" phrase in English or Hindi
            if not any(phrase in prediction_text.lower() for phrase in ["cannot give a prediction", "no precise prediction", "कोई सटीक भविष्यवाणी नहीं"]):
                return "प्रियवर, दिए गए नियमों के आधार पर मैं आपकी इस जिज्ञासा के लिए कोई सटीक भविष्यवाणी नहीं दे सकता/सकती हूँ।"
        
        return prediction_text
    except Exception as e:
        print(f"ERROR: Failed to get prediction from Gemini: {e}")
        return "मुझे आपकी भविष्यवाणी देने में कुछ समस्या आ रही है। कृपया कुछ देर बाद पुनः प्रयास करें।" # Graceful fallback message


# Example Usage (for testing this file independently)
if __name__ == "__main__":
    import asyncio # Needed to run async functions for testing
    import os # For setting API key if not in environment

    # Set a dummy API key for testing if not in environment
    if "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_API_KEY" # Replace with a real key for actual LLM calls

    # Ensure the model is correctly initialized as async if run directly
    # This is a hack for the example to make model.generate_content awaitable.
    # In your main app, model from `genai.AsyncGenerativeModel` (or `asyncio.to_thread(genai.GenerativeModel)`) is used.
    _temp_model_instance = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")
    async def _test_generate_content_wrapper(prompt_text):
        return await asyncio.to_thread(_temp_model_instance.generate_content, prompt_text)
    
    # Temporarily override the module's model.generate_content for testing this file
    # This is for example execution only, not for production integration.
    model.generate_content = _test_generate_content_wrapper


    async def main():
        sample_user_data = {
            "basic_data": {
                "name": "Aman Kumar",
                "date_of_birth": "1990/05/15",
                "time_of_birth": "10:12",
                "place_of_birth": "delhi, india"
            },
            "on_demand_data": {
                "relationship_status": "single",
                "current_job_title": "Software Engineer"
            },
            "predictions": [],
            "latitude": 28.7041,
            "longitude": 77.1025,
            "planets": {
                "Sun": 7, "Moon": 5, "Mars": 10, "Mercury": 12, "Jupiter": 10,
                "Venus": 7, "Saturn": 11, "Rahu": 6, "Ketu": 6
            }
        }

        sample_current_time = datetime.now(IST)

        sample_retrieved_rules_love = """
Condition: Saturn in 6 AND Moon in 2 AND AGE (30)
Result: किसी पुराने मित्र से मनमुटाव हो सकता है।

Condition: Sun in 5 AND DOB (1949-06-29 to 1951-06-29, 1980-06-29 to 1983-06-29)
Result: आपकी प्रेम जीवन में मधुरता आएगी और नए संबंध बन सकते हैं।

Condition: Venus in 7 AND DOB (1990-01-01 to 1995-12-31)
Result: प्रेम संबंध मजबूत होंगे और विवाह का योग बन सकता है।
"""
        sample_retrieved_rules_health = """
Condition: Mercury in 12 AND DOB (1939-06-29 to 1940-06-29, 2022-06-29 to 2024-06-29)
Result: सेहत को लेकर थोड़ी चिंता हो सकती है।

Condition: Mars in 6 AND AGE (35)
Result: पुरानी बीमारी फिर से उभर सकती है, सावधानी बरतें।
"""
        sample_retrieved_rules_empty = """
No matching rules found.
"""

        print("--- Prediction for Love Life (using matching rules) ---")
        prediction_love = await predict_user_query(
            sample_user_data,
            sample_current_time,
            sample_retrieved_rules_love,
            "Meri love life kaisi rahegi?" # Hinglish query
        )
        print(prediction_love)
        print("\n" + "="*80 + "\n")

        print("--- Prediction for Health (using matching rules) ---")
        prediction_health = await predict_user_query(
            sample_user_data,
            sample_current_time,
            sample_retrieved_rules_health,
            "Meri sehat kesi rahegi agle mahine me?" # Hinglish query
        )
        print(prediction_health)
        print("\n" + "="*80 + "\n")

        print("--- Prediction for Empty Rules ---")
        prediction_empty = await predict_user_query(
            sample_user_data,
            sample_current_time,
            sample_retrieved_rules_empty,
            "What does my future hold?" # English query
        )
        print(prediction_empty)
        print("\n" + "="*80 + "\n")

    # Run the example usage
    asyncio.run(main())
