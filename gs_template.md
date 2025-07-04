{
    "players": [
        {
            "name": "string",
            "hp": "integer",
            "ac": "integer",
            "strength": "integer",
            "dexterity": "integer",
            "constitution": "integer",
            "intelligence": "integer",
            "wisdom": "integer",
            "charisma": "integer",
            "class_type": "string",  // e.g., "wizard", "sorcerer", "fighter"
            "damage": "string", // e.g., "1d8", "3d6"
            "inventory": [
                {
                    "name": "string",
                    "type": "string",  // e.g., "melee", "ranged", "magic"
                    "damage": "string",  // e.g., "1d8", "3d6"
                    "finesse": "boolean",
                    "versatile": {
                        "one_hand": "string",  // e.g., "1d8"
                        "two_hands": "string"  // e.g., "1d10"
                    },
                    "mod": "string"  // e.g., "strength", "dexterity", "intelligence"
                }
            ],
            "spells": [
                {
                    "name": "string",
                    "type": "string",  // e.g., "damage", "healing", "buff", "utility"
                    "damage": "string",  // e.g., "3d4+3" (optional)
                    "healing": "string",  // e.g., "1d8+3" (optional)
                    "effect": {
                        "attribute": "string",  // e.g., "ac", "health", "visibility"
                        "modifier": "integer or string",  // e.g., +5, "bright"
                        "duration": "integer"  // in rounds
                    },
                    "save": "string",  // e.g., "dexterity" (optional)
                    "dc": "integer",  // Difficulty class_type for saving throw (optional)
                    "targeting": "string"  // e.g., "single", "aoe", "self"
                }
            ],
            "conditions": {
                "condition_name": "duration in rounds"
            }
        }
    ],
    "npcs": [
        {
            "name": "string",
            "hp": "integer",
            "ac": "integer",
            "strength": "integer",
            "dexterity": "integer",
            "constitution": "integer",
            "intelligence": "integer",
            "wisdom": "integer",
            "charisma": "integer",
            "class_type": "string",  // e.g., "wizard", "fighter", "sorcerer"
            "damage": "string", // e.g., "1d8", "3d6"
            "inventory": [
                {
                    "name": "string",
                    "type": "string",
                    "damage": "string",  // e.g., "1d12"
                    "finesse": "boolean",
                    "mod": "string"  // e.g., "strength"
                }
            ],
            "spells": [
                {
                    "name": "string",
                    "type": "string",  // e.g., "damage", "healing", "buff", "utility"
                    "damage": "string",  // e.g., "3d4+3" (optional)
                    "healing": "string",  // e.g., "1d8+3" (optional)
                    "effect": {
                        "attribute": "string",  // e.g., "ac", "health", "visibility"
                        "modifier": "integer or string",  // e.g., +5, "bright"
                        "duration": "integer"  // in rounds
                    },
                    "save": "string",  // e.g., "dexterity" (optional)
                    "dc": "integer",  // Difficulty class_type for saving throw (optional)
                    "targeting": "string"  // e.g., "single", "aoe", "self"
                }
            ],
            "conditions": {
                "condition_name": "duration in rounds"
            }
        }
    ]
}
