import pandas as pd
from datetime import datetime, timedelta
import re

EXCEL_FILE = "Refined_Knowledge_Bank (1).xlsx"

# Mapping from short planet names (as found in Excel 'Condition')
# to their full, more readable names.
SHORT_TO_FULL_PLANET_NAME_MAP = {
    "sun": "Sun",
    "moon": "Moon",
    "mars": "Mars",
    "mer": "Mercury",
    "jup": "Jupiter",
    "ven": "Venus",
    "sat": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu"
}

def calculate_dob_range_from_time_period(current_date: datetime, start_date_obj: datetime, end_date_obj: datetime) -> str:
    """
    Calculates the approximate Date of Birth range for a person for whom the
    given time period would be active, relative to the current date.
    """
    age_at_start_of_period = current_date.year - start_date_obj.year - ((current_date.month, current_date.day) < (start_date_obj.month, start_date_obj.day))
    age_at_end_of_period = current_date.year - end_date_obj.year - ((current_date.month, current_date.day) < (end_date_obj.month, end_date_obj.day))

    earliest_dob_year = current_date.year - max(age_at_start_of_period, age_at_end_of_period)
    latest_dob_year = current_date.year - min(age_at_start_of_period, age_at_end_of_period)

    start_dob_approx = datetime(earliest_dob_year, current_date.month, current_date.day)
    end_dob_approx = datetime(latest_dob_year, current_date.month, current_date.day)

    return f"{start_dob_approx.strftime('%Y-%m-%d')} to {end_dob_approx.strftime('%Y-%m-%d')}"


def transform_condition_to_dob_and_full_planets(original_condition_string: str) -> str:
    """
    Transforms the original condition string by:
    1. Converting 'TIME ((...))' to 'DOB (...)' ranges.
    2. Replacing short planet names with full names.
    3. Cleaning up 'Natal()' wrappers.
    4. General whitespace cleanup.
    """
    current_date = datetime.now() 

    modified_condition = original_condition_string

    # --- Step 1: Convert TIME to DOB ---
    time_pattern = re.compile(r'TIME\s*\(\((.*?)(?:\)\))?\s*$', re.IGNORECASE | re.DOTALL)
    match = time_pattern.search(modified_condition)

    if match:
        all_time_ranges_str = match.group(1).strip()
        individual_time_ranges = re.split(r'\)\s*,\s*\(|\)\s*\(|\)\s*,|\(', all_time_ranges_str)
        individual_time_ranges = [item.strip() for item in individual_time_ranges if item.strip()]

        converted_dob_ranges_list = []
        
        for tr_str in individual_time_ranges:
            clean_tr_str = tr_str.replace('(', '').replace(')', '').strip()
            parts = clean_tr_str.split(' to ')
            
            if len(parts) == 2:
                start_date_str = parts[0].strip()
                end_date_str = parts[1].strip()
                try:
                    start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
                    
                    if len(end_date_str) < 10: 
                        if end_date_str.strip() == "":
                            end_date_obj = current_date
                        else:
                            year_part_match = re.match(r'(\d{4})', end_date_str)
                            if year_part_match:
                                end_year = int(year_part_match.group(1))
                                end_date_obj = datetime(end_year, 12, 31)
                                if end_date_obj.year == current_date.year:
                                    end_date_obj = min(end_date_obj, current_date)
                            else:
                                raise ValueError(f"Could not parse end date: {end_date_str}")
                    else:
                        end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d")

                    dob_range_str = calculate_dob_range_from_time_period(current_date, start_date_obj, end_date_obj)
                    converted_dob_ranges_list.append(dob_range_str)

                except (ValueError, Exception): 
                    pass
            else:
                pass

        if converted_dob_ranges_list:
            new_dob_condition_content = ", ".join(converted_dob_ranges_list)
            new_dob_condition_str = f"DOB ({new_dob_condition_content})"
            modified_condition = time_pattern.sub(new_dob_condition_str, modified_condition, count=1)
    
    # --- Step 2: Expand short planet names to full names ---
    for short, full in SHORT_TO_FULL_PLANET_NAME_MAP.items():
        modified_condition = re.sub(r'\b' + re.escape(short) + r'\b', full, modified_condition, flags=re.IGNORECASE)

    # --- Step 3: Remove Natal() wrappers ---
    modified_condition = re.sub(r'Natal\s*\(([^)]+)\)', r'\1', modified_condition, flags=re.IGNORECASE)

    # --- Step 4: General whitespace and operator cleanup ---
    modified_condition = re.sub(r'\s+AND\s+', ' AND ', modified_condition, flags=re.IGNORECASE)
    modified_condition = re.sub(r'\s+OR\s+', ' OR ', modified_condition, flags=re.IGNORECASE)
    modified_condition = modified_condition.strip() 

    return modified_condition


def get_llm_formatted_rules_string(excel_rows_indices: list) -> str:
    """
    Processes specified Excel rows, applies the transformation to each,
    and consolidates the results into a single string formatted for an LLM.

    Args:
        excel_rows_indices (list): A list of Excel row numbers (1-indexed) to process.

    Returns:
        str: A single string containing all transformed Condition-Result pairs.
             Returns an empty string if no valid rows are processed.
    """
    excel_df = pd.read_excel(EXCEL_FILE)
    
    llm_output_parts = []

    for row_idx in excel_rows_indices:
        df_row_index = row_idx - 2 # Adjust for 0-indexed DataFrame

        if df_row_index < 0 or df_row_index >= len(excel_df):
            # Skip invalid row indices
            # print(f"Warning: Row {row_idx} is out of bounds and will be skipped.")
            continue

        original_condition = str(excel_df.iloc[df_row_index]['Condition'])
        result = str(excel_df.iloc[df_row_index]['Result'])
        
        # Apply the full transformation
        transformed_condition = transform_condition_to_dob_and_full_planets(original_condition)

        # Format for LLM input
        llm_output_parts.append(f"Condition: {transformed_condition}\nResult: {result}\n")
        
    return "\n".join(llm_output_parts).strip() # Join with newlines and remove any trailing whitespace


# Example Usage:
if __name__ == "__main__":
    # This list would typically come from your intent detection and initial filtering logic
    rows_to_format = [5, 11, 378] 
    
    print(f"Preparing LLM input for Excel rows: {rows_to_format}")

    llm_input_string = get_llm_formatted_rules_string(rows_to_format)

    print("\n--- LLM Input String ---")
    if llm_input_string:
        print(llm_input_string)
    else:
        print("No valid rules found to format for LLM input.")