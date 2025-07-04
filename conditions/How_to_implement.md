Let’s carefully analyze how we can implement the new `conditions_apply.json` into your combat engine. Here's the approach:

### Step 1: **Review the Role of the Current Condition Files**:
Your combat engine currently uses two files:
- **`action_restrictions.json`**: Defines how specific conditions restrict or modify actions, attacks, movement, etc.
- **`conditions_data.json`**: Provides details about condition attributes, modifiers, durations, and condition removal mechanisms.

These two files seem to manage:
1. **Action Modifiers**: How a condition affects a character’s ability to perform actions, movement, attacks, etc.
2. **Condition Duration and Removal**: How long a condition lasts and how it is removed (e.g., saving throws or spells).

### Step 2: **How the New `conditions_apply.json` Integrates**:
The new `conditions_apply.json` combines these functionalities into one unified structure. It includes:
- **Self-Effects**: How the condition affects the afflicted character (actions, movement, etc.).
- **Interaction Effects**: How creatures interacting with the afflicted are affected (e.g., attackers gaining advantage).
- **Duration and Removal**: How long the condition lasts and the methods for removing it (e.g., saving throws, spells).

### Step 3: **How to Replace the Existing Implementation**:
Here’s how we can replace the current usage of both `action_restrictions.json` and `conditions_data.json` with the new `conditions_apply.json`:

#### **1. Modify the Condition-Checking Mechanism**:
- **Current Approach**: You likely have a method like `check_action_restrictions()` that checks conditions and then uses the `action_restrictions.json` file to apply restrictions (like blocking actions or attacks).
- **New Approach**: You will now check the condition's `self_effects` from `conditions_apply.json`. For example:
  - If `self_effects["actions"]` is `"none"`, the character can’t take any actions.
  - If `self_effects["movement"]` is `"0"`, the character’s speed is reduced to 0.

#### **2. Apply Interaction Modifiers**:
- **Current Approach**: You may currently handle how conditions affect those interacting with the afflicted through both `action_restrictions.json` and custom logic in the engine.
- **New Approach**: You will now use the `interaction_effects` in the new `conditions_apply.json`. For example:
  - If `interaction_effects["attack_roll_against"]` is `"advantage"`, attackers will gain advantage when attacking the afflicted character.
  - If `interaction_effects["critical_hit"]` is `"yes"`, attackers within 5 feet will automatically score critical hits on a paralyzed creature.

#### **3. Manage Duration and Removal**:
- **Current Approach**: You likely track the duration of conditions using `conditions_data.json` and manage removal through saving throws or specific spells.
- **New Approach**: You will now use the `duration` and `removal` fields in `conditions_apply.json`:
  - The `duration` field tells you how long a condition lasts (fixed, variable, or until removed).
  - The `removal` field provides information on saving throws or spells that can end the condition. If no removal method applies, it’s clear from the structure (e.g., `special_removal: null`).

#### **4. Streamline the `decrement_conditions()` Logic**:
You currently use a function like `decrement_conditions()` to decrement condition durations. This function needs to be updated:
- **Old Approach**: You check the condition's duration in `conditions_data.json` and decrement it round by round.
- **New Approach**: You can now pull the `duration["type"]` and `duration["value"]` from `conditions_apply.json` to manage duration decrementing. This will also simplify checking if a condition is removed (via `removal` fields).

### Step 4: **Concrete Plan for Integration**:
1. **Load the `conditions_apply.json` File**:
   - Replace any logic that loads `action_restrictions.json` and `conditions_data.json` with loading the new `conditions_apply.json` file at the start of the engine.

   DONE SO FAR

2. **Update the Condition Application Logic**:
   - Replace references to action restrictions and effects with the `self_effects` and `interaction_effects` sections in `conditions_apply.json`.
   - Example:
     ```python
     if condition["self_effects"]["actions"] == "none":
         log_message(f"{character.name} cannot take actions.")
     if condition["interaction_effects"]["attack_roll_against"] == "advantage":
         log_message(f"Attackers have advantage when attacking {character.name}.")
     ```

3. **Update the `decrement_conditions()` Method**:
   - Use the `duration` field from `conditions_apply.json` to handle duration decrementing and condition removal.

4. **Handle Condition Removal**:
   - Update logic that handles saving throws and spell-based condition removal to use the `removal` section from the new data file.

### Step 5: **Advantages of the New System**:
- **Unified Structure**: Instead of managing two files (one for action restrictions and one for condition data), everything is consolidated into one file, making the engine easier to maintain and expand.
- **Clarity and Consistency**: With fields for both self-effects and interaction effects, the condition handling is clearer and covers all scenarios (whether the character is afflicted or interacting with someone who is).
- **Extensibility**: You can easily add new conditions or modify existing ones by editing a single file.

### Next Steps:
1. Implement loading of the `conditions_apply.json` file.
2. Update the core combat engine logic to reference `self_effects`, `interaction_effects`, `duration`, and `removal` from this file.
3. Replace old `action_restrictions.json` and `conditions_data.json` references with the new consolidated structure.

Let me know if you want to proceed with implementing this, and I can help walk through the specific code changes!