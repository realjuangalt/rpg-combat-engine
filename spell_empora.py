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

def generate_item(item_type, description):
    """Generate a spell, weapon, or item using Venice AI API based on user description"""
    url = "https://api.venice.ai/api/v1/chat/completions"
    full_template = load_game_state_template()
    
    # Extract only the relevant section of the template for spells or inventory
    if item_type.lower() == "spell":
        template_spec = extract_template_section(full_template, "spells")
    else:  # weapon or item
        template_spec = extract_template_section(full_template, "inventory")
    
    system_prompt = "You are an AI assistant tasked with generating D&D 5e spells, weapons, or items. Always return strictly formatted JSON objects with no additional text."
    user_prompt = (
        f"Generate a D&D 5e {item_type} based on the following description: '{description}'. "
        "If a specific name is provided in the description, use it; otherwise, create an appropriate name for the item. "
        f"Format the output strictly as a JSON object matching the structure defined in this specification for a single {item_type}:\n\n{template_spec}\n\n"
        "Ensure that all spells and attacks have base values for damage, healing, or effects compliant with the d20 library for dice rolling (e.g., '1d8', '2d6+3'). "
        "Do not leave any values empty; refer to D&D 5e standards and examples in the specification for appropriate values. "
        "Return ONLY the JSON object with no additional text, explanations, or formatting outside the JSON. "
        "Do not include any character or player data; focus solely on the requested item."
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
            print("DEBUG: Raw API response content (after cleaning):")
            print(content)
            try:
                response_data = json.loads(content)
                print(f"DEBUG: Parsed JSON response keys: {list(response_data.keys())}")
                # Extract the relevant item data based on item_type
                if item_type.lower() == "spell":
                    if "spells" in response_data and response_data["spells"]:
                        item_data = response_data["spells"][0]
                    elif isinstance(response_data, dict) and "name" in response_data and response_data.get("type") in ["damage", "healing", "buff", "utility"]:
                        item_data = response_data
                    else:
                        print(f"Error: Response does not contain a relevant array or direct object for {item_type} data.")
                        print(f"DEBUG: Full JSON response structure: {json.dumps(response_data, indent=2)[:1000]}... (truncated if too long)")
                        return None
                else:  # weapon or item
                    if "inventory" in response_data and response_data["inventory"]:
                        item_data = response_data["inventory"][0]
                    elif isinstance(response_data, dict) and "name" in response_data and response_data.get("type") in ["melee", "ranged", "magic"]:
                        item_data = response_data
                    else:
                        print(f"Error: Response does not contain a relevant array or direct object for {item_type} data.")
                        print(f"DEBUG: Full JSON response structure: {json.dumps(response_data, indent=2)[:1000]}... (truncated if too long)")
                        return None
                # Validate and refine the item data against the schema
                validation_result, refined_item_data = validate_and_refine_item_data(item_data, item_type)
                if validation_result:
                    return refined_item_data
                else:
                    print(f"Error: Generated {item_type} data could not be refined to conform to the schema. Returning unrefined data.")
                    return refined_item_data
            except json.JSONDecodeError:
                print("Error: Response is not valid JSON. Raw response:")
                print(content)
                return None
        else:
            print("No valid choices in API response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}. Response: {getattr(e.response, 'text', 'No response')}")
        print(f"Dark forces have prevented the {item_type} generation from succeeding. Please try again.")
        return None

def save_item(item_data, item_type):
    """Save the generated item to a JSON file in the /items folder"""
    if item_data and 'name' in item_data:
        # Validate before saving
        validation_result, refined_data = validate_and_refine_item_data(item_data, item_type)
        if validation_result:
            # Create items directory if it doesn't exist
            os.makedirs('items', exist_ok=True)
            filename = f"items/{item_type.lower()}_{refined_data['name'].replace(' ', '_')}.json"
            with open(filename, 'w') as file:
                json.dump(refined_data, file, indent=2)
            print(f"{item_type} saved to {filename}")
            return filename
        else:
            print(f"Warning: {item_type} data does not conform to schema. Saving anyway for reference.")
            os.makedirs('items', exist_ok=True)
            filename = f"items/{item_type.lower()}_{item_data['name'].replace(' ', '_')}_unvalidated.json"
            with open(filename, 'w') as file:
                json.dump(item_data, file, indent=2)
            print(f"{item_type} saved to {filename} with unvalidated suffix.")
            return filename
    else:
        print("No valid item data to save.")
        return None

def extract_template_section(full_template, section_name):
    """Extract the JSON section for spells or inventory from the full template"""
    import re
    if section_name == "spells":
        match = re.search(r'"spells":\s*\[([\s\S]*?)\]', full_template)
    else:  # inventory
        match = re.search(r'"inventory":\s*\[([\s\S]*?)\]', full_template)
    
    if match:
        section_content = match.group(1).strip()
        # Return a single object template by removing the array brackets and extra entries
        section_content = section_content.split('},')[0] + '}'
        return section_content
    else:
        print(f"Warning: Could not extract {section_name} section from template. Using full template.")
        return full_template

def main():
    """Main loop for command-line spell, weapon, or item generation"""
    print("Welcome to the D&D 5e Spell, Weapon, and Item Generator!")
    print("Type 'exit' at any time to quit.")
    
    try:
        load_game_state_template()  # Test loading template at startup
    except Exception as e:
        print(f"Error: {e}")
        print("The script cannot continue without a valid game state template. Please ensure gs_template.md is present.")
        return
    
    while True:
        item_type = input("\nEnter the type of item to generate (spell, weapon, or item): ")
        if item_type.lower() == 'exit':
            print("Goodbye!")
            break
        
        if item_type.lower() not in ['spell', 'weapon', 'item']:
            print("Invalid type. Please enter 'spell', 'weapon', or 'item'.")
            continue
        
        description = input(f"Enter a description for your {item_type} (e.g., 'a fiery sword that burns enemies', include name if desired): ")
        if description.lower() == 'exit':
            print("Goodbye!")
            break
        
        if description.strip():
            print(f"Generating {item_type}, please wait...")
            item = generate_item(item_type, description)
            if item:
                print(f"\nGenerated {item_type}:")
                print(json.dumps(item, indent=2))
                save_item(item, item_type)
            else:
                print(f"Failed to generate {item_type}. Please try again.")
        else:
            print("Description cannot be empty. Please try again.")

def validate_and_refine_item_data(item_data, item_type, max_retries=2):
    """Validate the generated item data against the game state schema and refine if necessary."""
    import json
    import jsonschema
    from jsonschema import ValidationError
    
    try:
        # Load the schema
        with open("gs_schema.json", 'r') as schema_file:
            schema = json.load(schema_file)
        
        # Wrap the item data in the appropriate structure to match the schema
        if item_type.lower() == "spell":
            wrapped_data = {"players": [{"name": "temp", "hp": 1, "ac": 10, "strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 10, "charisma": 10, "class_type": "wizard", "spells": [item_data], "inventory": [], "conditions": {}}], "npcs": []}
        else:  # weapon or item
            wrapped_data = {"players": [{"name": "temp", "hp": 1, "ac": 10, "strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 10, "charisma": 10, "class_type": "fighter", "inventory": [item_data], "spells": [], "conditions": {}}], "npcs": []}
        
        # Validate against the schema
        jsonschema.validate(instance=wrapped_data, schema=schema)
        print(f"{item_type} data validated successfully against schema.")
        return True, item_data
    except ValidationError as e:
        print(f"Validation error in {item_type} data: {str(e)}")
        print(f"Attempting to refine {item_type} data using LLM...")
        refined_data = refine_data_with_llm(item_data, schema, item_type.lower(), max_retries)
        if refined_data:
            try:
                if item_type.lower() == "spell":
                    wrapped_refined_data = {"players": [{"name": "temp", "hp": 1, "ac": 10, "strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 10, "charisma": 10, "class_type": "wizard", "spells": [refined_data], "inventory": [], "conditions": {}}], "npcs": []}
                else:
                    wrapped_refined_data = {"players": [{"name": "temp", "hp": 1, "ac": 10, "strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 10, "charisma": 10, "class_type": "fighter", "inventory": [refined_data], "spells": [], "conditions": {}}], "npcs": []}
                jsonschema.validate(instance=wrapped_refined_data, schema=schema)
                print(f"Refined {item_type} data validated successfully against schema.")
                return True, refined_data
            except ValidationError as re:
                print(f"Refinement failed to conform to schema: {str(re)}")
                return False, refined_data
        else:
            print(f"Refinement process failed for {item_type}. Returning original data.")
            return False, item_data
    except Exception as e:
        print(f"[bold red]Error during validation: {str(e)}[/bold red]")
        print(f"[bold red]Dark forces have prevented {item_type} validation. Returning original data.[/bold red]")
        return False, item_data

def refine_data_with_llm(data, schema, data_type, max_retries=2):
    """Use the Venice AI API to refine data that doesn't conform to the schema."""
    import requests
    import json
    import re
    import os
    import datetime
    from dotenv import load_dotenv
    
    # Load environment variables for API key
    load_dotenv()
    VENICE_API_KEY = os.getenv("VENICE_API_KEY")
    
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
            input_log_filename = f"refine-llm-logs/input_{data_type}_{timestamp}_attempt_{attempt+1}.json"
            with open(input_log_filename, 'w') as input_file:
                json.dump(payload, input_file, indent=2)
            print(f"Logged LLM input to {input_log_filename}")
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            # Log the output response
            output_log_filename = f"refine-llm-logs/output_{data_type}_{timestamp}_attempt_{attempt+1}.json"
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

if __name__ == "__main__":
    main()