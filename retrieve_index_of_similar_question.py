import pandas as pd
import google.generativeai as genai
import os
import re # <--- ADDED THIS LINE

# Configure Gemini API (ensure GEMINI_API_KEY is set in your environment variables)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")

EXCEL_FILE = "Refined_Knowledge_Bank (1).xlsx"

def get_relevant_excel_indices(user_query: str) -> list[int]:
    """
    Queries a Gemini model to find the most relevant Excel row indices
    based on a user query and the 'Result' column of an Excel file.

    Args:
        user_query (str): The user's question or query.

    Returns:
        list[int]: A list of integer Excel row numbers (1-indexed)
                   that Gemini deems most relevant. Returns an empty list
                   if no numbers are found or an error occurs.
    """
    try:
        excel_df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        print(f"Error: Excel file not found at '{EXCEL_FILE}'.")
        return []
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return []

    # Prepare results block for LLM (using 1-based Excel indexing)
    hard_code_result_block = ""
    for idx, row in enumerate(excel_df.itertuples(index=False), start=2): # Start from 2 for Excel row numbers
        result = str(row.Result).strip()
        if result:
            hard_code_result_block += f"{idx}. {result}\n"

    # Properly formatted prompt for Gemini
    prompt = f"""
You are a highly accurate semantic match engine.

Given the following user query:
"{user_query}"

Here user question can be in Hindi or English or Hinglish or Devnagari, You need to find the most relevant lines from the following list of texts which is mainly in devanagari(Hindi).

And the following list of texts, prefixed with their line numbers:
{hard_code_result_block}

Return the most relevant line numbers (e.g., 2, 3, 47) that most closely match the user's question in meaning.
Only return a list of numbers comma separated. Do not return explanations.
"""
    # Optional: Print prompt for debugging
    # print("--- Gemini Prompt ---")
    # print(prompt)
    # print("---------------------")

    try:
        # Get Gemini response
        response = model.generate_content(prompt)
        gemini_text_response = response.text
        
        # Optional: Print Gemini's raw response
        # print("--- Gemini Raw Response ---")
        # print(gemini_text_response)
        # print("---------------------------")

        # Extract line numbers from Gemini's response
        # This regex handles comma-separated numbers, spaces, and potential newlines.
        matched_numbers_str = re.findall(r'\b\d+\b', gemini_text_response)
        
        matched_indexes = []
        for num_str in matched_numbers_str:
            try:
                idx = int(num_str)
                # Basic validation: ensure index is within reasonable Excel row bounds
                if 2 <= idx <= len(excel_df) + 1:
                    matched_indexes.append(idx)
            except ValueError:
                # Should not happen with \b\d+\b but good practice
                continue
        
        return matched_indexes

    except Exception as e:
        print(f"Error getting or processing Gemini response: {e}")
        return []

# Example Usage:
if __name__ == "__main__":
    user_question = "Meri love life kaisi rahegi?"
    
    print(f"User Question: {user_question}")
    
    # Call the function to get relevant indices
    relevant_indices = get_relevant_excel_indices(user_question)

    
    print(f"\nRelevant Excel Row Indices (from Gemini): {relevant_indices}")

    # You can then use these indices to fetch full rule details if needed
    if relevant_indices:
        try:
            excel_df_full = pd.read_excel(EXCEL_FILE)
            print("\n--- Details of Top Relevant Rule ---")
            # Get the first relevant rule's details
            first_relevant_idx = relevant_indices[0]
            # Convert 1-based Excel row index to 0-based DataFrame index
            df_row_idx = first_relevant_idx - 2 
            if 0 <= df_row_idx < len(excel_df_full):
                rule_condition = str(excel_df_full.iloc[df_row_idx]["Condition"]).strip()
                rule_result = str(excel_df_full.iloc[df_row_idx]["Result"]).strip()
                print(f"Excel Row: {first_relevant_idx}")
                print(f"  Condition: {rule_condition}")
                print(f"  Result: {rule_result}")
            else:
                print(f"Error: Invalid index {first_relevant_idx} after validation.")
        except Exception as e:
            print(f"Error fetching rule details from Excel: {e}")
    else:
        print("\nNo relevant rules found by Gemini.")