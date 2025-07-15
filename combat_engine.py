# effects and conditions are applied successfully, but not removed successfully, seems like something is wrong with the part that decrements conditions. 
# Imports
import json
import d20
from rich.console import Console
from rich.logging import RichHandler
from rich.pretty import Pretty
from rich.traceback import install
import logging
from enum import Enum, auto
from class_data import CLASS_DATA


# Initialize rich traceback handler
install()

# Setup Rich console
console = Console()

# Setup custom logger with RichHandler and file logging
logger = logging.getLogger("combat_engine")
logger.setLevel(logging.DEBUG)
console_handler = RichHandler(console=console, rich_tracebacks=True, markup=True)
file_handler = logging.FileHandler("game_session.log", mode='w')
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# === DEBUG MODE FLAG ===
DEBUG_MODE = True  # Set to False for normal play, True for detailed logs

# Load the action restrictions from a file
# Load conditions from the new conditions_apply.json file
def load_conditions(filepath="conditions/consolidated_conditions.json"):
    with open(filepath, 'r') as file:
        return json.load(file)

# Example usage
CONDITIONS_DICT = load_conditions()


def log_message(message, debug_only=False):
    if not debug_only or DEBUG_MODE:
        logger.info(message)

def roll_with_advantage_disadvantage(modifier, adv_disadv="normal"):
    """Rolls with advantage, disadvantage, or normally."""
    if adv_disadv == "advantage":
        roll_1 = d20.roll(f"1d20 + {modifier}")
        roll_2 = d20.roll(f"1d20 + {modifier}")
        log_message(f"[bold green]Advantage roll: {roll_1.result} and {roll_2.result} - using higher: {max(roll_1.total, roll_2.total)}[/bold green]")
        return max(roll_1, roll_2, key=lambda roll: roll.total)
    elif adv_disadv == "disadvantage":
        roll_1 = d20.roll(f"1d20 + {modifier}")
        roll_2 = d20.roll(f"1d20 + {modifier}")
        log_message(f"[bold red]Disadvantage roll: {roll_1.result} and {roll_2.result} - using lower: {min(roll_1.total, roll_2.total)}[/bold red]")
        return min(roll_1, roll_2, key=lambda roll: roll.total)
    else:
        return d20.roll(f"1d20 + {modifier}")

# Enums for action types, damage types, conditions
class ActionType(Enum):
    ATTACK = auto()
    CAST_SPELL = auto()
    DEFEND = auto()
    BONUS_ACTION = auto()

class DamageType(Enum):
    SLASHING = auto()
    PIERCING = auto()
    FIRE = auto()
    LIGHTNING = auto()
    # More damage types as needed

class Condition(Enum):
    STUNNED = auto()
    POISONED = auto()
    BLINDED = auto()
    # More conditions as needed

class EffectTiming(Enum):
    """D&D 5e effect timing rules"""
    START_OF_TURN = "start_of_turn"
    END_OF_TURN = "end_of_turn"
    START_OF_NEXT_TURN = "start_of_next_turn"
    END_OF_COMBAT = "end_of_combat"
    UNTIL_REMOVED = "until_removed"

class EffectDuration(Enum):
    """D&D 5e effect duration types"""
    FIXED = "fixed"  # e.g., 3 rounds
    VARIABLE = "variable"  # e.g., 1d4 rounds
    CONCENTRATION = "concentration"  # until concentration breaks
    UNTIL_REMOVED = "until_removed"  # until removed by other means

class UnifiedEffect:
    """
    Unified effect system that handles both conditions and spell effects.
    Replaces the dual condition/effect system with a single, consistent approach.
    """
    
    def __init__(self, name, effect_type, source, duration_type=EffectDuration.FIXED, 
                 duration_value=1, timing=EffectTiming.END_OF_TURN, 
                 attributes=None, stacking_rules=None, removal_conditions=None):
        """
        Initialize a unified effect.
        
        Args:
            name (str): Name of the effect (e.g., "Stunned", "Bless", "Invisible")
            effect_type (str): Type of effect ("condition", "buff", "debuff", "spell_effect")
            source (str): Source of the effect ("spell", "condition", "item", "ability")
            duration_type (EffectDuration): How the duration works
            duration_value: Duration value (int for fixed, str for variable like "1d4")
            timing (EffectTiming): When the effect is processed
            attributes (dict): Dictionary of attribute modifications
            stacking_rules (dict): How this effect stacks with others
            removal_conditions (dict): Conditions that can remove this effect
        """
        self.name = name
        self.effect_type = effect_type
        self.source = source
        self.duration_type = duration_type
        self.duration_value = duration_value
        self.timing = timing
        self.attributes = attributes or {}
        self.stacking_rules = stacking_rules or {}
        self.removal_conditions = removal_conditions or {}
        
        # Current state
        self.active = True
        self.current_duration = self._calculate_initial_duration()
        self.applied_modifiers = {}  # Track what was actually applied
        
    def _calculate_initial_duration(self):
        """Calculate the initial duration based on duration type."""
        if self.duration_type == EffectDuration.FIXED:
            return int(self.duration_value)
        elif self.duration_type == EffectDuration.VARIABLE:
            # Roll for variable duration (e.g., "1d4" -> roll 1d4)
            if isinstance(self.duration_value, str) and 'd' in self.duration_value:
                return d20.roll(self.duration_value).total
            else:
                return int(self.duration_value)
        elif self.duration_type == EffectDuration.CONCENTRATION:
            return -1  # Special value for concentration
        elif self.duration_type == EffectDuration.UNTIL_REMOVED:
            return -2  # Special value for until removed
        else:
            return 1  # Default to 1 round
            
    def apply(self, character):
        """Apply the effect to a character."""
        if not self.active:
            return
            
        log_message(f"[bold blue]Applying unified effect {self.name} to {character.name}[/bold blue]")
        
        # Apply each attribute modification
        for attribute, modification in self.attributes.items():
            self._apply_attribute_modification(character, attribute, modification)
            
    def _apply_attribute_modification(self, character, attribute, modification):
        """Apply a single attribute modification."""
        if attribute == "adv_disadv":
            # Handle advantage/disadvantage
            setattr(character, attribute, modification)
            self.applied_modifiers[attribute] = modification
            log_message(f"{character.name} now has {modification} on advantage/disadvantage.")
            
        elif attribute == "movement" and modification == "none":
            # Handle movement restrictions
            character.movement = 0
            self.applied_modifiers[attribute] = 0
            log_message(f"{character.name} is now unable to move due to {self.name}.")
            
        elif attribute == "actions" and modification == "none":
            # Handle action restrictions
            character.check_action_restrictions = False
            self.applied_modifiers[attribute] = False
            log_message(f"{character.name} is now unable to act due to {self.name}.")
            
        elif attribute in character.stats:
            # Handle numerical modifiers
            current_value = getattr(character, attribute, 0)
            if isinstance(modification, (int, float)):
                new_value = current_value + modification
                setattr(character, attribute, new_value)
                self.applied_modifiers[attribute] = modification
                log_message(f"{self.name} increases {attribute} by {modification} for {character.name}. New value: {new_value}")
            else:
                # Handle string modifiers (like "advantage", "disadvantage")
                setattr(character, attribute, modification)
                self.applied_modifiers[attribute] = modification
                log_message(f"{self.name} sets {attribute} to {modification} for {character.name}.")
                
    def remove(self, character):
        """Remove the effect from a character."""
        if not self.active:
            return
            
        log_message(f"[bold blue]Removing unified effect {self.name} from {character.name}[/bold blue]")
        
        # Remove each applied modification
        for attribute, modification in self.applied_modifiers.items():
            self._remove_attribute_modification(character, attribute, modification)
            
        # Reset state
        self.active = False
        self.current_duration = 0
        self.applied_modifiers = {}
        
    def _remove_attribute_modification(self, character, attribute, modification):
        """Remove a single attribute modification."""
        if attribute == "adv_disadv":
            # Reset advantage/disadvantage
            setattr(character, attribute, "normal")
            log_message(f"{character.name}'s advantage/disadvantage reset to normal.")
            
        elif attribute == "movement" and modification == 0:
            # Restore movement
            character.movement = character.default_movement
            log_message(f"{character.name}'s movement restored to {character.default_movement}.")
            
        elif attribute == "actions" and modification == False:
            # Restore actions
            character.check_action_restrictions = True
            log_message(f"{character.name} is now able to act again.")
            
        elif attribute in character.stats:
            # Remove numerical modifiers
            current_value = getattr(character, attribute, 0)
            if isinstance(modification, (int, float)):
                new_value = current_value - modification
                setattr(character, attribute, new_value)
                log_message(f"{self.name} decreases {attribute} by {modification} for {character.name}. New value: {new_value}")
            else:
                # Reset string modifiers to default
                if attribute == "adv_disadv":
                    setattr(character, attribute, "normal")
                else:
                    # For other attributes, reset to base value
                    base_value = getattr(character, f"base_{attribute}", 0)
                    setattr(character, attribute, base_value)
                log_message(f"{self.name} resets {attribute} for {character.name}.")
                
    def decrement_duration(self):
        """Decrement the effect duration and return True if expired."""
        if self.duration_type in [EffectDuration.CONCENTRATION, EffectDuration.UNTIL_REMOVED]:
            return False  # These don't expire by duration
            
        if self.current_duration > 0:
            self.current_duration -= 1
            log_message(f"Duration of {self.name} decreased to {self.current_duration} rounds.")
            
        return self.current_duration <= 0
        
    def can_be_removed_by(self, removal_type, **kwargs):
        """Check if this effect can be removed by a specific method."""
        if removal_type not in self.removal_conditions:
            return False
            
        removal_data = self.removal_conditions[removal_type]
        
        if removal_type == "saving_throw":
            # Check if saving throw conditions match
            required_attr = removal_data.get("attribute")
            required_dc = removal_data.get("dc")
            return (kwargs.get("attribute") == required_attr and 
                   kwargs.get("dc") == required_dc)
                   
        elif removal_type == "spell":
            # Check if spell can remove this effect
            required_spells = removal_data.get("spells", [])
            return kwargs.get("spell_name") in required_spells
            
        return True
        
    def to_dict(self):
        """Convert effect to dictionary for serialization."""
        return {
            "name": self.name,
            "effect_type": self.effect_type,
            "source": self.source,
            "duration_type": self.duration_type.value,
            "duration_value": self.duration_value,
            "timing": self.timing.value,
            "attributes": self.attributes,
            "stacking_rules": self.stacking_rules,
            "removal_conditions": self.removal_conditions,
            "active": self.active,
            "current_duration": self.current_duration,
            "applied_modifiers": self.applied_modifiers
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create effect from dictionary."""
        effect = cls(
            name=data["name"],
            effect_type=data["effect_type"],
            source=data["source"],
            duration_type=EffectDuration(data["duration_type"]),
            duration_value=data["duration_value"],
            timing=EffectTiming(data["timing"]),
            attributes=data.get("attributes", {}),
            stacking_rules=data.get("stacking_rules", {}),
            removal_conditions=data.get("removal_conditions", {})
        )
        effect.active = data.get("active", True)
        effect.current_duration = data.get("current_duration", effect.current_duration)
        effect.applied_modifiers = data.get("applied_modifiers", {})
        return effect

class Character:
    """Base class for all characters (players and NPCs) in the game."""

    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None, speed=30, effects=None, description=None, **kwargs):
        # log_message(f"DEBUG: conditions passed to init: {conditions}")  # Check the value of conditions passed

        self.name = name
        self.description = description
        self.hp = hp
        self.ac = ac
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
        self.adv_disadv = "normal"  # Initialize the attribute here
        self.damage = damage
        self.inventory = inventory  # List of items (e.g., weapons)
        self.class_type = class_type
        self.default_movement = speed  # Default movement set here
        self.movement = self.default_movement  # Start with the default movement
        self.spells = spells if spells is not None else []
        self.proficiency_bonus = 0  # Base proficiency bonus, can be updated dynamically
        self.current_hp = hp  # To track damage
        self.initiative = 0


        self.stats = {
            "ac": self.ac, 
            "strength": self.strength, 
            "dexterity": self.dexterity, 
            "constitution": self.constitution, 
            "intelligence": self.intelligence, 
            "wisdom": self.wisdom, 
            "charisma": self.charisma,
            "movement": self.movement,  # Add movement to be affected by effects
            "hp": self.current_hp,      # Add health as a modifiable stat
            "adv_disadv": "normal"      # Track advantage/disadvantage
        }

        # Initialize conditions dynamically - conditions will only be added as they are applied
        if not conditions:
            self.conditions = {}
        else:
            # Handle both old format (condition_name: duration) and new format (condition_name: {"active": bool, "duration": int})
            self.conditions = {}
            for condition_name, condition_data in conditions.items():
                if isinstance(condition_data, dict):
                    # New format: {"active": bool, "duration": int}
                    self.conditions[condition_name] = condition_data
                elif isinstance(condition_data, int):
                    # Old format: duration as integer - convert to new format
                    self.conditions[condition_name] = {"active": True, "duration": condition_data}
                else:
                    # Invalid format - skip
                    log_message(f"Warning: Invalid condition format for {condition_name}: {condition_data}")
                    continue
        
        # log_message(f"DEBUG: self.conditions after initialization: {self.conditions}")


        # Unified effects system - replaces both conditions and effects
        self.unified_effects = {}  # Dictionary of effect_name -> UnifiedEffect
        # self.alive = True # checks that character is alive
        
        self.str_mod = self.calculate_modifier("strength")
        self.dex_mod = self.calculate_modifier("dexterity")
        self.con_mod = self.calculate_modifier("constitution")
        self.int_mod = self.calculate_modifier("intelligence")
        self.wis_mod = self.calculate_modifier("wisdom")
        self.cha_mod = self.calculate_modifier("charisma")




        # Class-specific data
        class_data = CLASS_DATA.get(self.class_type.lower())
        if class_data:
            self.proficient_saves = class_data["proficient_saves"]
            self.spellcasting_mod = class_data["spellcasting_mod"]
        else:
            raise ValueError(f"Class type {self.class_type} is not valid.")

        # Set the proficiency bonus based on character level


    def is_within_melee_range(self, target):
        """Placeholder: Assume all melee attacks are in range for now."""
        return True

    def is_within_ranged_range(self, target):
        """Placeholder: Assume all ranged attacks are in range for now."""
        return True
    
    def apply_condition_with_effects(self, condition_name, duration, spell=None):
        """
        Applies a condition and its effects to the character, managing duration and active state.
        """
        # log_message(f"APPLY CONDITION WITH EFFECTS: {condition_name}")

        # Fetch condition data from the fixed CONDITIONS dictionary
        condition_data = CONDITIONS_DICT.get(condition_name)

        if not condition_data:
            log_message(f"Error: Condition {condition_name} not found in CONDITIONS_DICT.")
            return

        # Check if the condition has a saving throw (from the spell)
        if spell and 'save' in spell:
            save_attr = spell['save']
            save_dc = spell['dc']
            spell_modifier = spell['effect']['modifier']

            # log_message(f"DEBUG: {self.name} is attempting a saving throw against {condition_name} (DC: {save_dc}).")
            # Perform the saving throw for the target
            if self.saving_throw(self, save_attr, save_dc, spell_modifier):
                log_message(f"{self.name} succeeds on the saving throw and avoids {condition_name}.")
                return  # Exit early, condition not applied
            log_message(f"{self.name} fails the saving throw and is affected by {condition_name}.")

        # Initialize or update condition in the character's state tracking dictionary
        if condition_name not in self.conditions:
            # log_message(f"DEBUG 162: {condition_name} is being applied to {self.name} for the first time, initializing it.")
            self.conditions[condition_name] = {"active": True, "duration": duration}
        else:
            # If already active, extend the duration
            if self.conditions[condition_name]["active"]:
                log_message(f"{self.name} already has {condition_name}. Extending duration by {duration} rounds.")
                self.conditions[condition_name]["duration"] = max(self.conditions[condition_name]["duration"], duration)
            else:
                log_message(f"Re-activating {condition_name} for {self.name} for {duration} rounds.")
                self.conditions[condition_name] = {"active": True, "duration": duration}

        # Apply the condition's effects using the unified effect system
        self_effects = condition_data.get("self_effects", {})
        if self_effects:
            # Convert condition data to unified effect format
            removal_conditions = {}
            if "removal" in condition_data:
                removal_conditions = condition_data["removal"]
                
            self.apply_unified_effect(
                effect_name=condition_name,
                effect_type="condition",
                source="condition",
                duration_type=EffectDuration.FIXED,
                duration_value=duration,
                timing=EffectTiming.END_OF_TURN,
                attributes=self_effects,
                removal_conditions=removal_conditions
            )
        else:
            log_message(f"{condition_name} has no self effects for {self.name}.")

        log_message(f"{self.name} is now affected by {condition_name} for {duration} rounds.")

    def decrement_conditions(self, combat_engine):
        """
        Decrement the duration of each condition on the character, and check if any conditions 
        can be removed via saving throws or other mechanisms.
        """
        # Process unified effects instead of old condition system
        self.remove_expired_effects()
        
        # Check for saving throw opportunities
        for effect_name, effect in self.unified_effects.items():
            if effect.active and effect.effect_type == "condition":
                # Check if this condition can be removed by saving throw
                if effect.can_be_removed_by("saving_throw"):
                    combat_engine.check_condition_removal(self)
                    break

    def remove_condition(self, condition_name):
        """Removes the specified condition from the character and reverses its effects if the condition is active."""
        # Check if the condition exists in the unified effects system
        if condition_name in self.unified_effects:
            effect = self.unified_effects[condition_name]
            if effect.active:
                log_message(f"Removing {condition_name} from {self.name} and reversing its effects.")
                effect.remove(self)
                del self.unified_effects[condition_name]
                log_message(f"{condition_name} has been removed from {self.name} and its effects reversed.")
            else:
                log_message(f"{condition_name} is not active on {self.name}, skipping removal.")
        else:
            log_message(f"{self.name} does not have {condition_name}, skipping removal.")

    def apply_unified_effect(self, effect_name, effect_type, source, duration_type=EffectDuration.FIXED, 
                           duration_value=1, timing=EffectTiming.END_OF_TURN, 
                           attributes=None, stacking_rules=None, removal_conditions=None):
        """Apply a unified effect to the character."""
        # Check stacking rules
        if effect_name in self.unified_effects:
            existing_effect = self.unified_effects[effect_name]
            if existing_effect.active:
                # Handle stacking based on stacking rules
                if stacking_rules and stacking_rules.get("stack_type") == "extend":
                    # Extend duration
                    existing_effect.current_duration = max(existing_effect.current_duration, duration_value)
                    log_message(f"{effect_name} duration extended to {existing_effect.current_duration} rounds.")
                    return
                elif stacking_rules and stacking_rules.get("stack_type") == "replace":
                    # Remove existing effect and apply new one
                    existing_effect.remove(self)
                else:
                    # Default: don't stack
                    log_message(f"{effect_name} already active on {self.name}, not stacking.")
                    return
        
        # Create and apply new effect
        effect = UnifiedEffect(
            name=effect_name,
            effect_type=effect_type,
            source=source,
            duration_type=duration_type,
            duration_value=duration_value,
            timing=timing,
            attributes=attributes or {},
            stacking_rules=stacking_rules or {},
            removal_conditions=removal_conditions or {}
        )
        
        self.unified_effects[effect_name] = effect
        effect.apply(self)
        log_message(f"{effect_name} applied to {self.name}.")
        
    def apply_effect(self, effect_name, attribute, modifier, duration):
        """Legacy method for backward compatibility."""
        self.apply_unified_effect(
            effect_name=effect_name,
            effect_type="spell_effect",
            source="spell",
            duration_type=EffectDuration.FIXED,
            duration_value=duration,
            timing=EffectTiming.END_OF_TURN,
            attributes={attribute: modifier}
        )

    def remove_expired_effects(self):
        """Remove unified effects whose duration has expired."""
        expired_effects = []
        
        for effect_name, effect in self.unified_effects.items():
            if effect.active and effect.decrement_duration():
                # Effect has expired
                expired_effects.append(effect_name)
                
        # Remove expired effects
        for effect_name in expired_effects:
            effect = self.unified_effects[effect_name]
            effect.remove(self)
            del self.unified_effects[effect_name]
            log_message(f"Removed expired effect {effect_name} from {self.name}.")
            
    def process_effects_by_timing(self, timing):
        """Process effects based on their timing (start of turn, end of turn, etc.)."""
        for effect_name, effect in self.unified_effects.items():
            if effect.active and effect.timing == timing:
                # Process effect based on timing
                if timing == EffectTiming.START_OF_TURN:
                    # Effects that trigger at start of turn
                    log_message(f"{effect_name} triggers at start of {self.name}'s turn.")
                elif timing == EffectTiming.END_OF_TURN:
                    # Effects that trigger at end of turn
                    log_message(f"{effect_name} triggers at end of {self.name}'s turn.")
                    
    def get_active_effects(self):
        """Get all active effects on the character."""
        return {name: effect for name, effect in self.unified_effects.items() if effect.active}
        
    def has_effect(self, effect_name):
        """Check if character has a specific active effect."""
        return effect_name in self.unified_effects and self.unified_effects[effect_name].active


    
    def get_modifier(self, attribute):
        """Calculate the modifier for a given ability score dynamically."""
        score = getattr(self, attribute)
        return (score - 10) // 2

    def calculate_modifier(self, mod_type):
        """Calculate the modifier based on type (e.g., 'strength', 'spell')."""

        if mod_type == "strength":
            return self.get_modifier('strength')
        elif mod_type == "dexterity":
            return self.get_modifier('dexterity')
        elif mod_type == "constitution":
            return self.get_modifier('constitution')
        elif mod_type == "intelligence":
            return self.get_modifier('intelligence')
        elif mod_type == "wisdom":
            return self.get_modifier('wisdom')
        elif mod_type == "charisma":
            return self.get_modifier('charisma')
        elif mod_type == "spell":
            # Dynamic handling of spellcasting modifiers based on class
            if self.class_type == "wizard":
                return self.get_modifier('intelligence')
            elif self.class_type in ["sorcerer", "bard", "warlock"]:
                return self.get_modifier('charisma')
            elif self.class_type in ["cleric", "druid", "paladin", "ranger"]:
                return self.get_modifier('wisdom')
            else:
                return 0  # Default for non-spellcasting classes
        else:
            return 0  # Default for unknown modifier types

    def roll_initiative(self):
        """Rolls for initiative to determine the order of actions in combat."""
        self.initiative = d20.roll(f"1d20 + {self.dex_mod}").total
        log_message(f"{self.name} rolls {self.initiative} for initiative.")
        return self.initiative

    def take_damage(self, amount):
        """Reduces the character's HP by the damage amount and logs if defeated."""
        self.current_hp -= amount
        if self.hp < 0:
            self.hp = 0
    
    def is_alive(self):
        """Checks if the character is still alive (HP greater than 0)."""
        return self.current_hp > 0
    

    def decrement_effect_durations(self):
        """Reduces the duration of all active conditions by 1 round and removes expired conditions."""
        expired_conditions = []
        
        # Ensure conditions are stored as a dictionary
        if isinstance(self.conditions, dict):
            # Iterate over each condition and reduce the duration
            for condition_name, condition_info in self.conditions.items():
                condition_info['duration'] -= 1

                # If the condition duration reaches zero, mark it for removal
                if condition_info['duration'] <= 0:
                    expired_conditions.append(condition_name)

            # Remove expired conditions and reverse their effects
            for condition_name in expired_conditions:
                self.remove_condition(condition_name)

        else:
            log_message(f"Error 374: {self.name}'s conditions are not stored as a dictionary.")    

   
    def is_proficient_in_save(self, save):
        """Checks if the character is proficient in a specific saving throw (e.g., 'strength', 'dexterity')."""
        return save in self.proficient_saves  # Assuming `proficient_saves` is a list of save types the character is proficient in
    
    def saving_throw(self, target, save, dc, effect = None, adv_disadv="normal"):
        """
        Handles the saving throw for a target, applying proficiency if applicable.
        If a condition is provided, it attempts to remove that condition if the saving throw succeeds.
        """
        condition_name = effect
        # Get the appropriate ability modifier (e.g., str_mod, dex_mod)
        modifier = getattr(target, f"{save}_mod", 0)

        # Add proficiency bonus if the target's class grants proficiency in this save
        if save in target.proficient_saves:
            modifier += target.proficiency_bonus
            # log_message(f"DEBUG 358: profficiency bonus -> {target.proficiency_bonus}.")

        # Roll the saving throw with advantage/disadvantage if applicable
        save_roll = roll_with_advantage_disadvantage(modifier, adv_disadv)
        log_message(f"{target.name} rolls a saving throw: 1d20 ({save_roll.result}) + {modifier} ({adv_disadv}) against DC {dc}.")

        # Check if the saving throw was successful or failed
        if save_roll.total >= dc:
            # log_message(f"{target.name} succeeds on the saving throw!")

            # If the saving throw is linked to a condition, remove the condition
            if condition_name:
                log_message(f"[bold yellow]{target.name} successfully removes {condition_name}.[/bold yellow]")
                # Remove from unified_effects if present
                if condition_name in target.unified_effects:
                    effect = target.unified_effects[condition_name]
                    effect.remove(target)
                    del target.unified_effects[condition_name]
                    log_message(f"{condition_name} has been removed from {target.name} (unified effects).")
                # For backward compatibility, also update old conditions dict if present
                if condition_name in target.conditions:
                    target.conditions[condition_name]["active"] = False

            return True
        else:
            # log_message(f"{target.name} fails the saving throw!")
            return False

class PlayerCharacter(Character):
    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None, **kwargs):
        super().__init__(name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells, conditions, **kwargs)
        self.spells = spells
        self.conditions = conditions or {}

class NonPlayerCharacter(Character):
    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None, is_enemy=True, ai_type="aggressive", **kwargs):
        super().__init__(name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells, conditions, **kwargs)
        self.is_enemy = is_enemy
        self.ai_type = ai_type  # "aggressive", "healer", "support"

    
    def is_adjacent(self, action):
        """For now, consider all characters adjacent."""
        return True
    
    def get_allies(self, all_characters):
        """Get list of allies (other NPCs if enemy, or other players if friendly)."""
        if self.is_enemy:
            return [char for char in all_characters if isinstance(char, NonPlayerCharacter) and char != self]
        else:
            return [char for char in all_characters if isinstance(char, PlayerCharacter)]
    
    def get_enemies(self, all_characters):
        """Get list of enemies."""
        if self.is_enemy:
            return [char for char in all_characters if isinstance(char, PlayerCharacter)]
        else:
            return [char for char in all_characters if isinstance(char, NonPlayerCharacter)]
    
    def has_healing_spells(self):
        """Check if this NPC has healing spells."""
        if not self.spells:
            return False
        return any(spell.get('type') == 'healing' for spell in self.spells)
    
    def has_condition_removal_spells(self):
        """Check if this NPC has condition removal spells."""
        if not self.spells:
            return False
        return any(spell.get('effect', {}).get('attribute') == 'condition_removal' for spell in self.spells)
    
    def has_buff_spells(self):
        """Check if this NPC has buff spells."""
        if not self.spells:
            return False
        return any(spell.get('type') == 'buff' for spell in self.spells)
    
    def find_ally_needing_healing(self, allies):
        """Find an ally that needs healing (below 50% HP)."""
        for ally in allies:
            if ally.is_alive() and ally.current_hp < (ally.hp * 0.5):
                return ally
        return None
    
    def find_ally_with_conditions(self, allies):
        """Find an ally with active conditions that can be removed."""
        for ally in allies:
            if ally.is_alive() and ally.unified_effects:
                return ally
        return None
    
    def find_ally_needing_buffs(self, allies):
        """Find an ally that could benefit from buffs."""
        for ally in allies:
            if ally.is_alive() and not ally.unified_effects:
                return ally
        return None
            
    def decide_action(self, action, all_characters=None):
        """Enhanced AI to decide what action to take based on AI type and conditions."""
        if not all_characters:
            all_characters = []
        
        # Check if stunned/incapacitated
        if self.has_effect('stunned') or self.has_effect('incapacitated'):
            log_message(f"{self.name} is stunned/incapacitated and cannot act this turn.")
            return None
        
        # Healer AI logic
        if self.ai_type == "healer":
            return self._healer_ai_logic(all_characters)
        
        # Support AI logic (buffs and condition removal)
        elif self.ai_type == "support":
            return self._support_ai_logic(all_characters)
        
        # Default aggressive AI logic
        else:
            return self._aggressive_ai_logic(all_characters)
    
    def _healer_ai_logic(self, all_characters):
        """Healer AI prioritizes healing and condition removal."""
        allies = self.get_allies(all_characters)
        
        # Priority 1: Heal critically wounded allies
        if self.has_healing_spells():
            wounded_ally = self.find_ally_needing_healing(allies)
            if wounded_ally:
                healing_spell = next(spell for spell in self.spells if spell.get('type') == 'healing')
                log_message(f"{self.name} (Healer) decides to heal {wounded_ally.name}.")
                return {"type": "cast_spell", "spell": healing_spell, "target": [wounded_ally]}
        
        # Priority 2: Remove conditions from allies
        if self.has_condition_removal_spells():
            conditioned_ally = self.find_ally_with_conditions(allies)
            if conditioned_ally:
                removal_spell = next(spell for spell in self.spells 
                                  if spell.get('effect', {}).get('attribute') == 'condition_removal')
                log_message(f"{self.name} (Healer) decides to remove conditions from {conditioned_ally.name}.")
                return {"type": "cast_spell", "spell": removal_spell, "target": [conditioned_ally]}
        
        # Priority 3: Buff allies
        if self.has_buff_spells():
            unbuffed_ally = self.find_ally_needing_buffs(allies)
            if unbuffed_ally:
                buff_spell = next(spell for spell in self.spells if spell.get('type') == 'buff')
                log_message(f"{self.name} (Healer) decides to buff {unbuffed_ally.name}.")
                return {"type": "cast_spell", "spell": buff_spell, "target": [unbuffed_ally]}
        
        # Fallback: Attack enemies
        return self._aggressive_ai_logic(all_characters)
    
    def _support_ai_logic(self, all_characters):
        """Support AI focuses on buffs and condition removal."""
        allies = self.get_allies(all_characters)
        
        # Priority 1: Remove conditions from allies
        if self.has_condition_removal_spells():
            conditioned_ally = self.find_ally_with_conditions(allies)
            if conditioned_ally:
                removal_spell = next(spell for spell in self.spells 
                                  if spell.get('effect', {}).get('attribute') == 'condition_removal')
                log_message(f"{self.name} (Support) decides to remove conditions from {conditioned_ally.name}.")
                return {"type": "cast_spell", "spell": removal_spell, "target": [conditioned_ally]}
        
        # Priority 2: Buff allies
        if self.has_buff_spells():
            unbuffed_ally = self.find_ally_needing_buffs(allies)
            if unbuffed_ally:
                buff_spell = next(spell for spell in self.spells if spell.get('type') == 'buff')
                log_message(f"{self.name} (Support) decides to buff {unbuffed_ally.name}.")
                return {"type": "cast_spell", "spell": buff_spell, "target": [unbuffed_ally]}
        
        # Priority 3: Heal if available
        if self.has_healing_spells():
            wounded_ally = self.find_ally_needing_healing(allies)
            if wounded_ally:
                healing_spell = next(spell for spell in self.spells if spell.get('type') == 'healing')
                log_message(f"{self.name} (Support) decides to heal {wounded_ally.name}.")
                return {"type": "cast_spell", "spell": healing_spell, "target": [wounded_ally]}
        
        # Fallback: Attack enemies
        return self._aggressive_ai_logic(all_characters)
    
    def _aggressive_ai_logic(self, all_characters):
        """Default aggressive AI logic."""
        enemies = self.get_enemies(all_characters)
        alive_enemies = [enemy for enemy in enemies if enemy.is_alive()]
        
        if not alive_enemies:
            return None
        
        # Choose weakest enemy
        target = min(alive_enemies, key=lambda e: e.current_hp)
        chosen_weapon = self.inventory[0] if self.inventory else None
        
        if chosen_weapon:
            log_message(f"{self.name} (Aggressive) decides to attack {target.name}.")
            return {"type": "attack", "target": target, "weapon": chosen_weapon}
        
        return None

    
# Legacy Effect class removed - replaced by UnifiedEffect

# Combat Engine Class
class CombatEngine:
    def __init__(self, players, npcs, debug_mode=DEBUG_MODE):
        self.players = players
        self.npcs = npcs
        self.initiative_order = []
        self.round_number = 0
        self.debug_mode = debug_mode
        self.max_rounds = None  # For testing - limit combat rounds

    def determine_initiative(self):
        all_characters = self.players + self.npcs
        for character in all_characters:
            character.roll_initiative()
        self.initiative_order = sorted(all_characters, key=lambda x: x.initiative, reverse=True)
        # initiative_list = self.initiative_order
        # log_message(f"\n--- Initiative Order - - -\n {initiative_list()}")

    def start_combat(self):
        log_message(f"\n[bold cyan]--- Combat Begins --- [/bold cyan]")
        self.determine_initiative()
        while not self.is_combat_over():
            self.round_number += 1
            log_message(f"[bold yellow]--- Round {self.round_number}: Start!---[/bold yellow]")
            for character in self.initiative_order:
                if character.is_alive():
                    self.take_turn(character)
            self.end_round()
            
            # Check if we've reached max rounds (for testing)
            if self.max_rounds and self.round_number >= self.max_rounds:
                log_message(f"[bold cyan]--- Combat ended after {self.round_number} rounds (test limit). ---[/bold cyan]")
                break

        # End of combat message
        log_message(f"\n[bold cyan]--- Combat has ended after {self.round_number} rounds. ---[/bold cyan]")
        console.print("[bold magenta]Thank you for playing! Exiting combat engine...[/bold magenta]")

    def take_turn(self, character):
        """Handles the turn logic for a character."""
        # Check if combat is already over before taking the turn
        if self.is_combat_over():
            return
        # Check if the character can act at all
        if not self.check_action_restrictions(character, "take_turn"):
            log_message(f"{character.name} is unable to act due to conditions like 'stunned' or 'paralyzed'.")
            character.decrement_conditions(self)  # Decrement conditions after skipping the turn
            return  # Skip the turn if the character cannot act

        # Movement logic (only if the character can move)
        if not self.check_action_restrictions(character, "move"):
            log_message(f"{character.name} is restricted from moving due to conditions.")

        
        # Attack logic (only if the character can attack)
        if not self.check_action_restrictions(character, "attack"):
            log_message(f"{character.name} is restricted from attacking due to conditions.")

            # Attack logic can be handled here if applicable

        # Saving throw logic (if the character can make saving throws this turn)
        if not self.check_action_restrictions(character, "saving_throw"):
            log_message(f"{character.name} is restricted from making saving throws due to condition {self.conditions}.")

            # Saving throw logic can be handled here if applicable
        # log_message(f"DEBUG 540: about to take turn.")
        # Handle player or NPC-specific actions
        if isinstance(character, PlayerCharacter):
            self.handle_player_turn(character)
        else:
            self.handle_npc_turn(character)

        # Process effects based on timing (end of turn)
        character.process_effects_by_timing(EffectTiming.END_OF_TURN)
        
        # Decrement condition durations after the character's turn
        log_message(f"{character.name}'s turn ends. Conditions & effects updated.")
        character.decrement_conditions(self)


    def check_condition_removal(self, character):
        """
        Check if conditions can be removed via saving throws, contested checks, or spells.
        """
        # log_message(f"YOU'VE ARRIVED AT CHECK_CONDITION_REMOVAL")
        conditions_to_update = []

        # Iterate over the character's conditions
        for condition_name, condition_info in character.conditions.items():
            # log_message(f"DEBUG 546: condition_info: {condition_name}, {condition_info}")

            # Skip conditions that are not active
            if not condition_info.get("active"):

                continue

            if condition_name in CONDITIONS_DICT:
                removal_info = CONDITIONS_DICT[condition_name].get("removal", {})

                # Check if the condition can be removed by saving throw
                if "saving_throw" in removal_info.get("removable_by", []):
                    save_info = removal_info.get("saving_throw", {})
                    save_attr = save_info.get("attribute")
                    save_dc = save_info.get("dc")

                    # Ensure save attribute and DC are present before performing saving throw
                    if save_attr and save_dc is not None:
                        log_message(f"{character.name} attempting saving throw for {condition_name}, DC {save_dc}.")
                        save_success = character.saving_throw(character, save_attr, int(save_dc))

                        if save_success:
                            log_message(f"[bold yellow]{character.name} succeeds on the saving throw (DC {save_dc}) and removes {condition_name}.[/bold yellow]")
                            conditions_to_update.append(condition_name)
                        else:
                            log_message(f"{character.name} fails the saving throw (DC {save_dc}) and {condition_name} persists.")

                # Check if the condition can be removed by contested check
                if "contested" in removal_info.get("removable_by", []):
                    contested_check_info = removal_info.get("contested_check", {})
                    contested_attr = contested_check_info.get("attribute")

                    if contested_attr:
                        # log_message(f"DEBUG: {character.name} attempting contested check for {condition_name}.")
                        contested_success = self.perform_contested_check(character, contested_attr)

                        if contested_success:
                            log_message(f"[bold yellow]{character.name} succeeds on the contested check and removes {condition_name}.[/bold yellow]")
                            conditions_to_update.append(condition_name)
                        else:
                            log_message(f"{character.name} fails the contested check and {condition_name} persists.")

                # Check if the condition can be removed by spell
                if "spell_removal" in removal_info.get("removable_by", []):
                    # Placeholder for spell-based condition removal logic
                    log_message(f"{condition_name} can be removed by spells such as {removal_info['spell_removal']}.")

        # Update the conditions that were successfully removed
        for condition in conditions_to_update:
            character.conditions[condition]["active"] = False
            character.conditions[condition]["duration"] = 0
            log_message(f"{condition} has been set to inactive for {character.name}.")



    def check_action_restrictions(self, character, action_type):
        """
        Checks if the character is restricted from performing an action based on their unified effects.
        """
        # Check unified effects for action restrictions
        for effect_name, effect in character.unified_effects.items():
            if not effect.active:
                continue
                
            # Check action restrictions based on effect attributes
            if action_type == "take_turn" and effect.attributes.get("actions") == "none":
                log_message(f"{character.name} is affected by {effect_name} and cannot act this turn.")
                return False  # Action is blocked

            # Check if movement is restricted
            if action_type == "move" and effect.attributes.get("movement") == "none":
                log_message(f"{character.name} is affected by {effect_name} and cannot move.")
                return False  # Movement is blocked

            # Check for specific conditions that block attacks
            if action_type == "attack" and effect.attributes.get("attack_roll") == "none":
                log_message(f"{character.name} is affected by {effect_name} and cannot attack.")
                return False  # Attack is blocked

            # Check for spell casting restrictions
            if action_type == "cast_spell" and effect.attributes.get("spell_casting") == "none":
                log_message(f"{character.name} is affected by {effect_name} and cannot cast spells.")
                return False  # Spell casting is blocked

        return True  # No restrictions, action is allowed


    def handle_player_turn(self, player):
        """Handles the player's turn and checks if they can perform actions."""
        action = self.get_player_action(player)
        
        # Check if the player is allowed to perform the chosen action (e.g., attack, move, cast spell)
        if action["type"] == "attack" and not self.check_action_restrictions(player, "attack"):
            log_message(f"{player.name} is restricted from attacking due to conditions like 'stunned'.")
            return  # Skip the action if restricted

        if action["type"] == "move" and not self.check_action_restrictions(player, "move"):
            log_message(f"{player.name} is restricted from moving due to conditions like 'grappled'.")
            return  # Skip the movement if restricted

        # If no restrictions, execute the action
        self.execute_action(player, action)


    def get_player_action(self, player):
        """Prompts the player to choose an action and returns the chosen action."""
        console.print(f"\n{player.name}'s turn with {player.current_hp} HP!")
        console.print("1. Attack")
        action_options = ["attack"]
        option_number = 2
        if player.spells and len(player.spells) > 0:
            console.print(f"{option_number}. Cast a Spell")
            action_options.append("cast_spell")
            option_number += 1
        console.print(f"{option_number}. Move")
        action_options.append("move")

        action_choice = input("Enter the number of your action: ")
        try:
            action_choice_int = int(action_choice)
        except (ValueError, TypeError):
            action_choice_int = 1  # Default to Attack

        if action_choice_int < 1 or action_choice_int > len(action_options):
            action_choice_int = 1  # Default to Attack

        chosen_action = action_options[action_choice_int - 1]

        if chosen_action == "attack":
            return self.handle_attack_action(player)
        elif chosen_action == "cast_spell":
            return self.handle_spell_action(player)
        elif chosen_action == "move":
            return self.handle_move_action(player)
        else:
            console.print("Invalid choice, defaulting to Attack.")
            return self.handle_attack_action(player)

    def handle_attack_action(self, player):
        """Handle the attack action selection and weapon choice."""
        while True:
            console.print("Choose a weapon:")
            for i, weapon in enumerate(player.inventory):
                console.print(f"{i + 1}. {weapon['name']} ({weapon['type']} - Damage: {weapon.get('damage', 'None')})")
            console.print(f"{len(player.inventory) + 1}. On second thought...")
            
            weapon_choice = input("Enter the number of the weapon you want to use: ")
            try:
                weapon_choice = int(weapon_choice)
            except (ValueError, TypeError):
                weapon_choice = 1
            
            if weapon_choice == len(player.inventory) + 1:
                # User wants to go back
                return self.get_player_action(player)
            
            if 1 <= weapon_choice <= len(player.inventory):
                chosen_weapon = player.inventory[weapon_choice - 1]
                target = self.choose_target(player, self.npcs)
                return {"type": "attack", "target": target, "weapon": chosen_weapon}
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")

    def handle_spell_action(self, player):
        """Handle the spell casting action selection."""
        while True:
            console.print("Choose a spell:")
            for i, spell in enumerate(player.spells, start=1):
                console.print(f"{i}. {spell['name']}")
            console.print(f"{len(player.spells) + 1}. On second thought...")
            
            spell_choice = input("Enter the number of the spell you want to cast: ")
            try:
                spell_choice = int(spell_choice)
            except (ValueError, TypeError):
                spell_choice = 1
            
            if spell_choice == len(player.spells) + 1:
                # User wants to go back
                return self.get_player_action(player)
            
            if 1 <= spell_choice <= len(player.spells):
                spell = player.spells[spell_choice - 1]
                # Determine target based on the spell's targeting type
                if spell['targeting'] == "aoe":
                    target = self.npcs  # All NPCs are affected by the AOE spell
                    log_message(f"{spell['name']} affects all NPCs!")
                elif spell['targeting'] == "self":
                    target = [player]  # The actor is the only target
                else:  # 'single'
                    target = [self.choose_target(player, self.npcs, spell)]
                return {"type": "cast_spell", "spell": spell, "target": target}
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")

    def handle_move_action(self, player):
        """Handle the move action (placeholder for now)."""
        console.print(f"{player.name} moves! (Movement system not yet implemented)")
        console.print("This is a placeholder for the future movement system.")
        return {"type": "move"}

    def choose_target(self, actor, targets_list, spell=None, is_attack=True, attack_type="melee"):
        # Filter valid targets based on whether they are alive
        valid_targets = [target for target in targets_list if target.is_alive()]

        if spell:
            # Handle spell targeting
            if spell['targeting'] == "self":
                valid_targets = [actor]  # Only the actor can be targeted
            elif spell['targeting'] == "single":
                if spell['type'] == 'healing' or spell['type'] == 'buff':
                    # Healing and buff spells target only alive allies
                    valid_targets = [target for target in self.players if target.is_alive()]
                else:
                    # Damage or debuff spells target only alive enemies
                    valid_targets = [target for target in self.npcs if target.is_alive()]
            elif spell['targeting'] == "area":
                valid_targets = self.choose_aoe_targets(actor, valid_targets, spell)
        # Handle attack targeting (melee and ranged)
        elif is_attack:
            if attack_type == "melee":
                # Only enemies within melee range are valid
                valid_targets = [target for target in valid_targets if target.is_enemy and target.is_adjacent(actor)]
            elif attack_type == "ranged":
                # Can target distant enemies
                valid_targets = [target for target in valid_targets if target.is_enemy and target.is_in_range(actor)]

        # Display the valid targets for selection
        for i, target in enumerate(valid_targets):
            console.print(f"{i + 1}. {target.name} (HP: {target.current_hp})")
  
        # Get user input to select the target
        choice = int(input("Enter the number of your target: ")) - 1
        return valid_targets[choice] if 0 <= choice < len(valid_targets) else valid_targets[0]

    def cast_spell(self, actor, spell, targets_list=None):
        """Cast a spell with comprehensive logging."""
        
        log_message(f"[bold cyan]{actor.name} begins casting {spell['name']}...[/bold cyan]")
        
        # Apply advantage or disadvantage only for attack roll spells
        adv_disadv = getattr(actor, 'adv_disadv', 'normal')
        
        # Determine the correct modifier for spells based on the actor's class
        spell_mod = actor.calculate_modifier('spell')
        log_message(f"{actor.name} uses {actor.class_type} spellcasting modifier: {spell_mod}")

        # Handle spell targeting "self"
        if spell['targeting'] == "self":
            targets_list = [actor]
            log_message(f"{spell['name']} targets {actor.name} (self-targeting spell).")

        # Handle spell targeting a single target (enemy or ally)
        elif spell['targeting'] == "single":
            if targets_list is None:
                # Healing, buff, or debuff spells should target allies
                if spell['type'] in ['healing', 'buff']:
                    log_message(f"{spell['name']} is a beneficial spell - selecting an ally target.")
                    targets_list = [actor] + self.players  # Target allies and actor
                else:
                    # Damage or debuff spells target enemies (NPCs)
                    log_message(f"{spell['name']} is a harmful spell - selecting an enemy target.")
                    targets_list = [self.choose_target(actor, self.npcs, spell)]

        # Handle AOE spells
        elif spell['targeting'] == "aoe":
            log_message(f"{spell['name']} is an area-of-effect spell targeting all enemies.")
            targets_list = [t for t in self.npcs if t.is_alive()]

        # Filter out defeated targets
        targets_list = [t for t in targets_list if t.is_alive()]
        if not targets_list:
            log_message(f"No valid targets for {spell['name']}.")
            return
            
        log_message(f"{spell['name']} will affect: {[t.name for t in targets_list]}")

        # Handle attack roll-based damage spells (e.g., Firebolt, Eldritch Blast)
        if spell.get('damage') and spell.get('save') is None:
            attack_roll = roll_with_advantage_disadvantage(spell_mod, adv_disadv)

            for target in targets_list:
                if attack_roll.total >= target.ac:
                    damage_roll = d20.roll(spell['damage'])
                    log_message(f"{actor.name} rolls a {attack_roll.result} ({adv_disadv}) to hit {target.name}'s AC of {target.ac} with the {spell['name']} spell.")
                    log_message(f"The spell hits! {actor.name} rolls a {spell['damage']} for a total damage of {damage_roll.total}.")
                    log_message(f"{target.name} takes {damage_roll.total} damage.")
                    target.take_damage(damage_roll.total)
                else:
                    log_message(f"{actor.name} rolls a {attack_roll.result} ({adv_disadv}) to hit {target.name}'s AC of {target.ac} with the {spell['name']} spell.")
                    log_message(f"{target.name} dodges {spell['name']}!")
                self.check_target_status(target)

        # Handle saving throw-based damage spells (e.g., Fireball)
        elif spell.get('damage') and spell.get('save'):
            damage_roll = d20.roll(spell['damage'])
            log_message(f"{actor.name} rolls {spell['damage']} for a total of damage of {damage_roll}!")
            for target in targets_list:
                if target.saving_throw(target, spell['save'], spell['dc']):
                    half_damage = damage_roll.total // 2
                    log_message(f"{target.name} succeeds on saving throw, taking half damage: {half_damage}.")
                    target.take_damage(half_damage)
                else:
                    log_message(f"{target.name} fails saving throw, taking full damage: {damage_roll.total}.")
                    target.take_damage(damage_roll.total)
                    
                    # Apply condition effect if the spell has one
                    if spell.get('effect'):
                        effect_data = spell['effect']
                        condition_name = effect_data['modifier']
                        duration = effect_data.get('duration', 1)
                        log_message(f"[bold yellow]Applying {condition_name} to {target.name} for {duration} round(s).[/bold yellow]")
                        target.apply_condition_with_effects(condition_name, duration, spell)
                        log_message(f"[bold yellow]{actor.name} successfully cast {spell['name']} on {target.name}![/bold yellow]")
                        
                self.check_target_status(target)

        # Handle healing spells
        elif spell.get('healing'):
            healing_roll = d20.roll(spell['healing'])
            log_message(f"{actor.name} rolls {healing_roll.result} for healing.")
            for target in targets_list:
                target.current_hp = min(target.current_hp + healing_roll.total, target.hp)  # Ensure HP doesn't exceed max
                log_message(f"{target.name} is healed for {healing_roll.total} HP and now has {target.current_hp} HP.")

        # Handle condition spells (e.g., stunning)
        elif spell['type'] == 'condition':
            effect_data = spell['effect']
            condition_name_in_spell = effect_data['modifier']  # The condition being applied (e.g., 'stunned')
            
            log_message(f"[bold magenta]Processing condition spell: {spell['name']} applies {condition_name_in_spell}[/bold magenta]")

            for target in targets_list:
                log_message(f"Attempting to apply {condition_name_in_spell} to {target.name}...")
                
                # Check for saving throw if specified in the spell
                if 'save' in spell:
                    log_message(f"{target.name} must make a {spell['save']} saving throw (DC {spell['dc']}) to resist {condition_name_in_spell}.")
                    if target.saving_throw(target, spell['save'], spell['dc'], spell['effect']['modifier']):
                        log_message(f"[bold green]{target.name} succeeds on the saving throw and avoids {condition_name_in_spell}![/bold green]")
                        continue  # Skip applying the condition if the saving throw succeeds
                    else:
                        log_message(f"[bold red]{target.name} fails the saving throw and is affected by {condition_name_in_spell}.[/bold red]")

                duration = effect_data.get('duration', 1)  # Default to 1 round if duration isn't specified
                log_message(f"[bold yellow]Applying {condition_name_in_spell} to {target.name} for {duration} round(s).[/bold yellow]")
                target.apply_condition_with_effects(condition_name_in_spell, duration, spell)
                log_message(f"[bold yellow]{actor.name} successfully cast {spell['name']} on {target.name}![/bold yellow]")

        # Handle condition removal spells (e.g., Lesser Restoration, Greater Restoration)
        elif spell['type'] == 'utility' and spell.get('effect', {}).get('attribute') == 'condition_removal':
            effect_data = spell['effect']
            removal_type = effect_data['modifier']  # 'remove_one' or 'remove_all'
            
            log_message(f"[bold magenta]Processing condition removal spell: {spell['name']} ({removal_type})[/bold magenta]")
            
            for target in targets_list:
                if removal_type == 'remove_one':
                    # Remove one condition (the first one found)
                    if target.unified_effects:
                        effect_name = list(target.unified_effects.keys())[0]
                        effect = target.unified_effects[effect_name]
                        effect.remove(target)
                        del target.unified_effects[effect_name]
                        log_message(f"[bold yellow]{actor.name} cast {spell['name']} on {target.name}, removing {effect_name}.[/bold yellow]")
                    else:
                        log_message(f"{target.name} has no conditions to remove.")
                        
                elif removal_type == 'remove_all':
                    # Remove all conditions
                    removed_effects = list(target.unified_effects.keys())
                    for effect_name in removed_effects:
                        effect = target.unified_effects[effect_name]
                        effect.remove(target)
                        del target.unified_effects[effect_name]
                    
                    if removed_effects:
                        log_message(f"[bold yellow]{actor.name} cast {spell['name']} on {target.name}, removing all conditions: {removed_effects}[/bold yellow]")
                    else:
                        log_message(f"{target.name} has no conditions to remove.")

        # Handle utility spells (like Blinding Light, Charm Person, etc.)
        elif spell['type'] == 'utility':
            effect_data = spell['effect']
            condition_name_in_spell = effect_data['modifier']  # The condition being applied (e.g., 'blinded')
            
            log_message(f"[bold magenta]Processing utility spell: {spell['name']} applies {condition_name_in_spell}[/bold magenta]")

            for target in targets_list:
                log_message(f"Attempting to apply {condition_name_in_spell} to {target.name}...")
                
                # Check for saving throw if specified in the spell
                if 'save' in spell:
                    log_message(f"{target.name} must make a {spell['save']} saving throw (DC {spell['dc']}) to resist {condition_name_in_spell}.")
                    if target.saving_throw(target, spell['save'], spell['dc'], spell['effect']['modifier']):
                        log_message(f"[bold green]{target.name} succeeds on the saving throw and avoids {condition_name_in_spell}![/bold green]")
                        continue  # Skip applying the condition if the saving throw succeeds
                    else:
                        log_message(f"[bold red]{target.name} fails the saving throw and is affected by {condition_name_in_spell}.[/bold red]")

                duration = effect_data.get('duration', 1)  # Default to 1 round if duration isn't specified
                log_message(f"[bold yellow]Applying {condition_name_in_spell} to {target.name} for {duration} round(s).[/bold yellow]")
                target.apply_condition_with_effects(condition_name_in_spell, duration, spell)
                log_message(f"[bold yellow]{actor.name} successfully cast {spell['name']} on {target.name}![/bold yellow]")

        # Handle buff spells (e.g., granting advantage, increasing AC)
        elif spell['type'] == 'buff':
            effect_data = spell['effect']
            spell_name = spell['name']
            attribute = effect_data['attribute']  # The attribute being affected (e.g., 'adv_disadv', 'ac')
            modifier = effect_data['modifier']  # The value being applied (e.g., 'advantage', +2)
            duration = effect_data.get('duration', 1)  # Default to 1 round if not specified

            log_message(f"[bold magenta]Processing buff spell: {spell['name']} modifies {attribute} by {modifier}[/bold magenta]")

            for target in targets_list:
                target.apply_effect(spell['name'], attribute, modifier, duration)
                log_message(f"[bold yellow]{actor.name} cast buff {spell['name']} on {target.name}: {attribute} is modified by {modifier} for {duration} round(s).[/bold yellow]")
                log_message(f"{target.name} is now affected by the buff for {duration} rounds.")

        # Handle debuff spells (e.g., granting disadvantage, decreasing AC)
        elif spell['type'] == 'debuff':
            effect_data = spell['effect']
            attribute = effect_data['attribute']  # The attribute being affected (e.g., 'adv_disadv', 'ac')
            modifier = effect_data['modifier']  # The value being applied (e.g., 'disadvantage', -2)
            duration = effect_data.get('duration', 1)  # Default to 1 round if not specified

            log_message(f"[bold magenta]Processing debuff spell: {spell['name']} modifies {attribute} by {modifier}[/bold magenta]")

            for target in targets_list:
                target.apply_effect(spell['name'], attribute, modifier, duration)
                log_message(f"[bold yellow]{actor.name} cast {spell['name']} on {target.name} debuffing it with {modifier} for {duration} round(s).[/bold yellow]")
                log_message(f"{target.name} is now affected by the debuff for {duration} rounds.")
   
    def attack(self, actor, target, weapon, adv_disadv=None, two_handed=False):
        """Handles the attack action, ensuring only alive targets are attacked and applying damage."""
    
        # Check for valid inputs
        if not actor or not target or not weapon:
            console.print("[red]Error: Invalid actor, target, or weapon.[/red]")
            console.print(f"Error: Actor {actor}")
            console.print(f"Error: Target {target}")
            console.print(f"Error: Weapon {weapon}")
            return

        if not target.is_alive():
            log_message(f"{target.name} is already defeated and cannot be attacked.")
            return

        # Determine the attack modifier
        if weapon.get('finesse'):
            # Automatically choose the higher modifier between Strength and Dexterity for finesse weapons
            attack_mod = max(actor.calculate_modifier('strength'), actor.calculate_modifier('dexterity'))
        else:
            # Use the weapon's specified modifier (defaulting to strength if not specified)
            attack_mod = actor.calculate_modifier(weapon.get('mod', 'strength'))

        # Handle versatile weapons (use two-handed damage if specified)
        if weapon.get('versatile') and two_handed:
            # Use versatile damage die (typically larger)
            weapon_damage = f"1d{weapon['versatile']}"
        else:
            # Use the standard damage die for the weapon
            weapon_damage = weapon['damage']

        # Apply interaction effects (advantage/disadvantage, automatic critical hits) from unified effects on the target
        for effect_name, effect in target.unified_effects.items():
            if effect.active:  # Check if the effect is active
                if effect_name in CONDITIONS_DICT:
                    interaction_effects = CONDITIONS_DICT[effect_name]["interaction_effects"]

                    # Check for advantage or disadvantage on attack rolls against the target
                    if interaction_effects["attack_roll_against"] == "advantage":
                        log_message(f"[bold green]Attackers have advantage when attacking {target.name} due to {effect_name}.[/bold green]")
                        adv_disadv = "advantage"
                    elif interaction_effects["attack_roll_against"] == "disadvantage":
                        log_message(f"[bold red]Attackers have disadvantage when attacking {target.name} due to {effect_name}.[/bold red]")
                        adv_disadv = "disadvantage"

        # Check for self-effects that affect the actor's attack rolls
        for effect_name, effect in actor.unified_effects.items():
            if effect.active:  # Check if the effect is active
                if effect_name in CONDITIONS_DICT:
                    self_effects = CONDITIONS_DICT[effect_name]["self_effects"]
                    
                    # Check if the actor has disadvantage on attack rolls due to a condition
                    if self_effects.get("attack_roll") == "disadvantage":
                        log_message(f"[bold red]{actor.name} has disadvantage on attack rolls due to {effect_name}.[/bold red]")
                        adv_disadv = "disadvantage"
                    elif self_effects.get("attack_roll") == "advantage":
                        log_message(f"[bold green]{actor.name} has advantage on attack rolls due to {effect_name}.[/bold green]")
                        adv_disadv = "advantage"

        # Roll to hit with advantage, disadvantage, or normally
        if not adv_disadv:
            adv_disadv = getattr(actor, 'adv_disadv', 'normal')  # Check if the actor has an advantage or disadvantage buff

        # log_message(f"DEBUG ATTACK 925: actor's adv_disadv -> {adv_disadv}")
        attack_roll = roll_with_advantage_disadvantage(attack_mod, adv_disadv)
        log_message(f"attack_roll -> {attack_roll} = attack_mod -> {attack_mod}, adv_disadv -> {adv_disadv}")

        # Check if the roll is valid
        if not attack_roll:
            console.print("[red]Error: Attack roll failed.[/red]")
            return

        # Log the attack roll and modifiers
        log_message(f"{actor.name} attacks {target.name} with {weapon['name']} ({adv_disadv}).")

        log_message(f"{actor.name} rolls ({attack_roll.result}) ({adv_disadv}) to hit {target.name} (AC {target.ac}).")

        # Handle automatic critical hit based on unified effects on the target
        critical_hit = False
        for effect_name, effect in target.unified_effects.items():
            if effect.active:  # Ensure only active effects apply
                if effect_name in CONDITIONS_DICT:
                    interaction_effects = CONDITIONS_DICT[effect_name]["interaction_effects"]

                    # Apply automatic critical hit if the condition allows it (e.g., Paralyzed within 5 feet)
                    if interaction_effects["critical_hit"] == "yes" and actor.is_within_melee_range(target):
                        log_message(f"{actor.name} automatically scores a critical hit on {target.name} due to {effect_name}.")
                        critical_hit = True

        # Handle critical hit from natural 20 or condition-based automatic crit
        if attack_roll.result == 20 or critical_hit:
            log_message(f"CRITICAL HIT! {actor.name} rolls 1d20 ({attack_roll.result}) (Critical Hit)!")
            damage_roll = d20.roll(f"2 * {weapon_damage} + {attack_mod}")
            # log_message(f"DEBUG 1033: Critical hit damage_roll -> {damage_roll}")
            total_damage = damage_roll.total
            target.take_damage(total_damage)
            log_message(f"{actor.name} hits {target.name} with {weapon['name']} for {damage_roll.result} damage!")
            self.check_target_status(target)

        # Handle critical failure
        elif attack_roll.result == 1:
            log_message(f"CRITICAL MISS! {actor.name} rolls 1d20 ({attack_roll.result}) (Critical Miss)!")
        
        # Handle regular hit
        elif attack_roll.total >= target.ac:
            damage_roll = d20.roll(f"{weapon_damage} + {attack_mod}")
            total_damage = damage_roll.total
            target.take_damage(total_damage)
            log_message(f"[bold yellow]{actor.name} hits {target.name} with {weapon['name']} for {damage_roll.result} damage![/bold yellow]")
            self.check_target_status(target)

        # Handle miss
        else:
            log_message(f"{actor.name} misses {target.name} with {weapon['name']}!")


    def choose_aoe_target(self, actor, target, spell):
        """Handles the selection of targets for area-of-effect (AOE) spells."""
        # Assuming all NPCs are in range, select all NPCs as targets for AOE spells
        aoe_radius = spell.get('radius', None)  # Optional: Implement radius logic in the future
        if aoe_radius:
            log_message(f"{spell['name']} affects NPCs within a {aoe_radius} ft radius!")
            # You could later add logic here to filter based on distance from actor if needed
        else:
            log_message(f"{spell['name']} affects all NPCs!")

        # Return all valid NPC target in the area of effect
        return [target for target in target if target.is_alive()]

    def choose_spell(self, actor):
        """Prompts the player to choose a spell to cast."""
        console.print("Choose a spell:")
        for i, spell in enumerate(actor.spells):
            console.print(f"{i + 1}. {spell['name']}")
        spell_choice = int(input("Enter the number of the spell you want to cast: ")) - 1

        if 0 <= spell_choice < len(actor.spells):
            return actor.spells[spell_choice]
        else:
            console.print("[red]Invalid choice, defaulting to the first spell.[/red]")
            return actor.spells[0]

    def handle_npc_turn(self, npc):
        """Determines the action of an NPC on their turn."""
        if not npc.is_alive():
            return

        # Get all characters for AI decision making
        all_characters = self.players + self.npcs
        
        # Use the new AI system
        action = npc.decide_action(None, all_characters)
        
        if action is None:
            log_message(f"{npc.name} cannot act this turn.")
            return
        
        # Execute the chosen action
        if action["type"] == "attack":
            self.attack(npc, action["target"], action["weapon"])
        elif action["type"] == "cast_spell":
            self.cast_spell(npc, action["spell"], action["target"])
        else:
            log_message(f"{npc.name} performs {action['type']} action.")

    def choose_weakest_player(self, players):
        """Selects the player with the lowest HP as the target for NPC attacks, only considering alive players."""
        alive_players = [player for player in players if player.is_alive()]
        
        if not alive_players:
            return None  # If no players are alive, return None
        
        if len(alive_players) == 1:
            return alive_players[0]  # If only one player is alive, return that player
        
        return min(alive_players, key=lambda player: player.current_hp)


    def remove_from_initiative(self, character):
        """Removes a defeated character from the initiative order."""
        if character in self.initiative_order:
            self.initiative_order.remove(character)
            log_message(f"{character.name} has been removed from the initiative order.")

    def check_target_status(self, target):
        """Checks if the target is alive and handles status accordingly."""
        if not target.is_alive():
            log_message(f"[bold red]{target.name} has been defeated!")
            self.remove_from_initiative(target)  # Removes from initiative
        else: 
            log_message(f"{target.name}'s HP is now {target.current_hp}.")

    def execute_action(self, character, action):
        """Executes the action chosen by the player or NPC."""
        # Checks for action restriction conditions
        if not self.check_action_restrictions(character, action["type"]):
            log_message(f"{character.name} is restricted from performing {action['type']} due to conditions.")
            return
        # Executes actions
        if action["type"] == "attack":
            self.attack(character, action["target"], action["weapon"])
        elif action["type"] == "cast_spell":
            self.cast_spell(character, action["spell"],  action["target"])
        elif action["type"] == "move":
            log_message(f"{character.name} moves! (Movement system not yet implemented)")

    def perform_contested_check(self, character, ability):
        """
        Perform a contested ability check for grapples, etc.
        Example: Grappled vs Grappler's Strength check.
        """

        # Assuming you want to contest against another character's ability
        # Use the existing ability modifier directly (str_mod, dex_mod, etc.)
        modifier = getattr(character, f"{ability}_mod", 0)  # This gets the correct modifier for the ability

        opposing_roll = d20.roll(f"1d20 + {modifier}")
        log_message(f"{character.name} rolls contested {ability} check: {opposing_roll.total}")
        
        return opposing_roll.total  # This would depend on how you want to handle contested rolls

    def is_combat_over(self):
        """Check if either all players or all NPCs are defeated."""
        all_players_defeated = not any(player.is_alive() for player in self.players)
        all_npcs_defeated = not any(npc.is_alive() for npc in self.npcs)

        if all_players_defeated:
            log_message("[bold red]All players have been defeated![/bold red] The combat has ended.")
            return True

        if all_npcs_defeated:
            log_message("[bold green]All NPCs have been defeated![/bold green] The players are victorious.")
            return True

        return False

    def end_round(self):
        """
        Called at the end of each round to handle condition decrement and possible removal.
        """
        log_message(f"[bold yellow]--- End Of Round {self.round_number} ---[/bold yellow]")
        # for character in self.initiative_order:
        #     if character.is_alive():

        #         # Check if any conditions can be removed via saving throws or spells
        #         self.check_condition_removal(character)
                
        # Increment round number for the next round
        
        # log_message(f"Round {self.round_number} begins.")


# Loading Characters from JSON
def load_characters_from_json(file_path):
    with open(file_path, 'r') as file:
        game_state = json.load(file)
    
    players = [PlayerCharacter(**pc) for pc in game_state['players']]
    npcs = [NonPlayerCharacter(**npc) for npc in game_state['npcs']]
    
    return players, npcs
# Main Execution
if __name__ == "__main__":
    players, npcs = load_characters_from_json('game_state_test.json')
    engine = CombatEngine(players, npcs)
    engine.start_combat()
    

