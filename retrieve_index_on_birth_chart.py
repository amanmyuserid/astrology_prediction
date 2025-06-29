import pandas as pd
from datetime import datetime
import re
import random

EXCEL_FILE = "Refined_Knowledge_Bank (1).xlsx"

# Mapping from full planet names (as expected in user_planet_positions)
# to their short forms used in the Excel sheet's 'Condition' column.
PLANET_NAME_MAP = {
    "Sun": "sun",
    "Moon": "moon",
    "Mars": "mars",
    "Mercury": "mer",
    "Jupiter": "jup",
    "Venus": "ven",
    "Saturn": "sat",
    "Rahu": "rahu",
    "Ketu": "ketu"
}

def calculate_age(dob_str: str) -> int:
    """Calculates age based on DOB string and current IST date."""
    today = datetime.now()
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

def get_matching_rules_by_planet_age_time(user_dob: str, user_planet_positions: dict) -> list:
    """
    Finds Excel rows where the 'Condition' matches a randomly selected
    user planet's natal house position, along with age and time period.

    Args:
        user_dob (str): The user's Date of Birth in "YYYY-MM-DD" format.
        user_planet_positions (dict): A dictionary of user's natal planet positions
                                      e.g., {"Sun": 7, "Moon": 7, ...}.

    Returns:
        list: A list of integer Excel row numbers (indices) that match the criteria.
              Returns an empty list if no matches.
    """
    excel_df = pd.read_excel(EXCEL_FILE)
    current_age = calculate_age(user_dob)
    current_date = datetime.now() 

    # --- CRITICAL CHANGE: Initialize as a list of integers ---
    matched_excel_indices = [] 

    if not user_planet_positions:
        print("Error: user_planet_positions dictionary is empty. Cannot select a random planet.")
        return []

    # Pick one random planet and its house from the user's data
    # Ensure the randomly picked planet has a mapping to its short form.
    # We iterate until a mappable planet is found or exhaust all options.
    mapped_random_planet_name = None
    random_planet_house = None
    
    shuffled_planets = list(user_planet_positions.keys())
    random.shuffle(shuffled_planets) # Shuffle to ensure true randomness

    for planet_full_name in shuffled_planets:
        if planet_full_name in PLANET_NAME_MAP:
            mapped_random_planet_name = PLANET_NAME_MAP[planet_full_name]
            random_planet_house = user_planet_positions[planet_full_name]
            break
    
    if mapped_random_planet_name is None:
        print("Error: No mappable planets found in user_planet_positions. Please ensure keys match PLANET_NAME_MAP.")
        return []

    print(f"Debug: Randomly selected planet for matching: {mapped_random_planet_name.capitalize()} (full: {planet_full_name}) in house {random_planet_house}")

    for idx, row in enumerate(excel_df.itertuples(index=False), start=2):
        condition = str(row.Condition).lower()
        
        # --- Condition 1: Natal Planet Position Matching ---
        natal_match = False 
        
        # 1.1 Check for specific "random_planet in its_house" match
        # Using \b for word boundaries to ensure 'sat' doesn't match 'saturday'
        # and checking for 'in' followed by the exact house number.
        natal_planet_in_house_pattern = re.compile(
            rf'\b{mapped_random_planet_name}\s+in\s+{random_planet_house}\b'
        )
        
        if natal_planet_in_house_pattern.search(condition):
            natal_match = True
        
        # 1.2 Check for "random_planet conjunct other_planet" or "other_planet conjunct random_planet"
        # and verify their positions
        conjunct_pattern = re.compile(
            rf'\b({mapped_random_planet_name})\s+conjunct\s+([a-z]+)\b|\b([a-z]+)\s+conjunct\s+({mapped_random_planet_name})\b'
        )
        
        conjunct_matches = conjunct_pattern.findall(condition)
        for match_group in conjunct_matches:
            # findall returns tuples, determine which group is the "other planet"
            matched_planet_short_name_in_rule = ''
            if match_group[0] == mapped_random_planet_name: # random planet is first
                matched_planet_short_name_in_rule = match_group[1]
            elif match_group[3] == mapped_random_planet_name: # random planet is second
                matched_planet_short_name_in_rule = match_group[2]

            # Find the full name for the "other_planet" from the map (reverse lookup)
            other_planet_full_name = None
            for full_name, short_name in PLANET_NAME_MAP.items():
                if short_name == matched_planet_short_name_in_rule:
                    other_planet_full_name = full_name
                    break

            if (other_planet_full_name and # ensure we found a valid other planet
                planet_full_name in user_planet_positions and # ensure random planet is in user data
                other_planet_full_name in user_planet_positions and # ensure other planet is in user data
                user_planet_positions[planet_full_name] == user_planet_positions[other_planet_full_name]): # positions match
                natal_match = True
                break # If one conjunction involving the random planet matches, this part is met
            
        # 1.3 Check for "random_planet not-with other_planet"
        not_with_pattern = re.compile(
            rf'\b({mapped_random_planet_name})\s+not-with\s+([a-z]+)\b|\b([a-z]+)\s+not-with\s+({mapped_random_planet_name})\b'
        )

        not_with_matches = not_with_pattern.findall(condition)
        for match_group in not_with_matches:
            matched_planet_short_name_in_rule = ''
            if match_group[0] == mapped_random_planet_name:
                matched_planet_short_name_in_rule = match_group[1]
            elif match_group[3] == mapped_random_planet_name:
                matched_planet_short_name_in_rule = match_group[2]

            other_planet_full_name = None
            for full_name, short_name in PLANET_NAME_MAP.items():
                if short_name == matched_planet_short_name_in_rule:
                    other_planet_full_name = full_name
                    break
            
            if (other_planet_full_name and
                planet_full_name in user_planet_positions and
                other_planet_full_name in user_planet_positions and
                user_planet_positions[planet_full_name] != user_planet_positions[other_planet_full_name]):
                natal_match = True # This specific 'not-with' condition is met
                break

        if not natal_match:
            continue 
            
        # --- Condition 2: Age Matching ---
        age_condition_met = True
        age_pattern = re.search(r'age\s*\(([^)]+)\)', condition)
        if age_pattern:
            ages_in_rule = [int(a.strip()) for a in age_pattern.group(1).split('/')]
            if current_age not in ages_in_rule:
                age_condition_met = False
        
        if not age_condition_met:
            continue

        # --- Condition 3: Time Period (Dasha) Matching ---
        time_condition_met = True
        time_pattern = re.search(r'time\s*\(\(([^)]+)\)\)', condition)
        if time_pattern:
            time_ranges_str = time_pattern.group(1).split('), (')
            
            any_time_range_matches = False
            for tr_str in time_ranges_str:
                try:
                    start_date_str, end_date_str = tr_str.replace('(', '').replace(')', '').split(' to ')
                    start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
                    if start_date <= current_date <= end_date:
                        any_time_range_matches = True
                        break
                except ValueError:
                    continue 
            if not any_time_range_matches:
                time_condition_met = False
        
        if not time_condition_met:
            continue

        # If all three conditions are met for this rule
        # --- CRITICAL CHANGE: Append only the index ---
        matched_excel_indices.append(idx) 
            
    return matched_excel_indices

# Example Usage:
if __name__ == "__main__":
    user_dob_input = "1990-05-15" # Example DOB (YYYY-MM-DD)
    
    # User's actual natal chart planet positions (using full names as keys)
    user_birth_chart_data = {
        "Sun": 7,
        "Moon": 7,
        "Mars": 10,
        "Mercury": 12, # Mercury in 12
        "Jupiter": 10,
        "Venus": 7,
        "Saturn": 11, # Saturn in 11
        "Rahu": 6,
        "Ketu": 6
    }
    
    print(f"User DOB: {user_dob_input} (Calculated Age: {calculate_age(user_dob_input)} years)")
    print(f"User Birth Chart Data: {user_birth_chart_data}")

    matched_rules_indices = get_matching_rules_by_planet_age_time(user_dob_input, user_birth_chart_data)

    print("matched rules indices:", matched_rules_indices)
    
    print(f"\n--- Matched Rule Indices ({len(matched_rules_indices)} found) ---")
    if matched_rules_indices:
        print(matched_rules_indices)
    else:
        print("No rules matched the specified criteria (random planet position + age + time).")