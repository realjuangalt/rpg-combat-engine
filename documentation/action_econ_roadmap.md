To help integrate action economy into your D&D game, we need a clear road map that breaks down the different elements of action economy (actions, bonus actions, movement, reactions, etc.) and prepares the code base for future updates.

### Action Economy Overview
- **Actions**: Standard actions like attacking, casting spells, or using items. Every character can typically take one action per turn.
- **Bonus Actions**: Certain abilities and spells allow bonus actions. A character can only take one per turn, but not every character may use them.
- **Movement**: Characters can move up to their movement speed each turn. Movement can be split across the turn and interact with different conditions.
- **Reactions**: A creature can take one reaction per round, typically outside of its turn, like making an opportunity attack.
- **Free Actions/Interactions**: Simple interactions like drawing a weapon or opening a door, typically allowed once per turn.

### Road Map for Action Economy Integration

1. **Step 1: Create Turn Tracking Framework**
   - Ensure each character’s turn is tracked properly, including whether they have taken an action, bonus action, or reaction.
   - **Counters for Action/Bonus Action/Reaction**: Add fields to characters for actions, bonus actions, and reactions allowed/remaining during a turn.

2. **Step 2: Structure the Action Economy**
   - Implement a flexible system that handles actions, bonus actions, reactions, and movement separately.
   - **Actions & Bonus Actions**: Create counters and logic to track whether a character has used their action or bonus action during their turn.
   - **Movement**: Plan a movement subsystem that tracks the distance a character has moved and the movement options left.
   
3. **Step 3: Track and Reset Action Economy**
   - Create logic to **reset** the action counters (actions, bonus actions, and reactions) at the end of a character’s turn and the beginning of a new round.
   - Track remaining movement per turn.

4. **Step 4: Reactions and Opportunity Attacks**
   - Implement reactions (e.g., opportunity attacks, Counterspell) and ensure they are tracked properly per round, not per turn.

5. **Step 5: Movement and Special Movement Types**
   - Integrate complex movement mechanics, like difficult terrain, flying, swimming, and climbing. Leave room for special cases like the *Dash* action, and conditions like prone.
   - Prepare for **interrupts** or effects that might modify movement (e.g., *Web* or *Hold Person*).

### Road Map Details (Based on Reference Code Analysis)

#### 1. **Turn Tracking Framework**
   - **Goal**: Create a system to track actions, bonus actions, and movement.
   - Add new fields to the character class:
     - `actions_taken`: Tracks whether the character has used their action.
     - `bonus_action_taken`: Tracks whether the character has used a bonus action.
     - `reaction_taken`: Tracks whether the character has used their reaction.
     - `movement_remaining`: Tracks the remaining movement for a character.
   
   Example:

   ```python
   class Character:
       def __init__(self, name, movement_speed):
           self.name = name
           self.movement_speed = movement_speed
           self.actions_taken = False
           self.bonus_action_taken = False
           self.reaction_taken = False
           self.movement_remaining = movement_speed  # Start with full movement each turn
   ```

#### 2. **Action Economy Counters**
   - **Goal**: Ensure that actions, bonus actions, and reactions are tracked on a per-turn basis.
   - In each combat round, the turn begins by resetting the counters.
   
   Add methods to handle actions, bonus actions, and reactions:
   
   ```python
   def take_action(self):
       if self.actions_taken:
           log_message(f"{self.name} has already taken an action this turn.")
       else:
           log_message(f"{self.name} takes an action.")
           self.actions_taken = True

   def take_bonus_action(self):
       if self.bonus_action_taken:
           log_message(f"{self.name} has already taken a bonus action this turn.")
       else:
           log_message(f"{self.name} takes a bonus action.")
           self.bonus_action_taken = True

   def take_reaction(self):
       if self.reaction_taken:
           log_message(f"{self.name} has already taken a reaction this round.")
       else:
           log_message(f"{self.name} takes a reaction.")
           self.reaction_taken = True
   ```

#### 3. **Resetting Action Economy at Turn End**
   - **Goal**: At the end of each turn, reset action counters, except for reactions (which reset at the start of the next round).
   
   Add a reset method:
   
   ```python
   def end_turn(self):
       log_message(f"{self.name}'s turn ends.")
       self.actions_taken = False
       self.bonus_action_taken = False
       self.movement_remaining = self.movement_speed  # Reset movement for the next turn
   ```

#### 4. **Reactions and Special Cases**
   - **Goal**: Handle opportunity attacks, spell reactions (like *Counterspell*), and any other special reaction scenarios.
   
   When the game asks for a reaction (outside of the character’s turn):
   
   ```python
   def take_reaction(self):
       if self.reaction_taken:
           log_message(f"{self.name} has already used a reaction this round.")
       else:
           log_message(f"{self.name} uses a reaction.")
           self.reaction_taken = True
   ```

#### 5. **Advanced Movement Integration**
   - **Goal**: Track the remaining movement for each character and handle movement in different terrain types or special cases.
   
   Implement movement tracking:
   
   ```python
   def move(self, distance):
       if distance > self.movement_remaining:
           log_message(f"{self.name} cannot move that far. Only {self.movement_remaining} feet remaining.")
       else:
           log_message(f"{self.name} moves {distance} feet.")
           self.movement_remaining -= distance
   ```

   Later steps might include difficult terrain, flying, and swimming speeds.

### Road Map for Full Integration:
1. **Foundation** (Action Counters):
   - Create and initialize action, bonus action, reaction, and movement tracking for each character.
   - Implement basic turn structure to reset these counters.

2. **Basic Actions/Bonus Actions**:
   - Implement action, bonus action, and reaction logic in the game’s core combat loop.

3. **Movement System**:
   - Track movement and handle reductions for each move action taken.

4. **Advanced Movement**:
   - Implement special movement types (Dash, difficult terrain, etc.).

5. **Reactions**:
   - Implement reaction triggers for opportunity attacks, Counterspell, etc.

6. **Special Features**:
   - Ensure class features, spells, and abilities interact correctly with the action economy (e.g., Rogues' Cunning Action, Warlocks' bonus action spells).

This roadmap should provide a step-by-step guide for integrating the action economy in a flexible and scalable manner!