character data on game_state.json file
# RPG Combat Engine
## Overview
This project is an RPG combat engine designed to simulate combat encounters in a Dungeons & Dragons 5th Edition (5e) style game. The engine handles various aspects of combat, including initiative rolls, action resolution, condition management, and logging.

## Features
* **Initiative Rolls**: Determines the order of actions in combat.
* **Action Resolution**: Handles attacks, spell casting, and other actions.
* **Condition Management**: Applies and tracks conditions like "stunned" or "poisoned".
* **Effect Management**: Applies and tracks effects like buffs and debuffs.
* **Logging**: Uses the rich library for detailed logging and console output.

## Project Structure

## Getting Started
### Prerequisites
* Python 3.7+
* rich library for enhanced console output and logging
* d20 library for dice rolling

### Installation
1. Clone the repository:
2. Install the required libraries:

### Usage
1. Prepare your game state in `game_state.json`:
2. Run the combat engine:

## Configuration
* **Conditions**: Define conditions in `conditions_apply.json`:
* **Class Data**: Define class-specific data in `class_data.py`:

## Classes and Methods
### CombatEngine
* `__init__(self, players, npcs)`: Initializes the combat engine with players and NPCs.
* `determine_initiative(self)`: Rolls for initiative and determines the order of actions.
* `start_combat(self)`: Starts the combat loop.
* `take_turn(self, character)`: Handles the turn logic for a character.
* `execute_action(self, character, action)`: Executes the chosen action.
* `is_combat_over(self)`: Checks if the combat is over.
* `end_round(self)`: Handles end-of-round logic.

### Character
* `__init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None, speed=30, effects=None)`: Initializes a character.
* `apply_condition_with_effects(self, condition_name, duration, spell=None)`: Applies a condition and its effects.
* `decrement_conditions(self, combat_engine)`: Decrements the duration of conditions.
* `remove_condition(self, condition_name)`: Removes a condition.
* `apply_effect(self, effect_name, attribute, modifier, duration)`: Applies an effect.
* `remove_expired_effects(self)`: Removes expired effects.
* `roll_initiative(self)`: Rolls for initiative.
* `take_damage(self, amount)`: Reduces the character's HP.
* `is_alive(self)`: Checks if the character is alive.

### Effect
* `__init__(self, name, attribute, modifier, duration)`: Initializes an effect.
* `apply(self, character)`: Applies the effect to a character.
* `remove(self, character)`: Removes the effect from a character.
* `decrement_duration(self)`: Decreases the duration of the effect.

## Logging
The engine uses the rich library for logging and console output. Logs are written to `game_session.log` and displayed in the console with rich formatting.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License.