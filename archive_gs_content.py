import json
import os

def ensure_directory(directory):
    """Ensure the specified directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def split_game_state():
    """Read game_state.json and split into individual JSON files for players, NPCs, items, and spells."""
    # Define output directories
    players_dir = "players"
    npcs_dir = "npcs"
    items_dir = "items"
    spells_dir = "spells"
    
    # Ensure directories exist
    ensure_directory(players_dir)
    ensure_directory(npcs_dir)
    ensure_directory(items_dir)
    ensure_directory(spells_dir)
    
    try:
        # Read the game state JSON
        with open("game_state.json", "r") as f:
            game_state = json.load(f)
        
        # Process player characters
        for player in game_state.get("players", []):
            player_name = player.get("name", "unknown_player").replace(" ", "_").lower()
            player_file = os.path.join(players_dir, f"character_{player_name}.json")
            with open(player_file, "w") as f:
                json.dump(player, f, indent=2)
            print(f"Saved player data to {player_file}")
        
        # Process NPCs
        for npc in game_state.get("npcs", []):
            npc_name = npc.get("name", "unknown_npc").replace(" ", "_").lower()
            npc_file = os.path.join(npcs_dir, f"npc_{npc_name}.json")
            with open(npc_file, "w") as f:
                json.dump(npc, f, indent=2)
            print(f"Saved NPC data to {npc_file}")
        
        # Process items from all characters (players and NPCs)
        item_index = 0
        for player in game_state.get("players", []):
            for item in player.get("inventory", []):
                item_name = item.get("name", f"item_{item_index}").replace(" ", "_").lower()
                item_file = os.path.join(items_dir, f"item_{item_name}.json")
                with open(item_file, "w") as f:
                    json.dump(item, f, indent=2)
                print(f"Saved item data to {item_file}")
                item_index += 1
        
        for npc in game_state.get("npcs", []):
            for item in npc.get("inventory", []):
                item_name = item.get("name", f"item_{item_index}").replace(" ", "_").lower()
                item_file = os.path.join(items_dir, f"item_{item_name}.json")
                with open(item_file, "w") as f:
                    json.dump(item, f, indent=2)
                print(f"Saved item data to {item_file}")
                item_index += 1
        
        # Process spells from all characters (players and NPCs)
        spell_index = 0
        for player in game_state.get("players", []):
            for spell in player.get("spells", []):
                spell_name = spell.get("name", f"spell_{spell_index}").replace(" ", "_").lower()
                spell_file = os.path.join(spells_dir, f"spell_{spell_name}.json")
                with open(spell_file, "w") as f:
                    json.dump(spell, f, indent=2)
                print(f"Saved spell data to {spell_file}")
                spell_index += 1
        
        for npc in game_state.get("npcs", []):
            for spell in npc.get("spells", []):
                spell_name = spell.get("name", f"spell_{spell_index}").replace(" ", "_").lower()
                spell_file = os.path.join(spells_dir, f"spell_{spell_name}.json")
                with open(spell_file, "w") as f:
                    json.dump(spell, f, indent=2)
                print(f"Saved spell data to {spell_file}")
                spell_index += 1
    
    except FileNotFoundError:
        print("Error: game_state.json not found. Please ensure the file exists in the project directory.")
    except json.JSONDecodeError:
        print("Error: game_state.json contains invalid JSON. Please check the file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    print("Splitting game state data into individual JSON files...")
    split_game_state()
    print("Process completed.")