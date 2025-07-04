To expand the NPCs' decision-making capabilities and integrate spell casting, conditions like charm or fear, and healing, we'll need to develop an approach that builds on both **`handle_npc_turn`** and **`decide_action`**. The goal is to provide NPCs with a more sophisticated AI that can:

1. **Evaluate their current conditions (e.g., stunned, charmed, frightened)**.
2. **Decide whether to attack, heal, or use a buff/debuff spell**.
3. **React appropriately based on their conditions** (e.g., avoiding attacking allies when charmed, fleeing when frightened).
4. **Assess allies' and their own health to determine if healing is needed**.

### Key Steps to Expand NPC AI

1. **Condition Handling**:
   Conditions like *stunned, charmed, frightened,* etc., should be prioritized in **`decide_action`**. This method would need to be expanded to check the full array of conditions that impact the NPC's actions.

2. **Target Selection**:
   Right now, the NPC attacks the weakest player. We should enhance this by:
   - Checking if the NPC is *charmed*—in which case it shouldn't target the player but rather treat them as an ally.
   - If *frightened*, avoid moving closer to or attacking the source of the fear.
   - Add logic for healing, such as if an ally's health is below a certain threshold or if the NPC's own health is dangerously low.
   
3. **Action Selection (Attack, Heal, Buff)**:
   Based on the NPC's conditions and the state of the battle, the NPC should decide whether to:
   - **Attack** a target if no conditions prevent it.
   - **Heal** themselves or an ally based on current health.
   - **Buff/Debuff** based on strategic needs (e.g., cast a debuff spell like *curse* on a player if it benefits the team).

4. **Implementing a Spell Casting Routine**:
   Just like we handle weapon attacks, NPCs should have logic to cast spells based on the context. This means adding a spell-casting pathway to **`decide_action`** and **`handle_npc_turn`**.

### Key Updates for Each Method

#### **`decide_action` Method:**

```python
def decide_action(self, allies, enemies):
    # Basic AI to decide what action to take based on conditions, targets, etc.

    # Check for conditions that prevent action (e.g., stunned)
    if 'stunned' in self.conditions and self.conditions['stunned']['active']:
        log_message(f"{self.name} is stunned and cannot act this turn.")
        return None
    
    # Handle charmed condition (NPC cannot attack charmed characters, treat them as allies)
    if 'charmed' in self.conditions and self.conditions['charmed']['active']:
        log_message(f"{self.name} is charmed and considers the player as an ally.")
        enemies = [e for e in enemies if not isinstance(e, PlayerCharacter)]  # Exclude players from enemies
        allies = self.players  # Treat players as allies

    # Handle frightened (NPC cannot move closer or attack the source of fear)
    if 'frightened' in self.conditions and self.conditions['frightened']['active']:
        # Skip action if frightened to the point of inaction
        log_message(f"{self.name} is frightened and avoids attacking or moving closer to the source of fear.")
        return None
    
    # Check if the NPC or an ally is injured and needs healing
    if self.should_heal(allies):
        return "heal", self.select_healing_target(allies)

    # Decide if the NPC should attack or cast a spell based on strategy
    action_type = self.choose_attack_or_spell()

    # Return the chosen action
    if action_type == 'attack':
        return "attack", self.select_attack_target(enemies)
    elif action_type == 'spell':
        return "cast_spell", self.choose_spell(), self.select_spell_target(enemies, allies)

    return "attack", self.select_attack_target(enemies)
```

#### **`handle_npc_turn` Method:**

```python
def handle_npc_turn(self, npc):
    """Determines the action of an NPC on their turn."""
    if not npc.is_alive():
        return

    action_decision = npc.decide_action(self.players, self.npcs)
    if action_decision is None:
        log_message(f"{npc.name} cannot act this turn due to conditions.")
        return

    action_type, target_or_spell, target = action_decision

    if action_type == "attack":
        chosen_weapon = npc.inventory[0]  # NPC uses the first weapon for simplicity
        self.attack(npc, target, chosen_weapon)
    elif action_type == "heal":
        self.cast_spell(npc, target_or_spell, [target])
    elif action_type == "cast_spell":
        self.cast_spell(npc, target_or_spell, [target])
```

### Expanded Logic

#### **Condition Handling**:
- *Charmed*: The NPC will now treat players as allies and won't target them for attacks.
- *Frightened*: The NPC will avoid the source of fear and possibly even skip their turn if severely frightened.
- *Stunned*: The NPC will not take any action during the turn.

#### **Healing**:
- The method **`should_heal`** will check if the NPC or allies need healing based on their health. It will return **True** if healing is required.
  
```python
def should_heal(self, allies):
    # If the NPC or an ally's health is below a certain threshold, healing is needed
    low_health_threshold = self.hp * 0.5
    for ally in allies:
        if ally.current_hp < low_health_threshold:
            return True
    return False

def select_healing_target(self, allies):
    # Selects the ally with the lowest HP for healing
    return min(allies, key=lambda ally: ally.current_hp)
```

#### **Attack and Spell Decisions**:
- **`choose_attack_or_spell`** will decide if the NPC should attack or cast a spell based on their available resources and the state of the battle.
  
```python
def choose_attack_or_spell(self):
    # Basic logic to decide whether to attack or cast a spell
    # should also decide based on character class and stats. 
    if self.spells and self.current_mana > 0:
        # Prioritize casting a spell if mana is available
        return "spell"
    return "attack"
```

- **`select_attack_target`** will continue selecting the weakest target but can be expanded to include other factors like proximity or threat level.

```python
def select_attack_target(self, enemies):
    # Target the weakest enemy for now, can be expanded to include other factors
    return self.choose_weakest_player(enemies)
```

### Conclusion

This approach expands the NPC logic significantly by introducing conditions handling, healing, and spell-casting capabilities. By enhancing **`decide_action`** to evaluate the current conditions and **`handle_npc_turn`** to execute more diverse actions, we can simulate a more strategic and dynamic NPC behavior, especially with charm, fear, and healing.