# Game State Schema Documentation

This document provides detailed information on the structure and intended logic of the game state schema defined in `gs_schema.json`. It addresses gaps and limitations in the JSON Schema logic, particularly where conditional validations or complex constraints could not be fully implemented due to issues with the `jsonschema` library's interpretation of advanced constructs like `if-then-else`, `allOf`, and `oneOf`.

## Overview

The `gs_schema.json` file defines the structure for the game state data used in the D&D 5e Combat Engine. It ensures that data in `game_state.json` adheres to a consistent format, covering players, NPCs, environmental effects, and combat-related attributes. The schema is designed to align with D&D 5e rules while accommodating the needs of automated combat resolution and AI-generated content.

## Schema Structure

### Root Object
- **Type**: `object`
- **Properties**:
  - `players`: An array of player character objects.
  - `npcs`: An array of non-player character objects.
  - `environment`: An array of environmental effects or conditions affecting the combat area.

### Character Objects (Players and NPCs)
- **Type**: `object`
- **Key Properties**:
  - `name`: A string representing the character's name.
  - `level`: An integer indicating the character's level.
  - `class`: A string representing the character's class.
  - `stats`: An object containing ability scores (e.g., strength, dexterity).
  - `hp`: An integer for current hit points.
  - `max_hp`: An integer for maximum hit points.
  - `ac`: An integer for armor class.
  - `speed`: An integer for movement speed in feet per turn.
  - `initiative`: An integer for the character's initiative roll.
  - `conditions`: An array of condition objects affecting the character.
  - `inventory`: An array of item objects.
  - `spells`: An array of spell objects.
  - `adv_disadv`: A string indicating advantage or disadvantage status (`advantage`, `disadvantage`, or `none`).
  - `description`: A string providing a brief description of the character.

### Spells and Effects
- **Type**: `object`
- **Key Properties**:
  - `name`: A string for the spell or effect name.
  - `level`: An integer or string indicating the spell level.
  - `type`: A string indicating the type (e.g., `buff`, `debuff`, `damage`, `heal`, `condition`).
  - `attribute`: A string specifying the affected attribute (e.g., `strength`, `hp`, `adv_disadv`).
  - `modifier`: A string or integer representing the modification or effect value.
  - `duration`: An integer for the number of rounds the effect lasts.
  - `target`: A string indicating the target scope (`single`, `aoe`, `self`).
  - `save`: A string for the saving throw type, if applicable.
  - `description`: A string describing the spell or effect.

### Conditions
- **Type**: `object`
- **Key Properties**:
  - `name`: A string for the condition name.
  - `duration`: An integer for the number of rounds the condition lasts.
  - `effect`: A string describing the condition's impact.

### Items
- **Type**: `object`
- **Key Properties**:
  - `name`: A string for the item name.
  - `type`: A string indicating the item type (e.g., `weapon`, `armor`, `potion`).
  - `effect`: An object or string describing the item's effect, if any.
  - `description`: A string providing details about the item.

### Environmental Effects
- **Type**: `object`
- **Key Properties**:
  - `name`: A string for the environmental effect name.
  - `effect`: A string or object describing the effect on the combat area.
  - `duration`: An integer for the number of rounds the effect lasts.

## Limitations and Intended Logic

### Modifier Field in Spell Effects
- **Current Schema Definition**: The `modifier` field in spell effects is currently defined as accepting any string or integer. This was a temporary workaround to resolve persistent validation errors caused by the `jsonschema` library's inconsistent handling of conditional logic (`if-then-else`, `allOf`, `oneOf`).
- **Intended Logic**: The `modifier` field should adhere to the following constraints based on the `type` and `attribute` of the effect:
  - For effects with `type: "buff"` or `type: "debuff"` and `attribute: "adv_disadv"`, `modifier` must be one of `advantage` or `disadvantage`.
  - For effects with `type: "condition"` and `attribute: "adv_disadv"`, `modifier` must be `none`.
  - For effects modifying numerical stats (e.g., `attribute: "strength"`, `attribute: "hp"`), `modifier` should be an integer representing the change in value.
  - For other conditions or effects (e.g., `attribute: "condition"`), `modifier` should be a string describing the condition (e.g., `unconscious`, `prone`).
- **Reason for Simplification**: Attempts to encode this logic using JSON Schema's conditional constructs resulted in validation failures due to library limitations. For instance, using `if-then-else` to enforce `modifier` as `advantage` or `disadvantage` when `attribute` is `adv_disadv` and `type` is `buff` or `debuff` did not work as expected. Similarly, `allOf` and `oneOf` combinations failed to correctly validate across multiple conditions.
- **Impact**: Without these constraints, invalid data (e.g., `modifier: "unconscious"` for `adv_disadv`) may pass validation, requiring manual checks or additional logic in scripts like `combat_engine.py` to handle edge cases.
- **Future Resolution**: Consider using a different validation library or custom validation code in Python to enforce these rules if `jsonschema` limitations persist. Alternatively, split `modifier` into distinct fields (e.g., `numeric_modifier`, `status_modifier`) to simplify validation.

### Duration and Target Constraints
- **Current Schema Definition**: `duration` and `target` fields are broadly defined to accept integers and strings respectively, with minimal constraints.
- **Intended Logic**: Certain effects or spells should have predefined `duration` values (e.g., instantaneous spells with `duration: 0`) or restricted `target` values based on D&D 5e rules (e.g., `Fireball` must be `aoe`). These are not currently enforced in the schema.
- **Impact**: Data may include non-standard values that do not align with game rules, requiring additional checks in the combat engine.
- **Future Resolution**: Add enumerated values or conditional checks if validation library support improves, or document expected values here for reference during data generation.

### Advantage/Disadvantage Field (`adv_disadv`)
- **Current Schema Definition**: Defined as a string with enumerated values `advantage`, `disadvantage`, or `none`.
- **Intended Logic**: This field should reflect the net effect of all active buffs, debuffs, and conditions on a character. The combat engine (`combat_engine.py`) should compute this dynamically based on active effects, but the schema only validates the static value.
- **Impact**: The schema does not prevent inconsistent data if effects are not correctly applied or updated in `game_state.json`.
- **Future Resolution**: Consider adding a note or metadata in the schema to indicate this field is computed, not manually set, or implement validation in the combat engine to ensure consistency.

## Best Practices for Data Consistency
1. **Validation Before Use**: Always run `tools/refine.py` to validate `game_state.json` against `gs_schema.json` before using it in the combat engine or other scripts.
2. **Manual Checks for Modifier**: Since `modifier` constraints are not enforced, manually verify or use script logic to ensure values like `advantage` or `disadvantage` are used correctly for `adv_disadv` effects.
3. **AI-Generated Data**: When using tools like `character_generator.py` or `spell_empora.py`, include clear instructions in API prompts to adhere to the intended logic for fields like `modifier`, `duration`, and `target`.
4. **Schema Updates**: If discrepancies are found, update `gs_schema.json` and document any new limitations or intended logic here.

## Conclusion
This documentation serves as a companion to `gs_schema.json`, providing clarity on the intended structure and rules for game state data in the D&D 5e Combat Engine. While the JSON Schema handles basic structural validation, the limitations outlined here highlight areas where additional care or custom logic is needed to ensure full compliance with D&D 5e mechanics and project goals.