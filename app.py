from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json
import time
import random
from typing import Dict, Any, List
from datetime import datetime
import pytz
from check_data_needs import check_for_additional_data
from retrieve_astro_chart import get_llm_formatted_rules_string
from retrieve_index_on_birth_chart import get_matching_rules_by_planet_age_time
from retrieve_index_of_similar_question import get_relevant_excel_indices
from prediction_of_user_query import predict_user_query

# --- Global Configurations & Constants ---
app = FastAPI()
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
IST = pytz.timezone('Asia/Kolkata')

PREDICTION_TEMPLATES = [
    "Aapke liye aane wala samay aarthik roop se behtar ho sakta hai. Nivesh karne se pehle sochna zaroori hai.",
    "Swasthya par vishesh dhyan dein. Choti-moti pareshaniyon ko nazarandaaz na karein.",
    "Parivarik rishton mein madhurta aayegi. Kisi purane dost se mulakat ho sakti hai.",
    "Career mein nayi unchaiyan mil sakti hain, lekin mehnat aur samparpan zaroori hoga.",
    "Koi adhoora kaam poora ho sakta hai. Yatra ka yog ban raha hai.",
    "Aapko apne krodh par niyantran rakhna hoga. Shaant mann se liye gaye faisle safal honge.",
    "Prem sambandhon ke liye samay anukool hai. Apne partner ke saath samay bitayein.",
    "Aapki rachanatmak (creative) shakti badhegi. Naye ideas par kaam karne ka ye sahi samay hai."
]

# In-memory data store
user_data_store: Dict[str, Dict[str, Any]] = {}


# --- Pydantic Models for Data Validation (No Change) ---
class UserDetails(BaseModel):
    mob: str
    name: str
    date_of_birth: str
    time_of_birth: str
    place_of_birth: str

class ChatMessage(BaseModel):
    mob: str
    user_question: str

class CustomInput(BaseModel):
    mob: str
    custom_data: Dict[str, Any]


# --- Database Handling Function (No Change) ---
def save_database(mob: str):
    print(f"DEBUG: save_database() for {mob}. (Saving is disabled).")
    pass

# ==============================================================================
# STAGE 2: THE NEW, SELF-CONTAINED LLM PROCESS
# ==============================================================================

async def get_next_user_response(websocket: WebSocket) -> Dict:
    """
    Helper Function: Yeh user ke agle message ka intezaar karta hai.
    Yeh sirf 'submit_custom_input' type ke message ko hi accept karega.
    """
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        if message.get("type") == "submit_custom_input":
            return message
        else:
            print(f"WARN: Unexpected message type '{message.get('type')}' received. Waiting for 'submit_custom_input'.")
            # Yahan hum user ko bata sakte hain ki "Please submit the form."
            continue



async def llm_process(websocket: Any, mob: str, initial_question: str) -> str:
    """
    This function manages the entire interaction flow:
    1. Determines if more data is needed using Gemini's check_for_additional_data.
    2. Asks questions to the user if needed and collects responses.
    3. Saves collected data into db_record['on_demand_data'].
    4. Generates and returns a final prediction.

    Args:
        websocket: The WebSocket connection for communication.
        mob (str): User identifier.
        initial_question (str): The user's initial query.

    Returns:
        str: The final astrological prediction text.
    """
    print(f"DEBUG: Entering LLM Process for {mob}.")
    user_session = user_data_store[mob]
    db_record = user_session["db_record"]
    session_state = user_session["session_state"]

    print(f"User Data: {user_data_store}")
    
    
    # Step 1: Check if more data is needed from the user using Gemini
    print("DEBUG: Checking for additional data needs with Gemini.")
    
    # --- CRITICAL FIX: AWAITING THE ASYNC LLM CALL ---
    # The check_for_additional_data function must be an 'async def' function,
    # and its internal call to model.generate_content() must be 'await'.
    data_assessment = await check_for_additional_data(db_record, initial_question)

    if data_assessment.get("data_needs_from_user"):
        question_list = data_assessment.get("question_list", [])
        if question_list:
            print(f"DEBUG: Gemini recommends asking {len(question_list)} additional questions.")
            
            target_interactions = len(question_list)

            # Step 2: Ask questions and collect responses (Interaction Loop)
            for i, q_info in enumerate(question_list):
                interaction_num = i + 1
                
                question_text_from_gemini = q_info.get("question", f"Please provide more details (Question {interaction_num}).")
                title_key = q_info.get("title", f"on_demand_field_{interaction_num}") 
                example_hint = q_info.get("e.g.", "")

                # Removed display_message_in_chat_bubble from 'message' field
                # The question will now only appear as the 'label' for the input field.
                # The 'display_message_in_chat' flag is kept as False to prevent a chat bubble.
                print(f"DEBUG: Starting interaction {interaction_num}/{target_interactions}. Requesting data for: '{question_text_from_gemini}'")
                
                action_field_item = {
                    "id": title_key,          
                    "label": question_text_from_gemini,   
                    "required": False,        
                    "example": example_hint   
                }

                await websocket.send_json({
                    "type": "request_custom_data",
                    # Removed 'message': display_message_in_chat_bubble
                    "action_needed_fields": [action_field_item], 
                    "display_message_in_chat": False 
                })
                
                response = await get_next_user_response(websocket)
                
                if "custom_data" in response and title_key in response["custom_data"]:
                    db_record['on_demand_data'][title_key] = response["custom_data"][title_key]
                    save_database(mob)
                    print(f"DEBUG: Saved custom data for '{title_key}'. Current on_demand_data: {db_record['on_demand_data']}")
                else:
                    print(f"DEBUG: No data received for question '{title_key}' from user response: {response}. Skipping save.")
        else:
            print("DEBUG: Gemini indicated data needed, but provided an empty question_list. Proceeding without asking questions.")
    else:
        print("DEBUG: No further information required as per Gemini's assessment. Proceeding with available data.")

    # Step 3: Final Prediction generate karo
    print("DEBUG: Interaction complete (if any). Generating final prediction.")
    



    # My own logic for generating a prediction


    user_dob = db_record['basic_data'].get('date_of_birth', 'Unknown').replace("/", "-")
    user_planets_info = db_record.get('planets', {})
    planet_based_retrieved_idx = get_matching_rules_by_planet_age_time(user_dob, user_planets_info)

    question_simillarity_based_retrieved_idx = get_relevant_excel_indices(initial_question)

    print(f"\n\nDEBUG: Retrieved indices based on planet age and time: {planet_based_retrieved_idx}")
    print(f"\n\nDEBUG: Retrieved indices based on question similarity: {question_simillarity_based_retrieved_idx}")


    # Combine both sets of indices, ensuring uniqueness

    combined_retrieved_indices = set(planet_based_retrieved_idx + question_simillarity_based_retrieved_idx)
    print(f"\n\nDEBUG: Combined unique indices for final prediction: {combined_retrieved_indices}")

    final_retrieved_rules = get_llm_formatted_rules_string(list(combined_retrieved_indices))

    try:
        IST = pytz.timezone('Asia/Kolkata')
    except ImportError:
        IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

    current_time = datetime.now(IST)

    prediction = predict_user_query(
            db_record,
            current_time,
            final_retrieved_rules,
            initial_question
        )

    # My own logic for generating a prediction ends

    print(f"DEBUG: Final prediction generated: {prediction}")
    
    prediction_record = {
        "user_question": initial_question,
        "astrology_prediction": prediction,
        "time": datetime.now(IST).isoformat() 
    }
    
    db_record['predictions'] = [prediction_record] + db_record.get('predictions', [])
    save_database(mob)
    
    print(f"DEBUG: LLM Process complete. Returning final prediction.")
    # Step 4: Final Prediction Text return karo
    return prediction

# ==============================================================================
# STAGE 1: CONNECTION & ROUTING LOGIC
# ==============================================================================

async def handle_new_connection(websocket: WebSocket, mob: str):
    # (Yeh function waisa hi hai, bas thoda saaf kiya gaya hai)
    await websocket.accept()
    print(f"INFO: WebSocket connected for MOB: {mob}")

    if mob not in user_data_store:
        user_data_store[mob] = {
            "db_record": {"basic_data": {}, "on_demand_data": {}, "predictions": []},
            "session_state": { "details_request_pending": False, "pending_question": None,

            }
        }
    
    db_record = user_data_store[mob]["db_record"]
    if not all(db_record['basic_data'].get(f) for f in ["name", "date_of_birth", "time_of_birth", "place_of_birth"]):
        user_data_store[mob]['session_state']['details_request_pending'] = True
        await websocket.send_json({
            "type": "status_update", "status": "user_details_needed", "message": "Welcome! Please provide your details.",
            "action_needed_fields": [
                {"id": "name", "label": "Name", "required": True},
                {"id": "date_of_birth", "label": "Date of Birth (YYYY/MM/DD)", "required": True},
                {"id": "time_of_birth", "label": "Time of Birth (HH:MM)", "required": True},
                {"id": "place_of_birth", "label": "Place of Birth", "required": True}
            ]
        })
    else:
        user_data_store[mob]['session_state']['details_request_pending'] = False
        await websocket.send_json({"type": "status_update", "status": "ready_for_chat", "message": f"Welcome back, {db_record['basic_data'].get('name', 'friend')}!"})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, mob: str):
    """
    Yeh main endpoint ab bahut saaf hai. Yeh sirf setup aur routing karta hai.
    Core logic 'llm_process' ke andar hai.
    """
    # STAGE 1: Connection ko handle karo aur user ko pehchano.
    await handle_new_connection(websocket, mob)

    try:
        # STAGE 2: Ab client se aane wale messages ko suno aur sahi jagah bhejo.
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            user_session = user_data_store[mob]

            if msg_type == "chat_message":
                # Check karo ki kahin user details pending to nahi hain
                if user_session['session_state'].get('details_request_pending'):
                    # Sawaal ko save karke rakho aur user ko details bharne do
                    user_session['session_state']['pending_question'] = message.get("user_question")
                    print("DEBUG: Details pending. Storing question for later.")
                    continue
                
                # Agar sab theek hai, to core logic 'llm_process' ko call karo
                final_prediction = await llm_process(websocket, mob, message.get("user_question"))
                
                # 'llm_process' se mili prediction ko user ko bhejo
                await websocket.send_json({"type": "llm_response", "message": final_prediction, "display_message_in_chat": True})

            elif msg_type == "save_user_details":
                # User ki details save karo
                db_record = user_session["db_record"]
                db_record['basic_data'] = {
                    "name": message.get("name"), "date_of_birth": message.get("date_of_birth"),
                    "time_of_birth": message.get("time_of_birth"), "place_of_birth": message.get("place_of_birth")
                }
                # ... baki random data generate karo ...
                db_record['latitude'] = round(random.uniform(-90, 90), 4)
                db_record['longitude'] = round(random.uniform(-180, 180), 4)
                db_record['planets'] = {planet: random.randint(1, 12) for planet in PLANETS}
                save_database(mob)
                
                user_session['session_state']['details_request_pending'] = False
                await websocket.send_json({"type": "status_update", "status": "details_saved", "message": "Thank you! Your details are saved."})

                # Check karo ki kya koi sawaal pending tha
                pending_question = user_session['session_state'].get('pending_question')
                if pending_question:
                    print("DEBUG: Details saved. Processing pending question now.")
                    # Agar sawaal pending tha, to ab 'llm_process' ko call karo
                    final_prediction = await llm_process(websocket, mob, pending_question)
                    await websocket.send_json({"type": "llm_response", "message": final_prediction, "display_message_in_chat": True})
            
            elif msg_type == "submit_custom_input":
                # Is message ko ab 'get_next_user_response' function handle karta hai,
                # isliye yahaan par isko ignore karna safe hai.
                print("DEBUG: 'submit_custom_input' received by main loop, but handled by 'llm_process'. Ignoring.")
                pass

    except WebSocketDisconnect:
        print(f"INFO: WebSocket disconnected for MOB: {mob}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred for {mob}: {e}")
        if not websocket.client_state == 'DISCONNECTED':
            await websocket.send_json({"type": "error", "message": f"Server error: {e}"})