It seems that the conditions are still not being initialized correctly across the entities. To address this issue, we'll take a more structured approach to ensure that every entity, whether it's a player character or NPC, has its `conditions` initialized with all available conditions from the `CONDITIONS_DICT`, each starting as inactive and with a duration of 0.

### The Plan:
- **Initialization**: Ensure that during the initialization of each entity (player or NPC), the `self.conditions` field includes all the possible conditions from `CONDITIONS_DICT` by default, with their states set to inactive (`active: False`) and duration set to 0.
- **Condition Application**: Update the `apply_condition` method to check and apply conditions only after ensuring they exist in the entity's condition dictionary.

### Updated Initialization Code:
Make sure each entity’s `conditions` field is correctly initialized with all conditions, regardless of whether `conditions` is passed or not.

```python
def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None):
    # Initialize conditions from CONDITIONS_DICT if no conditions are passed or if it's empty
    if not conditions:
        self.conditions = {condition_name: {"active": False, "duration": 0} for condition_name in CONDITIONS_DICT.keys()}
    else:
        # Ensure all conditions from CONDITIONS_DICT are present, initializing missing ones
        self.conditions = {condition_name: conditions.get(condition_name, {"active": False, "duration": 0}) for condition_name in CONDITIONS_DICT.keys()}
    
    log_message(f"DEBUG: conditions passed to init: {conditions}")
    log_message(f"self.conditions after initialization: {self.conditions}")
    log_message(f"Conditions DICT keys: {CONDITIONS_DICT.keys()}")
```

### Explanation:
1. **Condition Initialization**: 
   - If `conditions` is not passed or is empty, it will initialize `self.conditions` with every condition from `CONDITIONS_DICT`, each starting as inactive and with a duration of 0.
   - If `conditions` is passed but is missing some conditions, it will ensure all conditions from `CONDITIONS_DICT` are present in `self.conditions`, filling in any missing ones with the default values (`active: False, duration: 0`).

### Updated `apply_condition` Method:
Next, let's update the `apply_condition` method to avoid the `KeyError` by ensuring the condition exists before trying to modify it:

```python
def apply_condition(self, condition_name, duration):
    """Applies a condition to the character and sets its duration."""
    
    log_message("You've arrived at APPLY_CONDITION.")
    
    # Fetch condition data from the fixed CONDITIONS dictionary
    condition_data = CONDITIONS_DICT.get(condition_name)
    
    if not condition_data:
        log_message(f"Error: Condition {condition_name} not found in the conditions data.")
        return
    
    # Ensure the condition is initialized in self.conditions
    if condition_name not in self.conditions:
        log_message(f"Error: {condition_name} is not in self.conditions, initializing it now.")
        self.conditions[condition_name] = {"active": False, "duration": 0}
    
    log_message(f"DEBUG 152, print condition data {condition_data}")
    
    # Check if the condition is already applied
    if self.conditions[condition_name]["active"]:
        # Condition is already active, update the duration
        log_message(f"{self.name} already has {condition_name}, updating duration by {duration} rounds.")
        self.conditions[condition_name]["duration"] = max(self.conditions[condition_name]["duration"], duration)
    else:
        # Condition is being applied for the first time
        log_message(f"Applying {condition_name} to {self.name} for {duration} rounds.")
        self.conditions[condition_name]["active"] = True
        self.conditions[condition_name]["duration"] = duration

    # Apply the self-effects associated with the condition (e.g., disabling actions or movement)
    self.apply_condition_effects(condition_data)

    log_message(f"{self.name} is now affected by {condition_name} for {duration} rounds.")
```

### Explanation:
- **Ensure Condition Exists**: The `apply_condition` method checks whether the condition exists in `self.conditions`. If it doesn't, the condition is initialized (as inactive with a duration of 0) before modifying it.
- **Apply the Condition**: The condition is then applied, updating its `active` state and `duration`.

### Expected Result:
With these changes:
1. **All conditions** should be initialized for every entity (NPC or player), even if none are passed.
2. The **`KeyError`** should be resolved, as every condition, including `'stunned'`, will exist in `self.conditions`.
3. The conditions will update dynamically based on actions like spells being cast, with the `apply_condition` method handling the changes.

Try running this and check if the issue with `'stunned'` persists.