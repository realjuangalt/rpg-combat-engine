You're absolutely right—the most obvious bug is that the combat starts with all conditions applied, even though they should be off by default. Let's analyze the code to identify potential causes of this issue and reason through a solution.

### **Potential Causes of Conditions Being On by Default:**

1. **Initialization of Character's Conditions**:
   - Characters might be starting the combat with conditions pre-applied. If the conditions are being initialized as active rather than inactive, this would explain why conditions like `stunned`, `paralyzed`, and others are already affecting the character.

2. **Default Active State for Conditions**:
   - The conditions might be initialized with the `"active": True` flag by default, rather than `"active": False`. The code should ensure that all conditions are set to inactive at the start of combat and only become active when explicitly applied during gameplay.

3. **Incorrect State Persistence**:
   - If the `conditions` dictionary for each character is being loaded or stored incorrectly, the system may be reactivating conditions that should have been removed or remained inactive.

4. **Improper Reset of Conditions**:
   - When combat ends or resets, the character’s conditions might not be properly reset to their default inactive state. A reset mechanism should clear all active conditions or set them to inactive.

### **Key Areas of Code to Investigate**:

1. **Character Initialization**:
   - Ensure that when characters are initialized (whether from JSON or other sources), their conditions are set to `"active": False` and `duration = 0` by default.

2. **Condition Application Logic**:
   - When conditions are applied via `apply_condition_with_effects`, ensure that conditions aren't incorrectly applied at the start of combat or due to lingering state from a previous combat round.

3. **JSON Loading (game_state)**:
   - Check how the `conditions` dictionary is loaded from JSON or wherever the character data is coming from. Ensure no conditions are mistakenly marked as active when the game starts.

### **Steps to Solve the Issue**:

1. **Update Condition Initialization**:
   - Ensure all conditions are initialized to `"active": False` and `"duration": 0` during character creation or combat start.

2. **Reset Character Conditions on Combat Start**:
   - Add a method to reset all conditions to inactive at the start of combat to avoid inheriting any leftover conditions from previous rounds or tests.

3. **Refactor Condition State Management**:
   - Ensure that conditions are only set to active when applied explicitly during combat (e.g., via spells or effects). The `apply_condition_with_effects` method should only activate conditions when they are triggered by game events.

---

### **Proposed Fixes**:

1. **Ensure Default Condition Initialization**:
   In the `Character` class or wherever characters are created, make sure the conditions are initialized like this:
   ```python
   self.conditions = {condition_name: {"active": False, "duration": 0} for condition_name in CONDITIONS_DICT.keys()}
   ```

2. **Reset Conditions at Combat Start**:
   Before combat starts, we should reset all conditions to inactive by adding something like this in the `start_combat` method or similar place:
   ```python
   def reset_conditions(self):
       for character in self.characters:
           for condition_name in character.conditions:
               character.conditions[condition_name]["active"] = False
               character.conditions[condition_name]["duration"] = 0
   ```

3. **Check JSON Loaders for Condition States**:
   If characters are loaded from a JSON file, make sure the conditions are initialized correctly in that process.

---

### **Key Areas to Investigate and Update**:

- **Character Initialization**: Make sure characters start with all conditions set to inactive.
- **start_combat()**: Add a step to reset all conditions for each character at the start of combat.
- **JSON Loading**: If characters are loaded from external sources, ensure that conditions aren’t mistakenly initialized as active.
- **apply_condition_with_effects()**: Ensure that conditions are only set to active when appropriate game events occur.

Let's implement the condition reset mechanism and review the current initialization process to solve this bug. Would you like to see specific code updates for these suggestions?