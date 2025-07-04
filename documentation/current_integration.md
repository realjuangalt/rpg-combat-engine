To implement conditions in the combat engine, the `duration` key should hold values that can be easily interpreted and manipulated by the engine during combat. Here’s a breakdown of useful values for the `duration` key:

### **Useful Values for the `duration` Key:**

1. **Integer (e.g., `1`, `3`, `5`)**:
   - Represents a fixed number of **rounds** the condition will last.
   - Useful for conditions like **Stunned** or **Paralyzed**, which last for a specific number of rounds.
   - Example: `"duration": 3`

2. **String (e.g., `"until_save"`, `"until_end"`, `"until_removed"`)**:
   - Represents conditional durations based on external factors like saving throws, spell durations, or other actions.
   
   - **`"until_save"`**: The condition lasts until the target succeeds on a saving throw (common for conditions like **Paralyzed** or **Frightened**).
     - Example: `"duration": "until_save"`
   
   - **`"until_end"`**: The condition lasts until the effect that caused it naturally expires (e.g., the end of a spell or combat encounter).
     - Example: `"duration": "until_end"`
   
   - **`"until_removed"`**: The condition persists until something specific (like a spell or action) removes it (e.g., **Petrified** or **Charmed**).
     - Example: `"duration": "until_removed"`
   
3. **Mixed values (e.g., `"1_save"`, `"3_save"`)**:
   - Represents conditions that can last a certain number of rounds unless a saving throw ends them early.
   - **`"3_save"`**: The condition lasts up to 3 rounds, but if the target succeeds on a saving throw before that, it ends early.
     - Example: `"duration": "3_save"`

4. **Conditional (e.g., `"end_of_turn"`, `"start_of_next_turn"`)**:
   - Used for very short-duration effects, like **Shield** spells or conditions that last only until the end of the current turn.
   - **`"end_of_turn"`**: The condition lasts until the end of the current turn.
     - Example: `"duration": "end_of_turn"`
   
   - **`"start_of_next_turn"`**: The condition expires at the start of the target's next turn.
     - Example: `"duration": "start_of_next_turn"`

### Example Conditions Using the `duration` Key:

```json
{
    "Blinded": {
        "type": "condition",
        "attribute": ["attack_roll", "dexterity_saving_throw"],
        "modifier": ["disadvantage", "disadvantage"],
        "description": "A blinded creature has disadvantage on attack rolls and automatically fails any ability check that requires sight.",
        "duration": 3,  // Lasts for 3 rounds
        "effects": {
            "attacks_against": "advantage"
        }
    },
    "Frightened": {
        "type": "condition",
        "attribute": ["attack_roll", "saving_throw"],
        "modifier": ["disadvantage", "disadvantage"],
        "description": "A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight.",
        "duration": "until_save",  // Ends when a successful saving throw is made
        "effects": {
            "movement": "can’t move closer"
        }
    },
    "Paralyzed": {
        "type": "condition",
        "attribute": ["actions", "attack_roll", "saving_throw"],
        "modifier": ["none", "advantage", "advantage"],
        "description": "A paralyzed creature is incapacitated and can’t move or speak.",
        "duration": "until_save",  // Ends on a successful saving throw
        "effects": {
            "attacks_against": "critical if within 5 feet"
        }
    },
    "Prone": {
        "type": "condition",
        "attribute": ["movement", "attack_roll"],
        "modifier": ["half_speed", "disadvantage"],
        "description": "A prone creature’s only movement option is to crawl.",
        "duration": "end_of_turn",  // Ends at the end of the turn or if the target stands up
        "effects": {
            "melee_attacks_against": "advantage",
            "ranged_attacks_against": "disadvantage"
        }
    },
    "Incapacitated": {
        "type": "condition",
        "attribute": ["actions"],
        "modifier": ["none"],
        "description": "An incapacitated creature can’t take actions or reactions.",
        "duration": 2,  // Lasts for 2 rounds
        "effects": {}
    }
}
```

### Key Takeaways:
- **Fixed duration (`integer`)**: Great for predictable, short-term conditions like being **stunned** for a few rounds.
- **Conditional duration (`string`)**: Perfect for conditions that rely on external factors, like a successful saving throw (**paralyzed** or **frightened**).
- **Mixed (`X_save`)**: Conditions that last a set number of rounds but could end earlier with a save, like a **fear** spell.
- **Short-term conditional (`end_of_turn`)**: Ideal for very temporary conditions like **prone**.

This should give us a flexible system that works across different conditions and helps integrate their effects more cleanly into the combat engine.


--------

To streamline the integration of conditions into the combat engine and simplify their handling, we can categorize the 14 conditions based on their impact on players and NPCs. By grouping them into broader categories, we can abstract the effects they impose and standardize their implementation. Here’s a breakdown based on common effects:

### 1. **Action Restrictions**  
These conditions limit or prevent a character's ability to take actions, which can include attacks, movement, or reactions.

- **Incapacitated**: Can't take actions or reactions.
- **Stunned**: Incapacitated, can't move, speak falteringly, attackers have advantage.
- **Paralyzed**: Incapacitated, can't move or speak, attacks are critical hits if within 5 feet.
- **Unconscious**: Incapacitated, can't move or speak, unaware of surroundings.
- **Restrained**: Can't move, disadvantage on attacks and saving throws.

### 2. **Movement Impairment**  
These conditions primarily affect the character’s ability to move or adjust their position.

- **Grappled**: Speed becomes 0, can't benefit from movement bonuses.
- **Prone**: Movement is reduced, attackers have advantage in melee but disadvantage in ranged attacks.
- **Petrified**: Speed becomes 0, fully incapacitated, damage resistance to all types.
- **Frightened**: The creature can’t move closer to the source of fear.

### 3. **Perception and Senses Impact**  
These conditions primarily impact the character’s ability to perceive their environment.

- **Blinded**: Can’t see, disadvantage on attack rolls and saving throws involving sight, others have advantage attacking them.
- **Deafened**: Can’t hear, fails any hearing-based checks.
- **Invisible**: Other creatures can’t see them, advantage on attack rolls, attackers have disadvantage.

### 4. **Mental Influence and Behavior Modification**  
These conditions change how the character interacts with others and influence behavior.

- **Charmed**: Can’t attack charmer or target them with harmful effects, considers them friendly.
- **Frightened**: Disadvantage on attack rolls and saving throws, can’t move closer to source of fear.

### 5. **Health and Combat-Related Impairments**  
These conditions impose specific combat or health-related disadvantages.

- **Poisoned**: Disadvantage on attack rolls and ability checks.

---

### Proposed Categories for Combat Engine

1. **Action Impairment**:  
   Conditions that prevent or restrict taking actions. This can be abstracted into a "disabled" flag or "restricted_actions" attribute for each character.
   - Includes: **Incapacitated, Stunned, Paralyzed, Unconscious, Restrained**

2. **Movement Restriction**:  
   Conditions that limit or reduce a character’s movement or ability to reposition.
   - Includes: **Grappled, Prone, Petrified, Frightened**

3. **Perception Impairment**:  
   Conditions that impact sight, hearing, or the ability to be perceived by others.
   - Includes: **Blinded, Deafened, Invisible**

4. **Mental/Behavioral Influence**:  
   Conditions that affect decision-making or prevent specific hostile actions.
   - Includes: **Charmed, Frightened**

5. **Combat Debuff**:  
   Conditions that impact combat abilities without fully disabling actions or movement.
   - Includes: **Poisoned**

### Implementation Strategy

1. **Action and Movement Flags**:  
   Each character could have attributes like `can_take_actions`, `can_move`, and `can_react`, which are toggled by conditions. Action restrictions would simply toggle these attributes.

2. **Modifiers and Disadvantages**:  
   Conditions that impose disadvantage on attack rolls or saving throws (e.g., **Blinded, Poisoned**) could apply a `disadvantage_attack_roll` or `disadvantage_saving_throw` flag.

3. **Perception and Awareness**:  
   Conditions like **Blinded** and **Invisible** would modify perception-related checks. For example, a `perception_penalty` attribute could control visibility.

4. **Removal Mechanisms**:  
   For conditions that last until removed or require specific actions (like **Grappled** or **Charmed**), we could abstract this into a `removal_conditions` attribute that checks for specific actions (e.g., saving throws, dispelling magic).

---

By categorizing the conditions this way, we can reduce the complexity of individual condition handling and focus on broader attributes like action restriction, movement impairment, or perception changes. Let me know if you want to proceed with implementing this categorization!

### Standarized format for action restriction attributes

{
    "actions": "none | restricted | normal",
    "reactions": "none | normal",
    "movement": "none | restricted | 0 | normal",
    "attack_roll": "advantage | disadvantage | advantage_against | normal",
    "saving_throw": "disadvantage | normal",
    "melee_critical_hit": "yes | no",
    "damage_resistance": "resistant | normal"
}
