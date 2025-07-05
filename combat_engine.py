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

# Load the action restrictions from a file
# Load conditions from the new conditions_apply.json file
def load_conditions(filepath="conditions/conditions_apply.json"):
    with open(filepath, 'r') as file:
        return json.load(file)

# Example usage
CONDITIONS_DICT = load_conditions()


def log_message(message):
    console.print(message)

def roll_with_advantage_disadvantage(modifier, adv_disadv="normal"):
    """Rolls with advantage, disadvantage, or normally."""
    if adv_disadv == "advantage":
        roll_1 = d20.roll(f"1d20 + {modifier}")
        roll_2 = d20.roll(f"1d20 + {modifier}")
        # log_message(f"DEBUG 44 adv_disadv {adv_disadv} rolls: roll_1 {roll_1}, roll_2 {roll_2}.")
        return max(roll_1, roll_2, key=lambda roll: roll.total)
    elif adv_disadv == "disadvantage":
        roll_1 = d20.roll(f"1d20 + {modifier}")
        roll_2 = d20.roll(f"1d20 + {modifier}")
        # log_message(f"DEBUG 44 adv_disadv {adv_disadv} rolls: roll_1 {roll_1}, roll_2 {roll_2}.")
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

class Character:
    """Base class for all characters (players and NPCs) in the game."""

    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None, speed=30, effects=None):
        # log_message(f"DEBUG: conditions passed to init: {conditions}")  # Check the value of conditions passed

        self.name = name
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
            # Convert conditions from integer format to dictionary format if needed
            self.conditions = {}
            for condition_name, condition_value in conditions.items():
                if isinstance(condition_value, int):
                    self.conditions[condition_name] = {"active": True, "duration": condition_value}
                elif isinstance(condition_value, dict):
                    self.conditions[condition_name] = condition_value
                else:
                    self.conditions[condition_name] = {"active": False, "duration": 0}
            # Ensure all conditions are in dictionary format
            for condition_name in list(self.conditions.keys()):
                if not isinstance(self.conditions[condition_name], dict):
                    self.conditions[condition_name] = {"active": False, "duration": 0}
        
        # log_message(f"DEBUG: self.conditions after initialization: {self.conditions}")


        self.effects = {}
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
            # Default to a generic class for NPCs if not found
            self.proficient_saves = []
            self.spellcasting_mod = "intelligence"
            log_message(f"Warning: Class type {self.class_type} is not valid, defaulting to generic class settings.")

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

        # Apply the condition's effects using the Effect class
        self_effects = condition_data.get("self_effects", {})
        if self_effects:
            for attribute, modifier in self_effects.items():
                # Apply attribute modifiers using the Effect class
                effect = Effect(name=condition_name, attribute=attribute, modifier=modifier, duration=duration)
                effect.apply(self)
                log_message(f"{condition_name} applies {modifier} to {attribute} for {self.name}.")
        else:
            log_message(f"{condition_name} has no self effects for {self.name}.")

        log_message(f"{self.name} is now affected by {condition_name} for {duration} rounds.")

    def decrement_conditions(self, combat_engine):
        """
        Decrement the duration of each condition on the character, and check if any conditions 
        can be removed via saving throws or other mechanisms.
        """
        # conditions_to_update = []

        # Iterate over the conditions currently applied to the character
        for condition_name, condition_instance in self.conditions.items():
            # log_message(f"DEBUG 182: condition_instance: {condition_name}, {condition_instance}")

            if not condition_instance["active"]:
                # Skip conditions that are not active
                continue
            log_message(f"{self.name} skips their action due to being {condition_name}")
            # Fetch the global condition data from CONDITIONS_DICT
            log_message(f"Decrementing condition: {condition_name} with duration: {condition_instance.get('duration', 0)}")
            # log_message(f"DEBUG 191: condition_instance: {condition_name}, {condition_instance}")
            condition_data = CONDITIONS_DICT.get(condition_name)
            if not condition_data:
                continue  # Skip invalid conditions

            duration_info = condition_data.get("duration", {})  # Fetch the duration type from the global data
            removal_data = condition_data.get("removal", {})

            # Handle fixed duration (e.g., 3 rounds)
            if duration_info.get("type") == "fixed":
                # Decrement the instance-specific duration
                condition_instance['duration'] -= 1
                console.print(f"[yellow]{condition_name} on {self.name} has {condition_instance['duration']} round(s) remaining.[/yellow]")

                # Mark the condition to update if its duration reaches 0
                if condition_instance['duration'] <= 0:
                    console.print(f"[yellow]Condition {condition_name} has expired for {self.name}.[/yellow]")
                    self.remove_condition(condition_name)  # Use remove_condition method instead of inline logic


            # Handle variable duration (e.g., 1d4 rounds)
            elif duration_info.get("type") == "variable":
                if "duration" in condition_instance:
                    condition_instance['duration'] -= 1
                    console.print(f"[yellow]{condition_name} on {self.name} has {condition_instance['duration']} round(s) remaining.[/yellow]")

                    # Mark the condition to update if the duration reaches 0
                    if condition_instance['duration'] <= 0:
                        self.remove_condition(condition_name)  # Use remove_condition method instead of inline logic
                else:
                    # If no value is present, roll for the duration (e.g., 1d4)
                    rolled_duration = d20.roll(duration_info["value"]).total
                    condition_instance['duration'] = rolled_duration
                    log_message(f"{condition_name} on {self.name} lasts {rolled_duration} round(s).")

            # Handle conditions that last until removed by other means
            elif duration_info.get("type") == "until_removed":
                log_message(f"{condition_name} on {self.name} remains until removed by other means.")

            # Handle conditions that can be removed by saving throws or contested checks
            if "saving_throw" in removal_data:
                combat_engine.check_condition_removal(self)  # Centralize saving throw check to avoid duplication

    def remove_condition(self, condition_name):
        """Removes the specified condition from the character and reverses its effects if the condition is active."""
        # Check if the condition exists in the character's conditions list
        if condition_name in self.conditions:
            # Ensure the condition is active before attempting to remove it
            if self.conditions[condition_name]["active"]:
                log_message(f"Removing {condition_name} from {self.name} and reversing its effects.")
                # Fetch condition data from CONDITIONS_DICT
                condition_data = CONDITIONS_DICT.get(condition_name)
                if condition_data:
                    self_effects = condition_data.get('self_effects', {})
                    # Reverse each effect using the Effect class
                    for attribute, modifier in self_effects.items():
                        effect = Effect(name=condition_name, attribute=attribute, modifier=modifier, duration=0)
                        effect.remove(self)

                # Mark the condition as inactive and reset its duration
                self.conditions[condition_name] = {"active": False, "duration": 0}
                log_message(f"{condition_name} has been removed from {self.name} and its effects reversed.")
            # else:
                # log_message(f"{condition_name} is not active on {self.name}, skipping removal.")
        else:
            log_message(f"{self.name} does not have {condition_name}, skipping removal.")

    def apply_effect(self, effect_name, attribute, modifier, duration):
        # Ensure modifier is an integer to avoid type issues
        modifier_value = int(modifier) if isinstance(modifier, str) and modifier.isdigit() else modifier
        effect = Effect(effect_name, attribute, modifier_value, duration)
        self.effects[effect_name] = effect
        log_message(f"DEBUG: Applying effect {effect_name} to {self.name}. Target attribute: {attribute}, Modifier: {modifier}, Duration: {duration}")
        effect.apply(self)  # Apply the effect to the character
        current_value = getattr(self, attribute, 0) if attribute in self.stats else "N/A"
        log_message(f"DEBUG: Effect {effect_name} applied to {self.name}. {attribute} modified by {modifier}. Current value: {current_value}, stats dictionary value: {self.stats.get(attribute, 'N/A')}")

    def update_status_effects(self, current_round, caster_initiative=None):
        """
        Update all status effects (conditions and effects), decrement durations based on D&D 5e timing rules,
        remove expired ones, and log updates. Effects are tracked with respect to rounds and initiative order.
        
        Args:
            current_round: The current round number in combat.
            caster_initiative: The initiative position of the caster (used to determine expiration timing).
        """
        # Handle conditions
        expired_conditions = []
        for condition_name, condition_instance in self.conditions.items():
            if not condition_instance["active"]:
                continue
            # Decrement condition duration at the start of the affected character's turn
            condition_instance['duration'] -= 1
            console.print(f"[yellow]{condition_name} on {self.name} has {condition_instance['duration']} round(s) remaining.[/yellow]")
            if condition_instance['duration'] <= 0:
                expired_conditions.append(condition_name)
                console.print(f"[yellow]Condition {condition_name} has expired for {self.name}.[/yellow]")

        for condition_name in expired_conditions:
            self.remove_condition(condition_name)

        # Handle effects
        for effect_name, effect in list(self.effects.items()):
            if isinstance(effect, Effect):
                log_message(f"DEBUG: Updating effect {effect_name} for {self.name}. Current duration: {effect.duration}")
                # Decrement effect duration at the start of the affected character's turn
                effect.decrement_duration()
                log_message(f"DEBUG: Effect {effect_name} for {self.name} after decrement: New duration = {effect.duration}")
                if effect.duration <= 0:
                    log_message(f"DEBUG: Effect {effect_name} expired for {self.name}. Removing effect.")
                    effect.remove(self)
                    del self.effects[effect_name]
                    console.print(f"[yellow]{effect_name} has expired for {self.name}.[/yellow]")
                else:
                    console.print(f"[yellow]{effect_name} on {self.name} has {effect.duration} round(s) remaining.[/yellow]")
            else:
                log_message(f"Error: {effect_name} is not an Effect instance.")


    
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
        console.print(f"[white]{self.name} rolls [blue]{self.initiative}[/blue] for initiative.[/white]")
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
        """Deprecated: Use update_status_effects instead. Kept for backward compatibility."""
        log_message(f"Warning: decrement_effect_durations is deprecated. Use update_status_effects for {self.name}.")
        self.update_status_effects()
   
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
                target.conditions[condition_name]["active"] = False

            return True
        else:
            # log_message(f"{target.name} fails the saving throw!")
            return False

class PlayerCharacter(Character):
    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None):
        super().__init__(name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells, conditions)

        self.spells = spells
        self.conditions = conditions or {}

class NonPlayerCharacter(Character):
    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, race="unknown", spells=None, conditions=None, is_enemy=True):
        super().__init__(name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells, conditions)
        self.is_enemy = is_enemy
        self.race = race

    
    def is_adjacent(self, action):
        """For now, consider all characters adjacent."""
        return True
            
    def decide_action(self, action):
        # Basic AI to decide what action to take based on conditions, target, etc.
        if 'stunned' in self.conditions:
            log_message(f"{self.name} is stunned and cannot act this turn.")
            return None
        
        # # Logic to handle different actions based on 'action'
        # if action == ActionType.ATTACK and 'paralyzed' not in self.conditions:
        #     return ActionType.ATTACK
        # elif action == ActionType.CAST_SPELL and 'silenced' not in self.conditions:
        #     return ActionType.CAST_SPELL
        # else:
        #     # Handle other conditions or actions
        #     return ActionType.DEFEND  # Fallback action

    
class Effect:
    def __init__(self, name, attribute, modifier, duration):
        self.name = name
        self.attribute = attribute
        self.modifier = modifier
        self.duration = duration
        # log_message(f"YOU'VE ARRIVED AT EFFECT CLASS")

    def apply(self, character):
        """Applies the effect to the character."""
        # log_message(f"APPLY: Applying {self.name} to {character.name}: {self.attribute} -> {self.modifier}")
        # log_message(f"DEBUG 445: self -> {self.attribute}, {self.modifier}, {self.duration}")
        # log_message(f"DEBUG 445: self.stats -> {character.stats}")

        # Handle advantage/disadvantage effects
        if self.attribute == "adv_disadv":
            # log_message(f"DEBUG 426 APPLY: self.attribute {self.attribute}, character.attribute {character.attribute}")
            # log_message(f"DEBUG 426 APPLY: self.attribute {self.attribute}")
            setattr(character, self.attribute, self.modifier)
            log_message(f"{character.name} now has {self.modifier} on advantage/disadvantage.")
        
        # Handle movement restrictions (e.g., 'none' disables movement)
        elif self.attribute == "movement" and self.modifier == "none":
            character.movement = 0
            log_message(f"{character.name} is now unable to move due to {self.name}.")
        
        # Handle action restrictions
        elif self.attribute == "actions" and self.modifier == "none":
            character.check_action_restrictions = False
            log_message(f"APPLY: {character.name} is now unable to act due to {self.name}.")
        
        
        # Handle general numerical modifiers
        elif self.attribute in character.stats:
            current_value = getattr(character, self.attribute, 0)
            modifier_value = int(self.modifier) if isinstance(self.modifier, str) else self.modifier
            new_value = current_value + modifier_value
            log_message(f"DEBUG: Before setting {self.attribute} for {character.name}: Current value = {current_value}")
            setattr(character, self.attribute, new_value)
            # Update the stats dictionary to maintain consistency
            character.stats[self.attribute] = new_value
            log_message(f"DEBUG: After setting {self.attribute} for {character.name}: New value = {new_value}, stats dictionary updated to {character.stats.get(self.attribute, 'N/A')}")
            log_message(f"APPLY: {self.name} modifies {self.attribute} by {modifier_value} for {character.name}. New value: {new_value}")

    def remove(self, character):
        """Reverses the effect on the character."""
        # log_message(f"Removing effect: {self.name} from {character.name}")
        
        # Handle advantage/disadvantage effects
        if self.attribute == "adv_disadv":
            setattr(character, self.attribute, "normal")
            log_message(f"{character.name}'s advantage/disadvantage reset to normal.")

        # Handle movement restoration
        elif self.attribute == "movement" and self.modifier == "none":
            character.movement = character.default_movement
            log_message(f"{character.name}'s movement restored to {character.default_movement}.")

        # Handle action restoration
        elif self.attribute == "actions" and self.modifier == "none":
            character.check_action_restrictions = True  # Assuming `True` means actions are allowed
            log_message(f"{character.name} is now able to act again.")

        # Handle numerical modifiers
        elif self.attribute in character.stats:
            current_value = getattr(character, self.attribute, 0)
            modifier_value = int(self.modifier) if isinstance(self.modifier, str) else self.modifier
            new_value = current_value - modifier_value
            log_message(f"DEBUG: Before reversing {self.attribute} for {character.name}: Current value = {current_value}")
            setattr(character, self.attribute, new_value)
            # Update the stats dictionary to maintain consistency
            character.stats[self.attribute] = new_value
            log_message(f"DEBUG: After reversing {self.attribute} for {character.name}: New value = {new_value}, stats dictionary updated to {character.stats.get(self.attribute, 'N/A')}")
            log_message(f"REMOVE: {self.name} reverses modification of {self.attribute} by {modifier_value} for {character.name}. New value: {new_value}")

        # elif self in self.effects:
        #     effect_data = self.effects[self]
        #     effect = Effect(self, effect_data['attribute'], effect_data['modifier'], effect_data['duration'])
        #     effect.remove(self)  # Reverse the effect on the character
        #     log_message(f"Removed {self} from {self.name}.")
        #     del self.effects[self]  # Remove from effects dictionary

    def is_numeric_modifier(self):
        """Checks if the modifier is a numeric value (can be an integer)."""
        return self.modifier.isdigit() or (self.modifier.startswith('-') and self.modifier[1:].isdigit())

    def decrement_duration(self):
        """Reduces the duration of the effect by 1 round."""
        self.duration -= 1
        log_message(f"Duration of {self.name} decreased to {self.duration} rounds.")

# Combat Engine Class
class CombatEngine:
    def __init__(self, players, npcs):
        self.players = players
        self.npcs = npcs
        self.initiative_order = []
        self.round_number = 0

    def determine_initiative(self):
        all_characters = self.players + self.npcs
        for character in all_characters:
            character.roll_initiative()
        self.initiative_order = sorted(all_characters, key=lambda x: x.initiative, reverse=True)
        # Display initiative order in a cleaner way
        console.print("[blue]--- Initiative Order ---[/blue]")
        for character in self.initiative_order:
            console.print(f"[white]{character.name}: [blue]{character.initiative}[/blue][/white]")

    def start_combat(self):
        log_message(f"\n[blue]--- Combat Begins --- [/blue]")
        self.determine_initiative()
        while not self.is_combat_over():
            self.round_number += 1
            log_message(f"[blue]--- Round {self.round_number}: Start!---[/blue]")
            for character in self.initiative_order:
                if character.is_alive():
                    self.take_turn(character)
            self.end_round()

        # End of combat message
        log_message(f"\n[blue]--- Combat has ended after {self.round_number} rounds. ---[/blue]")
        console.print("[magenta]Thank you for playing! Exiting combat engine...[/magenta]")

    def take_turn(self, character):
        """Handles the turn logic for a character, updating status effects at the start of the turn."""
        # Update all status effects (conditions and effects) at the start of the character's turn for D&D 5e compliance
        console.print(f"[blue]--- {character.name}'s turn begins. Conditions & effects updated. ---[/blue]")
        character.update_status_effects(self.round_number)
        # Also check for condition removal via saving throws or other mechanisms
        self.check_condition_removal(character)

        # Check if the character can act at all
        if not self.check_action_restrictions(character, "take_turn"):
            log_message(f"{character.name} is unable to act due to conditions like 'stunned' or 'paralyzed'.")
            return  # Skip the turn if the character cannot act

        # Movement logic (only if the character can move)
        if not self.check_action_restrictions(character, "move"):
            log_message(f"{character.name} is restricted from moving due to conditions.")

        # Attack logic (only if the character can attack)
        if not self.check_action_restrictions(character, "attack"):
            log_message(f"{character.name} is restricted from attacking due to conditions.")

        # Saving throw logic (if the character can make saving throws this turn)
        if not self.check_action_restrictions(character, "saving_throw"):
            log_message(f"{character.name} is restricted from making saving throws due to conditions.")

        # Handle player or NPC-specific actions
        if isinstance(character, PlayerCharacter):
            self.handle_player_turn(character)
        else:
            self.handle_npc_turn(character)

        console.print(f"[blue]--- {character.name}'s turn ends. ---[/blue]")


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
        Checks if the character is restricted from performing an action based on their conditions.
        References the new conditions_apply.json file for restrictions.
        """
        # log_message(f"CHECK_ACTION_RESTRICTION:")
        
        # Iterate through each condition affecting the character
        for condition_name, condition_instance in character.conditions.items():
            # log_message(f"DEBUG 588: condition_instance: {condition_name}, {condition_instance}")

            # Ensure condition_instance is a dictionary before accessing
            if not isinstance(condition_instance, dict):
                log_message(f"Warning: Condition {condition_name} for {character.name} is not in dictionary format, converting.")
                character.conditions[condition_name] = {"active": False, "duration": 0}
                condition_instance = character.conditions[condition_name]
            
            # Skip conditions that are not active
            if not condition_instance.get("active", False):
                # log_message(f"DEBUG: {condition_name} is not active, skipping.")
                continue

            if condition_name in CONDITIONS_DICT:
                # Get the global condition data from CONDITIONS
                condition_data = CONDITIONS_DICT[condition_name]["self_effects"]

                # Check action restrictions based on condition's self_effects
                if action_type == "take_turn" and condition_data.get("actions", "normal") == "none":
                    # log_message(f"DEBUG 592: action_type {action_type}, condition data {condition_data.get('name')}")
                    # log_message(f"DEBUG 593: {character.name} is affected by {condition_name} and cannot act this turn.")
                    return False  # Action is blocked

                # Check if movement is restricted
                if action_type == "move" and condition_data.get("movement", "normal") == "0":
                    log_message(f"{character.name} is affected by {condition_name} and cannot move.")
                    return False  # Movement is blocked

                # Check for specific conditions that block attacks (e.g., "stunned")
                if action_type == "attack" and condition_data.get("attack_roll", "normal") == "none":
                    log_message(f"{character.name} is stunned and cannot attack.")
                    return False  # Attack is blocked

                # Additional checks can be added here for other action types (e.g., saving throws, casting spells)

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
        console.print(f"[white]\n{player.name}'s turn with [blue]{player.current_hp} HP[/blue]![/white]")
        console.print("[white]1. Attack[/white]")
        console.print("[white]2. Cast a Spell[/white]")
        console.print("[white]3. Defend (placeholder action)[/white]")
        action_choice = input("Enter the number of your action: ")

        if action_choice == "1":
            console.print("Choose a weapon:")
            for i, weapon in enumerate(player.inventory):
                console.print(f"[white]{i + 1}. {weapon['name']} ({weapon['type']} - Damage: {weapon['damage']})[/white]")
            weapon_choice = int(input("Enter the number of the weapon you want to use: ")) - 1

            if 0 <= weapon_choice < len(player.inventory):
                chosen_weapon = player.inventory[weapon_choice]
            else:
                console.print("[white]Invalid choice, defaulting to the first weapon.[/white]")
                chosen_weapon = player.inventory[0]

            target = self.choose_target(player, self.npcs)  # Select target after weapon is chosen

            return {"type": "attack", "target": target, "weapon": chosen_weapon}

        elif action_choice == "2":
            # Choose a spell
            console.print("Choose a spell:")
            for i, spell in enumerate(player.spells, start=1):
                console.print(f"[white]{i}. {spell['name']}[/white]")
            spell_choice = int(input("Enter the number of the spell you want to cast: ")) - 1

            if 0 <= spell_choice < len(player.spells):
                spell = player.spells[spell_choice]
            else:
                console.print("[white]Invalid spell choice, defaulting to the first spell.[/white]")
                spell = player.spells[0]

            # Determine target based on the spell's targeting type and effect
            if spell['targeting'] == "aoe":
                target = self.npcs  # All NPCs are affected by the AOE spell
                log_message(f"{spell['name']} affects all NPCs!")
            elif spell['targeting'] == "self":
                target = [player]  # The actor is the only target
                log_message(f"{spell['name']} targets {player.name} (self).")
                return {"type": "cast_spell", "spell": spell, "target": target}
            elif spell['targeting'] == "single":
                # Check if the spell is a buff or healing to target allies, otherwise target enemies
                if spell.get('type') in ["buff", "healing"] or (spell.get('effect', {}).get('type') in ['buff', 'healing']):
                    target = [self.choose_target(player, self.players, spell)]
                    console.print(f"[white]{spell['name']} targets an ally.[/white]")
                else:
                    target = [self.choose_target(player, self.npcs, spell)]
                    console.print(f"[white]{spell['name']} targets an enemy.[/white]")
            else:
                target = [self.choose_target(player, self.npcs, spell)]
            
            return {"type": "cast_spell", "spell": spell, "target": target}

        elif action_choice == "3":
            console.print(f"[white]{player.name} defends![/white]")
            return {"type": "defend"}

        else:
            console.print("[white]Invalid choice, defaulting to Attack.[/white]")
            return {"type": "attack", "target": self.choose_target(player, self.npcs), "weapon": player.inventory[0]}

    def choose_target(self, actor, targets, spell=None):
        """Prompts the player to choose a target from a list of possible targets."""
        console.print("Choose a target:")
        for i, target in enumerate(targets):
            if target.is_alive():
                console.print(f"[white]{i + 1}. {target.name} (HP: {target.current_hp})[/white]")
        target_choice = int(input("Enter the number of the target: ")) - 1

        if 0 <= target_choice < len(targets) and targets[target_choice].is_alive():
            return targets[target_choice]
        else:
            console.print("[white]Invalid target choice, defaulting to the first available target.[/white]")
            for target in targets:
                if target.is_alive():
                    return target
            return None  # If no targets are alive, return None

    def handle_npc_turn(self, npc):
        """Handles the NPC's turn based on AI logic."""
        if not npc.is_alive():
            log_message(f"{npc.name} is defeated and cannot act.")
            return

        console.print(f"[white]{npc.name}'s turn with [blue]{npc.current_hp} HP[/blue]![/white]")
        action = self.get_npc_action(npc)
        if action:
            self.execute_action(npc, action)

    def get_npc_action(self, npc):
        """Determines the NPC's action based on AI logic."""
        if not self.check_action_restrictions(npc, "take_turn"):
            log_message(f"{npc.name} is unable to act due to conditions.")
            return None

        # Simple AI: prioritize attacking a player
        for player in self.players:
            if player.is_alive():
                # Check if NPC can attack
                if self.check_action_restrictions(npc, "attack"):
                    return {"type": "attack", "target": player, "weapon": npc.inventory[0]}
        
        # If no players are alive or can't attack, do nothing
        log_message(f"{npc.name} takes no action.")
        return {"type": "defend"}

    def execute_action(self, actor, action):
        """Executes the chosen action for the actor."""
        if action["type"] == "attack":
            target = action["target"]
            weapon = action["weapon"]
            if target and target.is_alive():
                console.print(f"[white]{actor.name} attacks {target.name} with {weapon['name']}.[/white]")
                self.resolve_attack(actor, target, weapon)
            else:
                log_message(f"No valid target for {actor.name}'s attack.")

        elif action["type"] == "cast_spell":
            spell = action["spell"]
            targets = action["target"]
            log_message(f"{actor.name} casts {spell['name']}.")
            self.resolve_spell(actor, targets, spell)
            # Add descriptive message for spell effects
            if 'effect' in spell and spell['effect']:
                effect_data = spell['effect']
                effect_type = effect_data.get('type', spell.get('type'))
                if effect_type in ['buff', 'debuff']:
                    attribute = effect_data.get('attribute')
                    modifier = effect_data.get('modifier')
                    duration = effect_data.get('duration')
                    console.print(f"[yellow]{spell['name']} effect: Increases {attribute} by {modifier} for {duration} round(s).[/yellow]")
                elif effect_type == 'condition':
                    condition_name = effect_data['condition']
                    duration = effect_data['duration']
                    console.print(f"[yellow]{spell['name']} effect: Applies {condition_name} for {duration} round(s).[/yellow]")

        elif action["type"] == "defend":
            log_message(f"{actor.name} takes a defensive stance.")

    def resolve_attack(self, attacker, target, weapon):
        """Resolves an attack action with advantage/disadvantage based on conditions."""
        attack_mod = 0
        weapon_type = weapon['type']
        if weapon_type == "melee":
            attack_mod = attacker.str_mod
            log_message(f"DEBUG: Weapon 'type' is 'melee' for {weapon['name']}, using strength modifier: {attack_mod}")
        elif weapon_type == "ranged":
            attack_mod = attacker.dex_mod
            log_message(f"DEBUG: Weapon 'type' is 'ranged' for {weapon['name']}, using dexterity modifier: {attack_mod}")
        else:
            log_message(f"DEBUG: Weapon 'type' is '{weapon_type}' for {weapon['name']}, defaulting to no modifier")
        
        # Log the current adv_disadv state for debugging
        log_message(f"DEBUG: Before attack roll for {attacker.name}: adv_disadv attribute = {attacker.adv_disadv}, stats dictionary adv_disadv = {attacker.stats.get('adv_disadv', 'N/A')}")
        attack_roll = roll_with_advantage_disadvantage(attack_mod, attacker.adv_disadv)
        log_message(f"DEBUG: Attack roll made with adv_disadv parameter = {attacker.adv_disadv}")
        # Use the current AC directly from the target's stats, which already includes effect modifications
        current_ac = target.ac
        log_message(f"DEBUG: Calculating AC for {target.name}. Current AC: {current_ac}, stats dictionary AC: {target.stats.get('ac', 'N/A')}")
        log_message(f"DEBUG: Active effects on {target.name}: {[(name, eff.attribute, eff.modifier, eff.duration) for name, eff in target.effects.items() if isinstance(eff, Effect)]}")
        log_message(f"DEBUG: Final calculated AC for {target.name}: {current_ac} (already includes effect modifications)")
        console.print(f"[white]{attacker.name} rolls to hit: 1d20 ({attack_roll.result}) + {attack_mod} = {attack_roll.total} vs AC {current_ac}[/white]")

        if attack_roll.total >= current_ac:
            damage_roll = d20.roll(weapon['damage'])
            total_damage = damage_roll.total + attack_mod
            console.print(f"[red]Hit! {attacker.name} deals {total_damage} damage to {target.name}. (Damage Roll: {damage_roll.result} + {attack_mod})[/red]" if isinstance(target, PlayerCharacter) else f"[green]Hit! {attacker.name} deals {total_damage} damage to {target.name}. (Damage Roll: {damage_roll.result} + {attack_mod})[/green]")
            target.take_damage(total_damage)
            console.print(f"[yellow]{target.name} now has {target.current_hp} HP remaining.[/yellow]" if isinstance(target, NonPlayerCharacter) else f"[red]{target.name} now has {target.current_hp} HP remaining.[/red]")
            if not target.is_alive():
                console.print(f"[bold red]{target.name} is defeated![/bold red]")
        else:
            console.print(f"[gray]{attacker.name} misses {target.name}.[/gray]")

    def resolve_spell(self, caster, targets, spell):
        """
        Resolves a spell action by determining its type and applying the appropriate effects to the targets.
        This method handles various spell effects such as buffs, debuffs, conditions, damage, and healing.
        
        Args:
            caster: The character casting the spell.
            targets: List of target characters affected by the spell.
            spell: Dictionary containing spell data and effects.
        """
        # Log the spell casting action with target names for clarity
        console.print(f"[magenta]{caster.name} casts {spell['name']} targeting {', '.join([t.name for t in targets])}.[/magenta]")
        
        # Extract effect data and type from spell dictionary, handling nested or top-level structures
        effect_data, effect_type = self._extract_spell_effect_data(spell)
        
        # Handle different spell effect types using dedicated helper methods for clarity
        if effect_type in ['buff', 'debuff']:
            # Apply stat modifications like AC or strength buffs/debuffs
            self._apply_buff_debuff_effect(caster, targets, spell, effect_data)
        elif effect_type == 'condition':
            # Apply status conditions like stunned or poisoned
            self._apply_condition_effect(caster, targets, spell, effect_data)
        elif effect_type == 'damage':
            # Apply damage effects with potential saving throws for reduction
            self._apply_damage_effect(caster, targets, spell, effect_data)
        elif effect_type == 'healing':
            # Apply healing effects to restore HP
            self._apply_healing_effect(caster, targets, spell)
        else:
            # Fallback for spells without a defined effect type or unsupported types
            console.print(f"[white]{spell['name']} has no recognized effect type defined.[/white]")
            log_message(f"DEBUG: Unrecognized effect type {effect_type} for {spell['name']}. No effect applied.")

    def _extract_spell_effect_data(self, spell):
        """
        Extracts effect data and type from the spell dictionary, handling both nested and top-level structures.
        
        Args:
            spell: Dictionary containing spell data.
            
        Returns:
            tuple: (effect_data, effect_type) where effect_data is the dictionary of effect details,
                   and effect_type is the determined type of the spell effect.
        """
        # Check if spell has a nested 'effect' key with detailed data
        if 'effect' in spell and spell['effect']:
            effect_data = spell['effect']
            effect_type = effect_data.get('type', spell.get('type', 'unknown'))
            log_message(f"DEBUG: Spell 'type' from effect_data or spell: '{effect_type}' for {spell['name']}")
            log_message(f"DEBUG: Effect data for {spell['name']}: {effect_data}")
        else:
            # Fallback to top-level spell attributes if no nested effect data exists
            effect_data = {}
            effect_type = spell.get('type', 'unknown')
            log_message(f"DEBUG: Spell 'type' from top-level spell: '{effect_type}' for {spell['name']}")
            log_message(f"DEBUG: No effect data found for {spell['name']}, using top-level spell attributes")
        return effect_data, effect_type

    def _apply_buff_debuff_effect(self, caster, targets, spell, effect_data):
        """
        Applies buff or debuff effects to modify target attributes like AC or strength.
        
        Args:
            caster: The character casting the spell.
            targets: List of target characters to apply the effect to.
            spell: Dictionary containing spell data.
            effect_data: Dictionary containing effect details like attribute and modifier.
        """
        # Extract effect details for buff/debuff application
        attribute = effect_data.get('attribute')
        modifier = effect_data.get('modifier')
        duration = effect_data.get('duration')
        
        # Handle modifier based on attribute type; adv_disadv uses string values, others need numeric
        if attribute == 'adv_disadv':
            modifier_value = modifier  # Keep as string for advantage/disadvantage
        else:
            modifier_value = int(modifier) if isinstance(modifier, (str, float)) and str(modifier).replace('-', '').isdigit() else modifier
        log_message(f"DEBUG: Preparing to apply {spell['name']} effect. Attribute: {attribute}, Modifier: {modifier_value} (original: {modifier}), Duration: {duration}")
        
        # Apply the effect to each living target
        for target in targets:
            if target.is_alive():
                console.print(f"[yellow]Applying {spell['name']} effect to {target.name} for {duration} rounds. This modifies {attribute} by {modifier_value}.[/yellow]")
                log_message(f"DEBUG: Before applying effect {spell['name']} to {target.name}: Base {attribute} = {getattr(target, attribute, 'N/A')}")
                # Apply the effect using the target's method, which updates stats directly
                target.apply_effect(spell['name'], attribute, modifier_value, duration)
                log_message(f"DEBUG: After applying effect {spell['name']} to {target.name}: Updated {attribute} = {getattr(target, attribute, 'N/A')}, stats dictionary {attribute} = {target.stats.get(attribute, 'N/A')}")
                log_message(f"DEBUG: Effect {spell['name']} applied immediately. No additional status update needed as apply_effect modifies state directly.")

    def _apply_condition_effect(self, caster, targets, spell, effect_data):
        """
        Applies condition effects like stunned or poisoned to targets.
        
        Args:
            caster: The character casting the spell.
            targets: List of target characters to apply the condition to.
            spell: Dictionary containing spell data.
            effect_data: Dictionary containing condition details.
        """
        # Extract condition details for application
        condition_name = effect_data['condition']
        duration = effect_data['duration']
        
        # Apply condition to each living target, considering saving throws if defined
        for target in targets:
            if target.is_alive():
                console.print(f"[yellow]Applying {condition_name} to {target.name} for {duration} rounds.[/yellow]")
                # Apply condition with potential saving throw logic embedded in the method
                target.apply_condition_with_effects(condition_name, duration, spell)

    def _apply_damage_effect(self, caster, targets, spell, effect_data):
        """
        Applies damage effects to targets, considering saving throws for damage reduction.
        
        Args:
            caster: The character casting the spell.
            targets: List of target characters to apply damage to.
            spell: Dictionary containing spell data.
            effect_data: Dictionary containing damage details.
        """
        # Determine damage expression from effect data or top-level spell data
        damage_expr = effect_data.get('damage', spell.get('damage'))
        if damage_expr:
            damage = d20.roll(damage_expr).total
            damage_type = effect_data.get('damage_type', spell.get('damage_type', 'unknown'))
            console.print(f"[green]{spell['name']} deals {damage} {damage_type} damage.[/green]")
        else:
            damage = 0
            console.print(f"[white]{spell['name']} has no damage defined.[/white]")
        
        # Check for saving throw attributes to potentially reduce damage
        save_attr = spell.get('save')
        save_dc = spell.get('dc')
        
        # Apply damage to each living target
        for target in targets:
            if target.is_alive():
                if save_attr and save_dc:
                    # If saving throw is successful, reduce damage by half
                    if target.saving_throw(target, save_attr, save_dc):
                        reduced_damage = damage // 2
                        console.print(f"[red]{target.name} saves and takes {reduced_damage} damage (half).[/red]" if isinstance(target, PlayerCharacter) else f"[gray]{target.name} saves and takes {reduced_damage} damage (half).[/gray]")
                        target.take_damage(reduced_damage)
                        console.print(f"[green]{target.name} now has {target.current_hp} HP remaining.[/green]" if isinstance(target, NonPlayerCharacter) else f"[red]{target.name} now has {target.current_hp} HP remaining.[/red]")
                    else:
                        # Full damage on failed save
                        console.print(f"[red]{target.name} fails save and takes {damage} damage.[/red]" if isinstance(target, PlayerCharacter) else f"[green]{target.name} fails save and takes {damage} damage.[/green]")
                        target.take_damage(damage)
                        console.print(f"[green]{target.name} now has {target.current_hp} HP remaining.[/green]" if isinstance(target, NonPlayerCharacter) else f"[red]{target.name} now has {target.current_hp} HP remaining.[/red]")
                else:
                    # No saving throw, apply full damage
                    console.print(f"[red]{target.name} takes {damage} damage.[/red]" if isinstance(target, PlayerCharacter) else f"[green]{target.name} takes {damage} damage.[/green]")
                    target.take_damage(damage)
                    console.print(f"[green]{target.name} now has {target.current_hp} HP remaining.[/green]" if isinstance(target, NonPlayerCharacter) else f"[red]{target.name} now has {target.current_hp} HP remaining.[/red]")
                # Check if target is defeated after damage
                if not target.is_alive():
                    console.print(f"[bold red]{target.name} is defeated![/bold red]")

    def _apply_healing_effect(self, caster, targets, spell):
        """
        Applies healing effects to restore HP to targets.
        
        Args:
            caster: The character casting the spell.
            targets: List of target characters to heal.
            spell: Dictionary containing spell data.
        """
        # Check if healing is defined in the spell data
        if 'healing' in spell:
            healing = d20.roll(spell['healing']).total
            console.print(f"[cyan]{spell['name']} heals {healing} HP, restoring health to the target.[/cyan]")
            # Apply healing to each living target
            for target in targets:
                if target.is_alive():
                    target.current_hp += healing
                    # Cap healing at maximum HP
                    if target.current_hp > target.hp:
                        target.current_hp = target.hp
                    console.print(f"[yellow]{target.name} is healed to {target.current_hp} HP.[/yellow]" if isinstance(target, PlayerCharacter) else f"[cyan]{target.name} is healed to {target.current_hp} HP.[/cyan]")
        else:
            console.print(f"[white]{spell['name']} has no healing effect defined.[/white]")
            log_message(f"DEBUG: No healing attribute found for {spell['name']}. No healing applied.")

    def perform_contested_check(self, character, attribute):
        """Placeholder for contested check logic."""
        # Placeholder: Assume the character fails the contested check for now
        return False

    def end_round(self):
        """Handles end-of-round logic, such as checking for combat end."""
        log_message(f"[blue]--- Round {self.round_number}: End! ---[/blue]\n")
        # Additional end-of-round logic can be added here

    def is_combat_over(self):
        """Checks if combat is over (all players or all NPCs defeated)."""
        players_alive = any(player.is_alive() for player in self.players)
        npcs_alive = any(npc.is_alive() for npc in self.npcs)
        return not players_alive or not npcs_alive


# Load game state from JSON with schema validation
def load_game_state(filename="game_state.json"):
    import json
    import jsonschema
    from jsonschema import ValidationError
    
    try:
        # Load the schema
        with open("gs_schema.json", 'r') as schema_file:
            schema = json.load(schema_file)
        
        # Load the game state data
        with open(filename, 'r') as file:
            data = json.load(file)
        
        # Validate the data against the schema
        try:
            jsonschema.validate(instance=data, schema=schema)
            log_message(f"Game state data from {filename} validated successfully against schema.")
            return data
        except ValidationError as e:
            log_message(f"Validation error in game state data from {filename}: {str(e)}")
            log_message("Attempting to refine game state data using LLM...")
            refined_data = refine_game_state_data(data, schema)
            if refined_data:
                try:
                    jsonschema.validate(instance=refined_data, schema=schema)
                    log_message("Refined game state data validated successfully against schema.")
                    return refined_data
                except ValidationError as re:
                    log_message(f"Refinement failed to conform to schema: {str(re)}")
                    log_message("Dark forces have prevented game state refinement. Proceeding with original data.")
                    return data
            else:
                log_message("Refinement process failed. Dark forces have prevented game state loading. Proceeding with original data.")
                return data
    except Exception as e:
        log_message(f"Error during game state loading or validation: {str(e)}")
        log_message("Dark forces have prevented game state loading. Please check the file and try again.")
        return None

# Create characters from game state
def create_characters_from_state(game_state):
    players = []
    npcs = []
    for player_data in game_state['players']:
        player = PlayerCharacter(
            name=player_data['name'],
            hp=player_data['hp'],
            ac=player_data['ac'],
            strength=player_data['strength'],
            dexterity=player_data['dexterity'],
            constitution=player_data['constitution'],
            intelligence=player_data['intelligence'],
            wisdom=player_data['wisdom'],
            charisma=player_data['charisma'],
            damage=player_data.get('damage', '1d6'),  # Default damage if not specified
            inventory=player_data.get('inventory', []),
            class_type=player_data.get('class', 'fighter'),
            spells=player_data.get('spells', []),
            conditions=player_data.get('conditions', {})
        )
        players.append(player)
    
    for npc_data in game_state['npcs']:
        npc = NonPlayerCharacter(
            name=npc_data['name'],
            hp=npc_data['hp'],
            ac=npc_data['ac'],
            strength=npc_data['strength'],
            dexterity=npc_data['dexterity'],
            constitution=npc_data['constitution'],
            intelligence=npc_data['intelligence'],
            wisdom=npc_data['wisdom'],
            charisma=npc_data['charisma'],
            damage=npc_data.get('damage', '1d6'),  # Default damage if not specified
            inventory=npc_data.get('inventory', []),
            class_type=npc_data.get('class', 'fighter'),  # Default to 'fighter' for NPCs if class not specified
            race=npc_data.get('race', 'unknown'),  # Handle race separately from class
            spells=npc_data.get('spells', []),
            conditions=npc_data.get('conditions', {})
        )
        npcs.append(npc)
    
    return players, npcs

def refine_game_state_data(data, schema, max_retries=2):
    """Use the Venice AI API to refine game state data that doesn't conform to the schema."""
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
    system_prompt = "You are an AI assistant tasked with refining D&D 5e game state data to fit a specific JSON schema. Return only the corrected JSON object with no additional text."
    user_prompt = (
        f"Refine the following game state data to conform to the provided JSON schema. "
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Non-conforming data:\n{json.dumps(data, indent=2)}\n\n"
        "Fill in missing fields with appropriate D&D 5e values, remove invalid fields, and adjust existing fields to match the schema. "
        "Ensure the following: "
        "- For 'save' fields in spells, use a string value from ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', ''] and avoid 'None' or null values. Use '' (empty string) if no saving throw is required. "
        "- For 'attribute' fields in spell effects, only use values from ['ac', 'health', 'visibility', 'speed', 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', 'advantage', 'disadvantage']. Replace invalid values like 'movement' with 'speed'. "
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
            input_log_filename = f"refine-llm-logs/input_game_state_{timestamp}_attempt_{attempt+1}.json"
            with open(input_log_filename, 'w') as input_file:
                json.dump(payload, input_file, indent=2)
            log_message(f"Logged LLM input to {input_log_filename}")
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            # Log the output response
            output_log_filename = f"refine-llm-logs/output_game_state_{timestamp}_attempt_{attempt+1}.json"
            with open(output_log_filename, 'w') as output_file:
                json.dump(response_data, output_file, indent=2)
            log_message(f"Logged LLM output to {output_log_filename}")
            
            if "choices" in response_data and response_data["choices"]:
                content = response_data["choices"][0]["message"]["content"]
                content = re.sub(r'```json|```', '', content).strip()
                try:
                    refined_data = json.loads(content)
                    log_message(f"Refinement attempt {attempt + 1}/{max_retries} successful.")
                    return refined_data
                except json.JSONDecodeError:
                    log_message(f"Refinement attempt {attempt + 1}/{max_retries} failed: Response is not valid JSON.")
                    if attempt == max_retries - 1:
                        log_message("Max retries reached. Dark forces have prevented data refinement.")
                        return None
            else:
                log_message(f"Refinement attempt {attempt + 1}/{max_retries} failed: No valid choices in API response.")
                if attempt == max_retries - 1:
                    log_message("Max retries reached. Dark forces have prevented data refinement.")
                    return None
        except requests.exceptions.RequestException as e:
            log_message(f"API Error during refinement attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1:
                log_message("Max retries reached. Dark forces have prevented data refinement.")
                return None
    return None

if __name__ == "__main__":
    try:
        # Load game state
        game_state = load_game_state()
        if game_state is None:
            console.print("[bold red]Combat engine could not load game state due to dark forces. Exiting.[/bold red]")
        else:
            players, npcs = create_characters_from_state(game_state)
            
            # Initialize combat engine
            combat = CombatEngine(players, npcs)
            combat.start_combat()
    except Exception as e:
        log_message(f"Error in main execution: {str(e)}")
        console.print("[bold red]Combat engine encountered an error and could not start. Dark forces have prevented this battle. Check logs for details.[/bold red]")
