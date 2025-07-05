# D&D 5e Combat Engine and Tools

This project provides a comprehensive set of tools for Dungeons & Dragons 5th Edition (D&D 5e), including a combat engine to manage game state and resolve mechanics, as well as utilities for generating characters, spells, and items using the Venice AI API, and validating game data.

## Table of Contents
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [File Structure](#file-structure)
- [Output Format](#output-format)

## Installation

To use the tools in this project, ensure you have Python 3 installed on your system along with the required libraries:

```bash
pip install requests python-dotenv jsonschema rich
```

## Setup

1. **API Key Configuration**:
   - Create a `.env` file in the project directory with the following content:
     ```
     VENICE_API_KEY=your_api_key_here
     ```
   - Replace `your_api_key_here` with your actual Venice AI API key. This key is used to authenticate requests to the Venice AI API endpoint (`https://api.venice.ai/api/v1/chat/completions`).

2. **Template Specification**:
   - Ensure the `gs_template.md` file is present in the project directory. This file contains the specification for the character data structure that the LLM uses to format the output.

## Usage

1. **Running Combat Engine**: Execute `combat_engine.py` to simulate combat scenarios based on data in `game_state.json`.
   ```bash
   python3 combat_engine.py
   ```

2. **Generating Characters**: Use `character_generator.py` to create new characters with AI assistance.
   ```bash
   python3 character_generator.py
   ```
   - You will be prompted to enter a character name and a description (e.g., "a brave elven wizard skilled in fire magic").
   - The script will generate a character sheet and a lore sheet, saving them to the `/players` folder as `character_<name>.json` and `lore_<name>.txt` respectively.
   - Type `exit` at any prompt to quit the program.

3. **Generating Spells and Items**: Use `spell_empora.py` in the `tools` folder to create new spells and items with AI assistance.
   ```bash
   python3 tools/spell_empora.py
   ```

4. **Validating Game State**: Use `refine.py` in the `tools` folder to validate `game_state.json` against `gs_schema.json`.
   ```bash
   python3 tools/refine.py
   ```

## How It Works

### Combat Engine (`combat_engine.py`)
- Manages D&D 5e combat mechanics, including initiative, turn management, action resolution, spell effects, and conditions based on data in `game_state.json`.

### Character Generator (`character_generator.py`)
1. **Environment Setup**: Loads the Venice AI API key from the `.env` file using the `python-dotenv` library to authenticate API requests.
2. **Template Loading**: Reads the character data structure specification from `gs_template.md` as a text file, which is included in the API prompt to guide the LLM's output format.
3. **Character Generation**:
   - Prompts the user for a character name and description.
   - Sends a request to the Venice AI API (`llama-3.3-70b` model) with a system prompt and user prompt that includes the template specification and instructions to ensure base values for spells and attacks are compliant with the d20 library (e.g., '1d8', '2d6+3').
   - Cleans the response to remove markdown formatting (like ```json) and parses it as JSON.
   - Extracts the character data from the `players` array in the response.
4. **Lore Sheet Generation**:
   - Sends a second API request to generate a basic lore sheet (backstory and personality traits) for the character using the same name and description.
5. **Saving Output**:
   - Saves the character data to `/players/character_<name>.json`.
   - Saves the lore sheet to `/players/lore_<name>.txt`.
- The script handles errors such as invalid JSON responses, API failures, and missing template files, providing appropriate feedback to the user.

### Spell and Item Generator (`tools/spell_empora.py`)
- Uses the Venice AI API to generate detailed spells and items, enhancing game content with magical effects and equipment data structured according to `gs_schema.json`.

### Game State Validator (`tools/refine.py`)
- Validates `game_state.json` against `gs_schema.json` using the `jsonschema` library, reporting any discrepancies to ensure data consistency. Enhanced with `rich` for detailed error output.

## File Structure

- `.env`: Contains the Venice AI API key for authentication.
- `gs_template.md`: Specification for the character data structure used in the API prompt.
- `combat_engine.py`: Core script for managing D&D 5e combat mechanics.
- `character_generator.py`: Script for generating characters and lore sheets.
- `game_state.json`: JSON file storing the current state of the game, including player and NPC data.
- `gs_schema.json`: JSON Schema file defining the structure and validation rules for `game_state.json`.
- `/players/`: Directory where generated character JSON files and lore text files are saved.
- `tools/spell_empora.py`: Script for generating spells and items.
- `tools/refine.py`: Script for validating game state data against the schema.
- `documentation/gs_schema_documentation.md`: Detailed documentation on the schema, addressing limitations and intended logic not captured in JSON.

## Output Format

- **Character Sheet (`character_<name>.json`)**: A JSON file containing detailed character stats, inventory, spells, and conditions, structured as per the specification in `gs_template.md`.
- **Lore Sheet (`lore_<name>.txt`)**: A plain text file with a short backstory (2-3 sentences) and personality traits (2-3 bullet points) for the character.
- Example character filename: `players/character_Jarvis.json`
- Example lore filename: `players/lore_Jarvis.txt`