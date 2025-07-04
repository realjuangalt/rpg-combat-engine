# D&D 5e Character Generator

This project provides a command-line tool for generating D&D 5e characters using the Venice AI API. The tool allows users to input a character name and description, and it generates a detailed character sheet and lore sheet based on the provided input.

## Table of Contents
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [File Structure](#file-structure)
- [Output Format](#output-format)

## Installation

To use the character generator, ensure you have Python 3 installed on your system along with the required libraries:

```bash
pip install requests python-dotenv
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

Run the character generator script from the command line:

```bash
python character_generator.py
```

- You will be prompted to enter a character name and a description (e.g., "a brave elven wizard skilled in fire magic").
- The script will generate a character sheet and a lore sheet based on the input, saving them to the `/players` folder as `character_<name>.json` and `lore_<name>.txt` respectively.
- Type `exit` at any prompt to quit the program.

## How It Works

The `character_generator.py` script operates as follows:

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

The script handles errors such as invalid JSON responses, API failures, and missing template files, providing appropriate feedback to the user.

## File Structure

- `.env`: Contains the Venice AI API key for authentication.
- `gs_template.md`: Specification for the character data structure used in the API prompt.
- `character_generator.py`: Main script for generating characters and lore sheets.
- `/players/`: Directory where generated character JSON files and lore text files are saved.

## Output Format

- **Character Sheet (`character_<name>.json`)**: A JSON file containing detailed character stats, inventory, spells, and conditions, structured as per the specification in `gs_template.md`.
- **Lore Sheet (`lore_<name>.txt`)**: A plain text file with a short backstory (2-3 sentences) and personality traits (2-3 bullet points) for the character.

Example character filename: `players/character_Jarvis.json`
Example lore filename: `players/lore_Jarvis.txt`