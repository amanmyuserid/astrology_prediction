import google.generativeai as genai
import os
import json # For pretty-printing user data and parsing Gemini's JSON response
import asyncio # <--- ADDED for asyncio.to_thread

# Configure Gemini API (ensure GEMINI_API_KEY is set in your environment variables)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- CRITICAL FIX 1: Revert to GenerativeModel and use asyncio.to_thread ---
# This model is synchronous, but we will call it asynchronously using asyncio.to_thread.
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")

# --- CRITICAL FIX 2: Keep the function itself async ---
async def check_for_additional_data(user_data: dict, user_query: str) -> dict:
    """
    Uses Gemini to determine if additional, minimal information is needed from the user
    to provide a more precise astrological prediction for the given query,
    and returns the assessment as a structured JSON object.

    Args:
        user_data (dict): A dictionary containing available user astrological data
                          (basic_data, on_demand_data, planets, etc.).
        user_query (str): The user's specific question (e.g., "how is my love life?").

    Returns:
        dict: A dictionary representing the JSON output from Gemini, with the following structure:
              {
                "data_needs_from_user": bool,
                "number_of_question": int,
                "question_list": [
                  {"question": str, "title": str, "e.g.": str}
                ]
              }
              Returns an error dictionary if communication or parsing fails.
    """
    # Format user_data into a readable JSON string for the LLM
    formatted_user_data = json.dumps(user_data, indent=2)

    prompt = f"""
You are an intelligent astrology data assistant. Your task is to review a user's question and their currently available profile data.

Based on the provided user query and data, determine if asking for *minimal, additional information* from the user would significantly help in generating a more precise astrological prediction. Your goal is to avoid overwhelming the user, so only ask if the missing information is **absolutely critical and fundamentally improves** the prediction.

Your response MUST be a JSON object. If the `question_list` is not empty, `data_needs_from_user` must be `true`. If `question_list` is empty, `data_needs_from_user` must be `false`.
always generate at least randomly between 1 to 3 questions related to question but each one different.

Here is the exact JSON schema you must follow:
```json
{{
  "data_needs_from_user": true | false, // true if more data is needed, false otherwise
  "number_of_question": integer,       // Count of questions in 'question_list', 0 if no data needed
  "question_list": [                   // Array of questions, empty if no data needed
    {{
      "question": "string",            // The specific question to ask the user
      "title": "string",               // A concise, snake_case key for storing this data in 'on_demand_data' (e.g., "relationship_status", "current_job_title", "health_concerns")
      "e.g.": "string"                 // An example or hint for the user's answer (e.g., "single, married, divorced", "Software Developer, Project Manager", "Migraines, Diabetes, etc.")
    }}
  ]
}}
```
User Query: "{user_query}"

Current User Data:
{formatted_user_data}
"""

    # --- CRITICAL FIX 3: Use asyncio.to_thread to run synchronous LLM call asynchronously ---
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        gemini_text_response = response.text.strip()
        
        if gemini_text_response.startswith("```json") and gemini_text_response.endswith("```"):
            json_string = gemini_text_response[7:-3].strip()
        else:
            json_string = gemini_text_response
            
        parsed_response = json.loads(json_string)
        return parsed_response
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Gemini's JSON response: {e}", "raw_response": gemini_text_response}
    except Exception as e:
        return {"error": f"Error communicating with Gemini: {e}"}

# Example Usage: (This part remains the same for testing the async function)
if __name__ == "__main__":
    import asyncio # Needed to run async functions
    from typing import Dict # Needed for Dict in MockWebSocket

    # Define placeholder data and mocks for testing the async function
    # In your main application, these would be imported or correctly instantiated.
    class MockWebSocket:
        def __init__(self):
            self._send_queue = asyncio.Queue()
            self._receive_queue = asyncio.Queue()

        async def send_json(self, data: Dict):
            print(f"\n--- WS SENT (UI Action) ---\n{json.dumps(data, indent=2, ensure_ascii=False)}\n")
            # For testing, we might want to automatically put a response in the receive queue
            # if this mock is used for full llm_process simulation.
            # Here, just simulating the output.

        async def receive_json(self):
            # This is where the test would block waiting for a "user response"
            print("WS RECEIVE: (Waiting for simulated user input...)")
            response = await self._receive_queue.get()
            return response

        # Helper for tests to put a simulated user response
        async def _put_user_response(self, response_data: Dict):
            await self._receive_queue.put(response_data)


    async def get_next_user_response(websocket: MockWebSocket) -> Dict:
        # This mocks your get_next_user_response that waits for user input
        return await websocket.receive_json()

    PREDICTION_TEMPLATES = [
        "Your love life will flourish, indicating new beginnings and harmony.",
        "Expect some challenges in your career this quarter, requiring careful planning.",
        "Health needs attention; focus on diet and exercise for overall well-being."
    ]

    class MockIST: # Simple mock for IST if pytz is not used in test context
        def isoformat(self):
            return datetime.now().isoformat() + "+05:30"
    IST = MockIST()

    user_data_store = {}
    def save_database(mob: str):
        # Placeholder for actual database save
        print(f"DEBUG: Database for {mob} saved (simulated). Current on_demand_data: {user_data_store[mob]['db_record']['on_demand_data']}")

    # End of placeholder definitions for testing context

    async def test_check_for_additional_data():
        example_user_data_1 = {
            "basic_data": {
                "name": "Aman Kumar",
                "date_of_birth": "1990/05/15",
                "time_of_birth": "10:12",
                "place_of_birth": "delhi, india"
            },
            "on_demand_data": {
                "goal": "To become software engineer"
            },
            "predictions": [],
            "latitude": 28.7041,
            "longitude": 77.1025,
            "planets": {
                "Sun": 6, "Moon": 11, "Mars": 5, "Mercury": 11, "Jupiter": 11,
                "Venus": 5, "Saturn": 4, "Rahu": 6, "Ketu": 9
            }
        }

        # Test Case 1: Love life query, limited on-demand data
        user_query_1 = "How is my love life looking in the coming year?"
        print(f"Test Case 1: User Query: '{user_query_1}'")
        data_needed_1 = await check_for_additional_data(example_user_data_1, user_query_1)
        print("\n--- Gemini's Assessment (JSON Output) ---")
        print(json.dumps(data_needed_1, indent=2, ensure_ascii=False))
        print("\n" + "="*50 + "\n")

        # Test Case 2: Health query, no health-specific on-demand data
        user_query_3 = "Will my health be good in the next few months?"
        example_user_data_1["on_demand_data"] = {"goal": "To become software engineer"} # Reset for test 3
        print(f"Test Case 2: User Query: '{user_query_3}'")
        data_needed_3 = await check_for_additional_data(example_user_data_1, user_query_3)
        print("\n--- Gemini's Assessment (JSON Output) ---")
        print(json.dumps(data_needed_3, indent=2, ensure_ascii=False))
        print("\n" + "="*50 + "\n")


    # Run the test for check_for_additional_data
    asyncio.run(test_check_for_additional_data())
