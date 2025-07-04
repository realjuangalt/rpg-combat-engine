After analyzing the code, here's a summary of the methods related to applying effects or conditions in the `combat_engine.py`:

### Methods Related to Conditions and Effects:
1. **`apply_condition(self, condition_name, duration)`**:
   - Applies a condition to the character and sets its duration.
   - Ensures the condition is initialized if it's not already present.
   - Calls `apply_condition_effects` to apply the self-effects (disabling actions, movement, etc.).

2. **`apply_condition_effects(self, condition_data)`**:
   - Applies the immediate effects of a condition, such as disabling actions or movement.
   - Handles attributes like `actions` and `movement`.
   - Applies normal attribute modifiers using the `Effect` class.

3. **`decrement_conditions(self, combat_engine)`**:
   - Decrements the duration of each condition and checks if it should be set to inactive.
   - Includes handling for different duration types (`fixed`, `variable`, `until_removed`).
   - Checks for saving throw removal and spell-based removal.

4. **`check_condition_removal(self, character)`**:
   - Checks if any conditions can be removed via saving throws or spells.
   - Handles saving throw logic by calling `saving_throw`.

5. **`remove_condition(self, condition_name)`**:
   - Removes a specified condition from the character and reverses its effects.

6. **`apply_effect(self, effect)`**:
   - Applies a specific effect to a character, typically used for applying modifiers from conditions.

7. **`remove_effect(self, effect)`**:
   - Removes a specific effect from a character, used when reversing the effects of a condition.

8. **`saving_throw(self, target, save, dc, adv_disadv="normal")`**:
   - Handles saving throws for a character, applying proficiency bonuses if applicable.
   - This is used in conjunction with condition removal, where a successful saving throw can remove a condition.

### Redundant or Deprecated Code:
1. (DONE)**Multiple condition checks**: There are several places where condition application and removal are handled, such as in `apply_condition`, `apply_condition_effects`, `check_condition_removal`, and `remove_condition`. These can sometimes overlap or cause redundancy in how conditions are processed.

2. (LATER MAYBE)**Hardcoded `Effect` class handling**: The `Effect` class could be further integrated into how conditions are applied to avoid manually applying attributes and modifiers in `apply_condition_effects`.

### Next Steps to Update:
1. (DONE)**Simplify Condition Management**:
   - Consolidate condition checks and applications in fewer methods to avoid redundancy. For instance, the `apply_condition` and `apply_condition_effects` could be merged to reduce code repetition.
   - Use the `Effect` class more consistently for both applying and removing effects instead of directly handling attributes in `apply_condition_effects`.

2. (DONE)**Use of Conditions Dictionary**:
   - The conditions are stored in both `CONDITIONS_DICT` and character-specific dictionaries. Ensure that condition data (like duration and effects) is always referenced from `CONDITIONS_DICT` to avoid inconsistencies.

3. **Deprecate Separate Saving Throw Logic**:
   - You can merge the saving throw logic in `decrement_conditions` and `check_condition_removal` to avoid duplicating checks.

By streamlining these portions, we can make the code cleaner and reduce redundancy, improving its maintainability and efficiency in managing conditions and effects.


--------

To update and ensure that all instances of condition application reference the `CONDITIONS_DICT` and the character's `conditions` dictionary properly, you should focus on the following areas in the current reference code. Here's the reasoning:

### Key Methods Related to Conditions

- **`apply_condition_with_effects`**: This method is responsible for applying conditions to a character. It already references `CONDITIONS_DICT` for condition data but should also ensure that the condition's effects are properly handled through the `Effect` class and applied or reversed as needed.

- **`decrement_conditions`**: This method handles reducing the duration of conditions and marking them as inactive when expired. It uses `CONDITIONS_DICT` to check for condition data. Make sure that all interactions with conditions, such as decrementing duration or removing conditions, rely on `CONDITIONS_DICT` for accurate data.

- **`remove_condition`**: This method should reverse the effects of conditions when they are removed. Again, it must correctly reference the `CONDITIONS_DICT` and should be updated to use the `Effect` class to handle the reversal of effects.

### Areas That Need to Reference the `CONDITIONS_DICT` Correctly

- **`check_action_restrictions`**: This method currently checks if actions (such as movement, attacking, or casting spells) are restricted due to conditions. It must reference the `CONDITIONS_DICT` to ensure that the correct condition data is being used to determine whether actions are allowed or restricted.

- **`check_condition_removal`**: This method handles checking whether conditions can be removed, such as through saving throws. It should reference `CONDITIONS_DICT` for condition removal data and to ensure the correct handling of saving throws or spells.

### Steps to Update

1. (DONE)**Remove Redundancy in Effect Handling**:
   You should update methods like `apply_condition_with_effects` and `remove_condition` to directly rely on the `Effect` class, rather than manually applying or reversing condition effects. This simplifies the logic and avoids redundancy.

2. (DONE)**Standardize References to Conditions**:
   Ensure that all methods that interact with conditions (such as `apply_condition_with_effects`, `decrement_conditions`, `remove_condition`, `check_action_restrictions`, and `check_condition_removal`) consistently reference `CONDITIONS_DICT` for condition data (e.g., self-effects, removal rules) and use the character's `conditions` dictionary for state tracking (e.g., active status, duration).

### Example Changes

For **`apply_condition_with_effects`**, ensure that after fetching condition data, effects are applied using the `Effect` class:

```python
def apply_condition_with_effects(self, condition_name, duration):
    log_message(f"APPLY CONDITION WITH EFFECTS: {condition_name}")

    # Fetch condition data from the fixed CONDITIONS dictionary
    condition_data = CONDITIONS_DICT.get(condition_name)
    
    if not condition_data:
        log_message(f"Error: Condition {condition_name} not found.")
        return

    # Initialize or update condition state
    if condition_name not in self.conditions:
        self.conditions[condition_name] = {"active": False, "duration": 0}

    # Activate condition and update duration
    if self.conditions[condition_name]["active"]:
        self.conditions[condition_name]["duration"] = max(self.conditions[condition_name]["duration"], duration)
    else:
        self.conditions[condition_name] = {"active": True, "duration": duration}

    # Apply effects using the Effect class
    self_effects = condition_data.get("self_effects", {})
    for attribute, modifier in self_effects.items():
        effect = Effect(name=condition_name, attribute=attribute, modifier=modifier, duration=duration)
        effect.apply(self)
```

For **`remove_condition`**, ensure it properly reverses the effects through the `Effect` class:

```python
def remove_condition(self, condition_name):
    if condition_name in self.conditions:
        condition_data = CONDITIONS_DICT.get(condition_name)
        if condition_data:
            self_effects = condition_data.get('self_effects', {})

            # Reverse each effect using the Effect class
            for attribute, modifier in self_effects.items():
                effect = Effect(name=condition_name, attribute=attribute, modifier=modifier, duration=0)
                effect.remove(self)

        # Mark the condition as inactive
        self.conditions[condition_name] = {"active": False, "duration": 0}
        log_message(f"{condition_name} has been removed from {self.name} and its effects reversed.")
```

### Areas to Update Method References

- **`apply_condition_with_effects`**
- **`remove_condition`**
- **`decrement_conditions`**
- **`check_action_restrictions`**
- **`check_condition_removal`**

Each of these methods should consistently refer to `CONDITIONS_DICT` for global condition data and the character's `conditions` dictionary for the state of specific conditions on that character. Any references to conditions must go through these two structures to ensure data consistency and proper effect handling.