# Unified Effect System Design

## Overview
This document outlines a unified approach to handling all character modifications (conditions, spell effects, buffs, debuffs) through a single, consistent system.

## Core Concept
All character modifications are "Effects" with a common structure, regardless of their source (conditions, spells, items, etc.).

## D&D 5e Timing Rules
In D&D 5e, effects have specific timing for when they apply and expire:

### Effect Duration Types:
1. **Fixed Duration**: Effects last for a specific number of rounds (e.g., "3 rounds")
2. **Variable Duration**: Effects last for a rolled duration (e.g., "1d4 rounds") 
3. **Concentration**: Effects last while the caster maintains concentration
4. **Until Removed**: Effects last until removed by specific actions or spells
5. **End of Turn**: Effects expire at the end of the target's current turn
6. **Start of Next Turn**: Effects expire at the start of the target's next turn

### Timing Implementation:
- **Default**: Effects are processed at the **end of turn** for consistency
- **Round-based effects**: Decrement at end of turn, ensuring full round benefit
- **Turn-based effects**: Process at appropriate turn boundary
- **Concentration effects**: Check concentration at end of caster's turn

## Unified Effect Structure

### Effect Definition
```json
{
  "name": "string",                    // Effect name (e.g., "stunned", "bless", "haste")
  "source": "string",                  // Source type: "condition", "spell", "item", "feature"
  "source_name": "string",             // Specific source (e.g., "Hold Person", "Bless spell")
  "duration": {
    "type": "fixed|variable|concentration|until_removed|end_of_turn|start_of_next_turn",
    "value": "string",                 // e.g., "3", "1d4", "concentration", "until_removed"
    "rounds": "integer",               // Current remaining rounds (for tracking)
    "timing": "end_of_turn|start_of_turn"  // When effect is applied/removed during turn
  },
  "self_effects": {                    // Effects on the affected character
    "actions": "normal|none|disadvantage",
    "movement": "normal|none|half_speed|0",
    "attack_roll": "normal|advantage|disadvantage|none",
    "saving_throw": "normal|advantage|disadvantage|none",
    "damage_resistance": "normal|immunity|resistance",
    "attributes": {                    // Direct attribute modifiers
      "ac": "+2",
      "strength": "-2",
      "adv_disadv": "advantage"
    }
  },
  "interaction_effects": {             // Effects on others interacting with this character
    "attack_roll_against": "normal|advantage|disadvantage",
    "critical_hit": "no|yes",
    "saving_throw_against": "normal|advantage|disadvantage"
  },
  "removal": {
    "removable_by": ["saving_throw", "spell", "action", "fixed_duration"],
    "saving_throw": {
      "attribute": "string",
      "dc": "integer",
      "resistance_allowed": "boolean"
    },
    "spell_removal": ["spell_name1", "spell_name2"],
    "special_removal": "string"
  },
  "stacking": {
    "type": "none|extend|stack|replace",
    "max_instances": "integer"
  }
}
```

## Implementation Strategy

### 1. Unified Effect Class
```python
class UnifiedEffect:
    def __init__(self, effect_data, source="spell", source_name="", duration_rounds=1):
        self.name = effect_data["name"]
        self.source = source
        self.source_name = source_name
        self.duration = self._parse_duration(effect_data["duration"], duration_rounds)
        self.self_effects = effect_data.get("self_effects", {})
        self.interaction_effects = effect_data.get("interaction_effects", {})
        self.removal = effect_data.get("removal", {})
        self.stacking = effect_data.get("stacking", {"type": "none", "max_instances": 1})
        
    def apply(self, character):
        """Apply all effects to the character"""
        # Apply self effects
        self._apply_self_effects(character)
        
    def remove(self, character):
        """Remove all effects from the character"""
        # Remove self effects
        self._remove_self_effects(character)
        
    def decrement_duration(self):
        """Decrement duration and return True if expired"""
        if self.duration["type"] in ["fixed", "variable"]:
            self.duration["rounds"] -= 1
            return self.duration["rounds"] <= 0
        elif self.duration["type"] == "end_of_turn":
            # Effect expires at end of current turn
            return True
        elif self.duration["type"] == "start_of_next_turn":
            # Effect expires at start of next turn
            return True
        return False
```

### 2. Character Effect Management
```python
class Character:
    def __init__(self, ...):
        # Single unified effects storage
        self.effects = {}  # {effect_name: [UnifiedEffect instances]}
        
    def apply_effect(self, effect_data, source="spell", source_name="", duration=1):
        """Apply any effect (condition, spell, item, etc.)"""
        effect = UnifiedEffect(effect_data, source, source_name, duration)
        
        # Handle stacking
        if effect.name in self.effects:
            existing_effects = self.effects[effect.name]
            if effect.stacking["type"] == "extend":
                # Extend duration of existing effect
                existing_effects[0].duration["rounds"] = max(
                    existing_effects[0].duration["rounds"], 
                    effect.duration["rounds"]
                )
                return
            elif effect.stacking["type"] == "replace":
                # Remove old, add new
                self.remove_effect(effect.name)
            elif effect.stacking["type"] == "stack":
                # Add new instance if under max
                if len(existing_effects) < effect.stacking["max_instances"]:
                    existing_effects.append(effect)
                    effect.apply(self)
                return
            elif effect.stacking["type"] == "none":
                # Don't apply if already exists
                return
                
        # Apply new effect
        if effect.name not in self.effects:
            self.effects[effect.name] = []
        self.effects[effect.name].append(effect)
        effect.apply(self)
        
    def process_effects_at_end_of_turn(self):
        """Process all effects that should be handled at end of turn"""
        effects_to_remove = []
        
        for effect_name, effect_list in self.effects.items():
            for effect in effect_list:
                # Handle round-based effects
                if effect.duration["type"] in ["fixed", "variable"]:
                    if effect.decrement_duration():
                        effects_to_remove.append((effect_name, effect))
                        
                # Handle end-of-turn effects
                elif effect.duration["type"] == "end_of_turn":
                    effects_to_remove.append((effect_name, effect))
                    
        # Remove expired effects
        for effect_name, effect in effects_to_remove:
            effect.remove(self)
            self.effects[effect_name].remove(effect)
            if not self.effects[effect_name]:
                del self.effects[effect_name]
                
    def process_effects_at_start_of_turn(self):
        """Process all effects that should be handled at start of turn"""
        effects_to_remove = []
        
        for effect_name, effect_list in self.effects.items():
            for effect in effect_list:
                # Handle start-of-next-turn effects
                if effect.duration["type"] == "start_of_next_turn":
                    effects_to_remove.append((effect_name, effect))
                    
        # Remove expired effects
        for effect_name, effect in effects_to_remove:
            effect.remove(self)
            self.effects[effect_name].remove(effect)
            if not self.effects[effect_name]:
                del self.effects[effect_name]
        
    def remove_effect(self, effect_name, source=None):
        """Remove specific effect instances"""
        if effect_name in self.effects:
            effects_to_remove = []
            for effect in self.effects[effect_name]:
                if source is None or effect.source == source:
                    effect.remove(self)
                    effects_to_remove.append(effect)
                    
            for effect in effects_to_remove:
                self.effects[effect_name].remove(effect)
                
            if not self.effects[effect_name]:
                del self.effects[effect_name]
                
    def get_effect_modifier(self, attribute):
        """Get total modifier for an attribute from all active effects"""
        total_modifier = 0
        for effect_list in self.effects.values():
            for effect in effect_list:
                if "attributes" in effect.self_effects:
                    attr_mod = effect.self_effects["attributes"].get(attribute, 0)
                    if isinstance(attr_mod, str) and attr_mod.startswith(("+", "-")):
                        total_modifier += int(attr_mod)
                    elif isinstance(attr_mod, int):
                        total_modifier += attr_mod
        return total_modifier
        
    def has_effect_restriction(self, restriction_type):
        """Check if character has any effects restricting a specific action"""
        for effect_list in self.effects.values():
            for effect in effect_list:
                if effect.self_effects.get(restriction_type) in ["none", "0"]:
                    return True
        return False
```

### 3. Condition Loading
```python
def load_unified_conditions(filepath="conditions/conditions.json"):
    """Load conditions and convert to unified effect format"""
    with open(filepath, 'r') as file:
        conditions_data = json.load(file)
    
    unified_conditions = {}
    for condition_name, condition_data in conditions_data.items():
        # Convert condition format to unified effect format
        unified_conditions[condition_name] = {
            "name": condition_name,
            "source": "condition",
            "source_name": condition_name,
            "duration": condition_data["duration"],
            "self_effects": condition_data["self_effects"],
            "interaction_effects": condition_data["interaction_effects"],
            "removal": condition_data["removal"],
            "stacking": {"type": "extend", "max_instances": 1}
        }
    
    return unified_conditions
```

### 4. Spell Effect Integration
```python
def create_spell_effect(spell_data, target, duration=None):
    """Convert spell effect data to unified effect format"""
    effect_data = spell_data.get("effect", {})
    
    # Handle different spell types
    if spell_data["type"] == "condition":
        # Apply condition from spell
        condition_name = effect_data["modifier"]
        return load_unified_conditions()[condition_name]
        
    elif spell_data["type"] in ["buff", "debuff"]:
        # Create buff/debuff effect
        return {
            "name": spell_data["name"],
            "source": "spell",
            "source_name": spell_data["name"],
            "duration": {
                "type": "fixed",
                "value": str(effect_data.get("duration", 1)),
                "rounds": effect_data.get("duration", 1)
            },
            "self_effects": {
                "attributes": {
                    effect_data["attribute"]: effect_data["modifier"]
                }
            },
            "interaction_effects": {},
            "removal": {"removable_by": ["fixed_duration"]},
            "stacking": {"type": "extend", "max_instances": 1}
        }
```

## Migration Strategy

### Phase 1: Create Unified System
1. Create `UnifiedEffect` class
2. Update `Character` class to use unified effects
3. Create conversion functions for existing data

### Phase 2: Migrate Conditions
1. Convert `conditions_apply.json` to unified format
2. Update condition application logic
3. Test condition functionality

### Phase 3: Migrate Spell Effects
1. Update spell casting to use unified system
2. Convert spell effect data
3. Test spell functionality

### Phase 4: Cleanup
1. Remove old `Effect` class
2. Remove old condition/effect methods
3. Update all references

## Benefits

1. **Consistency**: All effects work the same way
2. **Maintainability**: Single codebase for effect logic
3. **Flexibility**: Easy to add new effect types
4. **Debugging**: Unified logging and tracking
5. **D&D 5e Compatibility**: Matches official rules structure

## Example Usage

```python
# Apply condition
character.apply_effect(
    unified_conditions["stunned"], 
    source="condition", 
    source_name="stunned", 
    duration=2
)

# Apply spell effect
character.apply_effect(
    create_spell_effect(spell_data, target, duration=3),
    source="spell",
    source_name="Bless",
    duration=3
)

# Check restrictions
if character.has_effect_restriction("actions"):
    print("Character cannot take actions")

# Get total AC modifier
ac_bonus = character.get_effect_modifier("ac")
```

This unified approach eliminates the dual system problem while maintaining full D&D 5e compatibility and improving code maintainability. 