import requests
import json
import os
import re
from dotenv import load_dotenv
from rich.traceback import install

# Initialize rich traceback handler
install()

# Load environment variables for API key
load_dotenv()
VENICE_API_KEY = os.getenv("VENICE_API_KEY")

def load_game_state_template():
    """Load the game state template specification from gs_template.md"""
    try:
        with open('gs_template.md', 'r') as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Failed to load game state template from gs_template.md: {str(e)}")

def generate_character(name, description):
    """Generate a character using Venice AI API based on user description"""
    url = "https://api.venice.ai/api/v1/chat/completions"
    template_spec = load_game_state_template()
    
    system_prompt = "You are an AI assistant tasked with generating D&D 5e characters. Always return strictly formatted JSON objects with no additional text."
    user_prompt = (
        f"Generate a D&D 5e character named '{name}' based on the following description: '{description}'. "
        f"Format the output strictly as a JSON object matching the structure defined in this specification:\n\n{template_spec}\n\n"
        "Ensure that all spells and attacks have base values for damage, healing, or effects compliant with the d20 library for dice rolling (e.g., '1d8', '2d6+3'). "
        "Do not leave any values empty; refer to D&D 5e standards and examples in the specification for appropriate values. "
        "Return ONLY the JSON object with no additional text, explanations, or formatting outside the JSON."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "model": "llama-3.3-70b",
        "temperature": 0.7,
        "venice_parameters": {
            "enable_web_search": "auto"
        },
        "parallel_tool_calls": True
    }
    headers = {
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "choices" in data and data["choices"]:
            content = data["choices"][0]["message"]["content"]
            # Clean the response by removing markdown code block markers
            content = re.sub(r'```json|```', '', content).strip()
            try:
                response_data = json.loads(content)
                # Extract the first character from the 'players' array if it exists
                if "players" in response_data and response_data["players"]:
                    character_data = response_data["players"][0]
                    # Validate the character data against the schema
                    validation_result, character_data = validate_and_refine_character_data(character_data)
                    if validation_result:
                        return character_data
                    else:
                        print("Error: Generated character data could not be refined to conform to the schema. Returning unrefined data.")
                        return character_data
                else:
                    print("Error: Response does not contain a 'players' array with character data.")
                    return None
            except json.JSONDecodeError:
                print("Error: Response is not valid JSON. Raw response:")
                print(content)
                return None
        else:
            print("No valid choices in API response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}. Response: {getattr(e.response, 'text', 'No response')}")
        print("Dark forces have prevented the character generation from succeeding. Please try again.")
        return None

def generate_lore_sheet(name, description):
    """Generate a lore sheet for the character using Venice AI API"""
    url = "https://api.venice.ai/api/v1/chat/completions"
    
    system_prompt = "You are an AI assistant tasked with generating lore sheets for D&D 5e characters. Return a concise backstory and personality description."
    user_prompt = (
        f"Generate a basic lore sheet for a D&D 5e character named '{name}' with the following description: '{description}'. "
        "Include a short backstory (2-3 sentences) and personality traits (2-3 bullet points). "
        "Return the response in plain text format."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "model": "llama-3.3-70b",
        "temperature": 0.7,
        "venice_parameters": {
            "enable_web_search": "auto"
        },
        "parallel_tool_calls": True
    }
    headers = {
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "choices" in data and data["choices"]:
            content = data["choices"][0]["message"]["content"]
            return content
        else:
            print("No valid choices in lore sheet API response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API Error for lore sheet: {e}. Response: {getattr(e.response, 'text', 'No response')}")
        print("Dark forces have prevented the lore sheet generation from succeeding. Please try again.")
        return None

def save_character(character_data):
    """Save the generated character to a JSON file in the /players folder"""
    if character_data and 'name' in character_data:
        # Validate before saving
        if validate_and_refine_character_data(character_data)[0]:
            # Create players directory if it doesn't exist
            os.makedirs('players', exist_ok=True)
            filename = f"players/character_{character_data['name'].replace(' ', '_')}.json"
            with open(filename, 'w') as file:
                json.dump(character_data, file, indent=2)
            print(f"Character saved to {filename}")
            return filename
        else:
            print("Warning: Character data does not conform to schema. Saving anyway for reference.")
            os.makedirs('players', exist_ok=True)
            filename = f"players/character_{character_data['name'].replace(' ', '_')}_unvalidated.json"
            with open(filename, 'w') as file:
                json.dump(character_data, file, indent=2)
            print(f"Character saved to {filename} with unvalidated suffix.")
            return filename
    else:
        print("No valid character data to save.")
        return None

def save_lore_sheet(name, lore_content):
    """Save the generated lore sheet to a text file in the /players folder"""
    if lore_content:
        # Create players directory if it doesn't exist
        os.makedirs('players', exist_ok=True)
        filename = f"players/lore_{name.replace(' ', '_')}.txt"
        with open(filename, 'w') as file:
            file.write(lore_content)
        print(f"Lore sheet saved to {filename}")
        return filename
    else:
        print("No valid lore data to save.")
        return None

def validate_and_refine_character_data(character_data, max_retries=2):
    """Validate the generated character data against the game state schema and refine if necessary."""
    import json
    import jsonschema
    from jsonschema import ValidationError
    
    try:
        # Load the schema
        with open("gs_schema.json", 'r') as schema_file:
            schema = json.load(schema_file)
        
        # Wrap the character data in a 'players' array to match the schema structure
        wrapped_data = {"players": [character_data], "npcs": []}
        
        # Validate against the schema
        jsonschema.validate(instance=wrapped_data, schema=schema)
        print("Character data validated successfully against schema.")
        return True, character_data
    except ValidationError as e:
        print(f"Validation error in character data: {str(e)}")
        print("Attempting to refine character data using LLM...")
        refined_data = refine_data_with_llm(character_data, schema, "character", max_retries)
        if refined_data:
            try:
                wrapped_refined_data = {"players": [refined_data], "npcs": []}
                jsonschema.validate(instance=wrapped_refined_data, schema=schema)
                print("Refined character data validated successfully against schema.")
                return True, refined_data
            except ValidationError as re:
                print(f"Refinement failed to conform to schema: {str(re)}")
                return False, refined_data
        else:
            print("Refinement process failed. Returning original data.")
            return False, character_data
    except Exception as e:
        print(f"[bold red]Error during validation: {str(e)}[/bold red]")
        print("[bold red]Dark forces have prevented validation. Returning original data.[/bold red]")
        return False, character_data

def refine_data_with_llm(data, schema, data_type, max_retries=2):
    """Use the Venice AI API to refine data that doesn't conform to the schema."""
    import datetime
    url = "https://api.venice.ai/api/v1/chat/completions"
    system_prompt = "You are an AI assistant tasked with refining D&D 5e data to fit a specific JSON schema. Return only the corrected JSON object with no additional text."
    user_prompt = (
        f"Refine the following {data_type} data to conform to the provided JSON schema. "
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Non-conforming data:\n{json.dumps(data, indent=2)}\n\n"
        "Fill in missing fields with appropriate D&D 5e values, remove invalid fields, and adjust existing fields to match the schema. "
        "Return ONLY the corrected JSON object with no additional text or formatting."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "model": "llama-3.3-70b",
        "temperature": 0.5,
        "venice_parameters": {
            "enable_web_search": "auto"
        },
        "parallel_tool_calls": True
    }
    headers = {
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Create log directory
    os.makedirs('refine-llm-logs', exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            # Log the input payload
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            input_log_filename = f"refine-llm-logs/input_character_{timestamp}_attempt_{attempt+1}.json"
            with open(input_log_filename, 'w') as input_file:
                json.dump(payload, input_file, indent=2)
            print(f"Logged LLM input to {input_log_filename}")
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            # Log the output response
            output_log_filename = f"refine-llm-logs/output_character_{timestamp}_attempt_{attempt+1}.json"
            with open(output_log_filename, 'w') as output_file:
                json.dump(response_data, output_file, indent=2)
            print(f"Logged LLM output to {output_log_filename}")
            
            if "choices" in response_data and response_data["choices"]:
                content = response_data["choices"][0]["message"]["content"]
                content = re.sub(r'```json|```', '', content).strip()
                try:
                    refined_data = json.loads(content)
                    print(f"Refinement attempt {attempt + 1}/{max_retries} successful.")
                    if data_type == "character" and "players" in refined_data and refined_data["players"]:
                        return refined_data["players"][0]
                    elif data_type in ["spell", "item", "weapon"] and (data_type + "s" in refined_data or "inventory" in refined_data):
                        return refined_data.get(data_type + "s", refined_data.get("inventory", [{}]))[0] if refined_data.get(data_type + "s", refined_data.get("inventory", [])) else None
                    return refined_data
                except json.JSONDecodeError:
                    print(f"[bold red]Refinement attempt {attempt + 1}/{max_retries} failed: Response is not valid JSON.[/bold red]")
                    if attempt == max_retries - 1:
                        print("[bold red]Max retries reached. Dark forces have prevented data refinement.[/bold red]")
                        return None
            else:
                print(f"[bold red]Refinement attempt {attempt + 1}/{max_retries} failed: No valid choices in API response.[/bold red]")
                if attempt == max_retries - 1:
                    print("[bold red]Max retries reached. Dark forces have prevented data refinement.[/bold red]")
                    return None
        except requests.exceptions.RequestException as e:
            print(f"[bold red]API Error during refinement attempt {attempt + 1}/{max_retries}: {e}[/bold red]")
            if attempt == max_retries - 1:
                print("[bold red]Max retries reached. Dark forces have prevented data refinement.[/bold red]")
                return None
    return None

def main():
    """Main loop for command-line character generation"""
    print("Welcome to the D&D 5e Character Generator!")
    print("Type 'exit' at any time to quit.")
    
    try:
        load_game_state_template()  # Test loading template at startup
    except Exception as e:
        print(f"Error: {e}")
        print("The script cannot continue without a valid game state template. Please ensure gs_template.md is present.")
        return
    
    while True:
        name = input("\nEnter the name for your character: ")
        if name.lower() == 'exit':
            print("Goodbye!")
            break
        
        if not name.strip():
            print("Name cannot be empty. Please try again.")
            continue
        
        description = input("Enter a description for your character (e.g., 'a brave elven wizard skilled in fire magic'): ")
        if description.lower() == 'exit':
            print("Goodbye!")
            break
        
        if description.strip():
            print("Generating character, please wait...")
            character = generate_character(name, description)
            if character:
                print("\nGenerated Character:")
                print(json.dumps(character, indent=2))
                save_character(character)
                
                print("Generating lore sheet, please wait...")
                lore = generate_lore_sheet(name, description)
                if lore:
                    print("\nGenerated Lore Sheet:")
                    print(lore)
                    save_lore_sheet(name, lore)
                else:
                    print("Failed to generate lore sheet.")
            else:
                print("Failed to generate character. Please try again.")
        else:
            print("Description cannot be empty. Please try again.")

if __name__ == "__main__":
    main()