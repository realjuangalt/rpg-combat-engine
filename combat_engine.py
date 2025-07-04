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
    logger.info(message)

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
            # Ensure conditions are dynamically initialized from CONDITIONS_DICT
            self.conditions = {
                condition_name: conditions.get(condition_name, {"active": False, "duration": 0})
                for condition_name in CONDITIONS_DICT if condition_name in conditions
            }
        
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
                log_message(f"{condition_name} on {self.name} has {condition_instance['duration']} round(s) remaining.")

                # Mark the condition to update if its duration reaches 0
                if condition_instance['duration'] <= 0:
                    log_message(f"Condition {condition_name} has expired and will be set to inactive.")
                    self.remove_condition(condition_name)  # Use remove_condition method instead of inline logic


            # Handle variable duration (e.g., 1d4 rounds)
            elif duration_info.get("type") == "variable":
                if "duration" in condition_instance:
                    condition_instance['duration'] -= 1
                    log_message(f"{condition_name} on {self.name} has {condition_instance['duration']} round(s) remaining.")

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
        effect = Effect(effect_name, attribute, modifier, duration)
        self.effects[effect_name] = effect
        effect.apply(self)  # Apply the effect to the character
        log_message(f"{effect_name} applied to {self.name}.")

    def remove_expired_effects(self):
        """Remove effects whose duration has expired."""
        for effect_name, effect in list(self.effects.items()):  # Use list() to allow deletion during iteration
            # Ensure the effect is an instance of the Effect class
            if isinstance(effect, Effect):
                effect.decrement_duration()
                if effect.duration <= 0:
                    effect.remove(self)
                    del self.effects[effect_name]
            # else:
            #     log_message(f"Error: {effect_name} is not an Effect instance.")
        for effect_name, effect in list(self.effects.items()):  # Use list() to allow deletion during iteration
            if isinstance(effect, Effect):
                effect.decrement_duration()
                if effect.duration <= 0:
                    effect.remove(self)
                    del self.effects[effect_name]
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
    def __init__(self, name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells=None, conditions=None,is_enemy=True):
        super().__init__(name, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, damage, inventory, class_type, spells, conditions)
        self.is_enemy = is_enemy

    
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
        # elif self.is_numeric_modifier():
        elif self.attribute in character.stats:
            """Checks if the modifier is a numeric value (can be an integer)."""
            # log_message(f"DEBUG 478: -> {self.attribute}")
            # self.modifier.isdigit() or (self.modifier.startswith('-') and self.modifier[1:].isdigit())
            current_value = getattr(character, self.attribute, 0)
            # log_message(f"DEBUG 452: current_value {current_value}")
            # log_message(f"DEBUG 452: self.attribute {self.attribute}")
            # log_message(f"DEBUG 452: self.modifier {self.modifier}")

            new_value = current_value + (self.modifier)
            setattr(character, self.attribute, new_value)
            log_message(f"APPLY: {self.name} increases {self.attribute} by {self.modifier} for {character.name}. New value: {new_value}")

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
            new_value = current_value - int(self.modifier)
            setattr(character, self.attribute, new_value)
            log_message(f"{self.name} decreases {self.attribute} by {self.modifier} for {character.name}. New value: {new_value}")

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

        # End of combat message
        log_message(f"\n[bold cyan]--- Combat has ended after {self.round_number} rounds. ---[/bold cyan]")
        console.print("[bold magenta]Thank you for playing! Exiting combat engine...[/bold magenta]")

    def take_turn(self, character):
        """Handles the turn logic for a character."""
        # Check if the character can act at all
        # log_message(f"DEBUG 588 YOU'VE ARRIVED AT TAKE TURN IN COMBATENGINE CLASS")
        # character.remove_expired_effects()
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

        # Decrement condition durations after the character's turn
        
        log_message(f"{character.name}'s turn ends. Conditions & effects updated.")
        character.decrement_conditions(self)
        character.decrement_effect_durations()


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

            # Skip conditions that are not active
            if not condition_instance.get("active"):
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
        console.print(f"\n{player.name}'s turn with {player.current_hp} HP!")
        console.print("1. Attack")
        console.print("2. Cast a Spell")
        console.print("3. Defend (placeholder action)")
        action_choice = input("Enter the number of your action: ")

        if action_choice == "1":
            console.print("Choose a weapon:")
            for i, weapon in enumerate(player.inventory):
                console.print(f"{i + 1}. {weapon['name']} ({weapon['type']} - Damage: {weapon['damage']})")
            weapon_choice = int(input("Enter the number of the weapon you want to use: ")) - 1

            if 0 <= weapon_choice < len(player.inventory):
                chosen_weapon = player.inventory[weapon_choice]
            else:
                console.print("[red]Invalid choice, defaulting to the first weapon.[/red]")
                chosen_weapon = player.inventory[0]

            target = self.choose_target(player, self.npcs)  # Select target after weapon is chosen

            return {"type": "attack", "target": target, "weapon": chosen_weapon}

        elif action_choice == "2":
            # Choose a spell
            console.print("Choose a spell:")
            for i, spell in enumerate(player.spells, start=1):
                console.print(f"{i}. {spell['name']}")
            spell_choice = int(input("Enter the number of the spell you want to cast: ")) - 1

            if 0 <= spell_choice < len(player.spells):
                spell = player.spells[spell_choice]
            else:
                console.print("[red]Invalid spell choice, defaulting to the first spell.[/red]")
                spell = player.spells[0]

            # Determine target based on the spell's targeting type
            if spell['targeting'] == "aoe":
                target = self.npcs  # All NPCs are affected by the AOE spell
                log_message(f"{spell['name']} affects all NPCs!")
            elif spell['targeting'] == "self":
                target = [player]  # The actor is the only target
            else:  # 'single'
                target = [self.choose_target(player, self.npcs, spell)]
                print(f"get_player_action target test: {self.choose_target}")
            
            return {"type": "cast_spell", "spell": spell, "target": target}

        elif action_choice == "3":
            console.print(f"{player.name} defends!")
            return {"type": "defend"}

        else:
            console.print("Invalid choice, defaulting to Attack.")
            return {"type": "attack", "target": self.choose_target(player, self.npcs), "weapon": player.inventory[0]}

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

        # Apply advantage or disadvantage only for attack roll spells
        adv_disadv = getattr(actor, 'adv_disadv', 'normal')
        # log_message(f"DEBUG 771: adv_disadv -> {adv_disadv}")
        
        # Determine the correct modifier for spells based on the actor's class
        spell_mod = actor.calculate_modifier('spell')

        # Handle spell targeting "self"
        if spell['targeting'] == "self":
            targets_list = [actor]
            log_message(f"{spell['name']} only affects {actor.name}.")

        # Handle spell targeting a single target (enemy or ally)
        elif spell['targeting'] == "single":
            # log_message(f"DEBUG 783: spell selected-> {spell}")
            if targets_list is None:
                # Healing, buff, or debuff spells should target allies
                if spell['type'] in ['healing', 'buff']:
                    log_message(f"Selecting an ally to apply {spell['name']}.")
                    targets_list = [actor] + self.players  # Target allies and actor
                else:
                    # Damage or debuff spells target enemies (NPCs)
                    log_message(f"Selecting an enemy for {spell['name']}.")
                    targets_list = [self.choose_target(actor, self.npcs, spell)]

        # Filter out defeated targets
        targets_list = [t for t in targets_list if t.is_alive()]
        if not targets_list:
            log_message(f"No valid targets for {spell['name']}.")
            return

        # Handle attack roll-based damage spells (e.g., Firebolt, Eldritch Blast)
        if "damage" in spell and spell.get('save') is None:
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
        elif "damage" in spell and spell.get('save'):
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
                self.check_target_status(target)

        # Handle healing spells
        elif "healing" in spell:
            healing_roll = d20.roll(spell['healing'])
            log_message(f"{actor.name} rolls {healing_roll.result} for healing.")
            for target in targets_list:
                target.current_hp = min(target.current_hp + healing_roll.total, target.hp)  # Ensure HP doesn't exceed max
                log_message(f"{target.name} is healed for {healing_roll.total} HP and now has {target.current_hp} HP.")

        # Handle condition spells (e.g., stunning)
        if spell['type'] == 'condition':
            effect_data = spell['effect']
            condition_name_in_spell = effect_data['modifier']  # The condition being applied (e.g., 'stunned')

            for target in targets_list:
                # Check for saving throw if specified in the spell
                if 'save' in spell:
                    if target.saving_throw(target, spell['save'], spell['dc'], spell['effect']['modifier']):
                        log_message(f"{target.name} succeeds on the saving throw and avoids {condition_name_in_spell}.")
                        continue  # Skip applying the condition if the saving throw succeeds
                    else:
                        log_message(f"{target.name} fails the saving throw and is affected by {condition_name_in_spell}.")

                duration = effect_data.get('duration', 1)  # Default to 1 round if duration isn't specified
                log_message(f"Applying {condition_name_in_spell} to {target.name} for {duration} round(s).")
                target.apply_condition_with_effects(condition_name_in_spell, duration, spell)
                log_message(f"[bold yellow]{actor.name} cast {spell['name']} on {target.name}: {attribute} is modified by {modifier} for {duration} round(s).[/bold yellow]")
        # Handle buff spells (e.g., granting advantage, increasing AC)
        if spell['type'] == 'buff':
            # log_message(f"DEBUG 864: Actually casting buff spell {spell}")
            effect_data = spell['effect']
            spell_name = spell['name']
            attribute = effect_data['attribute']  # The attribute being affected (e.g., 'adv_disadv', 'ac')
            modifier = effect_data['modifier']  # The value being applied (e.g., 'advantage', +2)
            duration = effect_data.get('duration', 1)  # Default to 1 round if not specified

            for target in targets_list:
                target.apply_effect(spell['name'], attribute, modifier, duration)
                # log_message(f"DEBUG 871: Applying buff {spell['name']} to {target.name}: {attribute} is modified by {modifier} for {duration} round(s).")
                
                # Create an Effect instance and apply it to the target
                # effect = Effect(name=spell['name'], attribute=attribute, modifier=modifier, duration=duration)
                # effect = Effect(name = spell_name, attribute=attribute, modifier=modifier, duration=duration)
                # log_message(f"DEBUG 869: effect - > {Effect}")
                # effect.apply(target)  # Reuse the apply method from Effect class
                log_message(f"[bold yellow]{actor.name} cast buff {spell['name']} on {target.name}: {attribute} is modified by {modifier} for {duration} round(s).[/bold yellow]")
                log_message(f"{target.name} is now affected by the buff for {duration} rounds.")
        # Handle buff spells (e.g., granting advantage, increasing AC)
        if spell['type'] == 'debuff':
            log_message(f"DEBUG 858: Actually casting debuff spell {spell}")
            effect_data = spell['effect']
            attribute = effect_data['attribute']  # The attribute being affected (e.g., 'adv_disadv', 'ac')
            modifier = effect_data['modifier']  # The value being applied (e.g., 'advantage', +2)
            duration = effect_data.get('duration', 1)  # Default to 1 round if not specified

            for target in targets_list:

                # Create an Effect instance and apply it to the target
                target.apply_effect(spell['name'], attribute, modifier, duration)
                log_message(f"[bold yellow]{actor.name} cast {spell['name']} on {target.name} debuffing it with {modifier} for {duration} round(s).[/bold yellow]")
                log_message(f"{target.name} is now affected by the buff for {duration} rounds.")
   
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

        # Apply interaction effects (advantage/disadvantage, automatic critical hits) from conditions on the target
        for condition_name, condition_info in target.conditions.items():
            if condition_info.get("active"):  # Check if the condition is active
                if condition_name in CONDITIONS_DICT:
                    interaction_effects = CONDITIONS_DICT[condition_name]["interaction_effects"]

                    # Check for advantage or disadvantage on attack rolls against the target
                    if interaction_effects["attack_roll_against"] == "advantage":
                        log_message(f"Attackers have advantage when attacking {target.name} due to {condition_name}.")
                        adv_disadv = "advantage"
                    elif interaction_effects["attack_roll_against"] == "disadvantage":
                        log_message(f"Attackers have disadvantage when attacking {target.name} due to {condition_name}.")
                        adv_disadv = "disadvantage"

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

        # Handle automatic critical hit based on conditions on the target
        critical_hit = False
        for condition_name, condition_info in target.conditions.items():
            if condition_info.get("active"):  # Ensure only active conditions apply
                if condition_name in CONDITIONS_DICT:
                    interaction_effects = CONDITIONS_DICT[condition_name]["interaction_effects"]

                    # Apply automatic critical hit if the condition allows it (e.g., Paralyzed within 5 feet)
                    if interaction_effects["critical_hit"] == "yes" and actor.is_within_melee_range(target):
                        log_message(f"{actor.name} automatically scores a critical hit on {target.name} due to {condition_name}.")
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

        target = self.choose_weakest_player(self.players)  # Example target selection
        log_message(f"{npc.name} decides to attack {target.name}.")
        chosen_weapon = npc.inventory[0]  # For simplicity, NPC uses the first weapon
        self.attack(npc, target, chosen_weapon)

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
        elif action["type"] == "defend":
            log_message(f"{character.name} defends this round.")

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
    players, npcs = load_characters_from_json('game_state.json')
    engine = CombatEngine(players, npcs)
    engine.start_combat()
    

