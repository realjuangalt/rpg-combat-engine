import json
import jsonschema
from jsonschema import ValidationError
from rich.console import Console
from rich.traceback import install

# Initialize rich traceback handler
install()
console = Console()

def load_json_file(filename):
    """Load a JSON file and return its contents, ensuring fresh load by clearing any cache."""
    try:
        # Clear any potential cache by reading the file directly each time
        with open(filename, 'r') as file:
            return json.load(file)
    except Exception as e:
        console.print(f"[bold red]Error loading {filename}: {str(e)}[/bold red]")
        return None

def check_discrepancies(data, schema, filename="game_state.json"):
    """Check the data against the schema and print discrepancies."""
    try:
        jsonschema.validate(instance=data, schema=schema)
        console.print("[bold green]No discrepancies found. The game state data conforms to the schema.[/bold green]")
    except ValidationError as e:
        console.print("[bold red]Discrepancies found in game state data:[/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]")
        # Attempt to extract the name of the object if available
        object_name = None
        try:
            path_parts = e.json_path.split('.')
            base_path = None
            index = None
            if 'spells' in path_parts:
                index = path_parts[path_parts.index('spells') + 1].strip('[]')
                base_path = '.'.join(path_parts[:path_parts.index('spells') + 2]) + '.name'
            elif 'inventory' in path_parts:
                index = path_parts[path_parts.index('inventory') + 1].strip('[]')
                base_path = '.'.join(path_parts[:path_parts.index('inventory') + 2]) + '.name'
            if base_path and index:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    current = data
                    for part in path_parts[:path_parts.index('spells' if 'spells' in path_parts else 'inventory')]:
                        if '[' in part:
                            key, idx = part.split('[')
                            idx = int(idx.strip(']'))
                            current = current.get(key, [])[idx]
                        else:
                            current = current.get(part, {})
                    target_list = current.get('spells' if 'spells' in path_parts else 'inventory', [])
                    target_index = int(index)
                    if target_index < len(target_list):
                        object_name = target_list[target_index].get('name', None)
        except Exception as ex:
            console.print(f"[red]Could not retrieve object name: {ex}[/red]")
        if object_name:
            console.print(f"[cyan]Object Name: {object_name}[/cyan]")
        console.print(f"[yellow]Path to error: {e.json_path}[/yellow]")
        console.print(f"[yellow]Failed validation rule: {e.validator}[/yellow]")
        console.print(f"[yellow]Expected: {e.validator_value}[/yellow]")
        console.print(f"[yellow]Found: {e.instance}[/yellow]")
        # Attempt to find the line number in the JSON file
        # Line number approximation has been removed due to inaccuracy.
        # If needed, manually inspect the file using the path to error.

def find_line_number(filename, json_path):
    """Attempt to find the approximate line number in the JSON file based on the JSON path."""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        # Simple heuristic: count the number of opening braces/brackets to estimate depth
        # This is not perfect but can give a rough approximation
        path_parts = json_path.split('.')
        line_estimate = 1
        brace_count = 0
        bracket_count = 0
        for i, line in enumerate(lines, 1):
            brace_count += line.count('{')
            brace_count -= line.count('}')
            bracket_count += line.count('[')
            bracket_count -= line.count(']')
            if brace_count + bracket_count >= len(path_parts):
                line_estimate = i
                break
        return line_estimate
    except Exception as e:
        console.print(f"[yellow]Could not estimate line number: {str(e)}[/yellow]")
        return None

def main():
    """Main function to load files and check for discrepancies."""
    console.print("[bold blue]Starting validation of game_state.json against gs_schema.json...[/bold blue]")
    
    # Load schema and game state data, ensuring fresh load
    console.print("[cyan]Loading schema and data with cache refresh...[/cyan]")
    schema = load_json_file("gs_schema.json")
    if schema is None:
        console.print("[bold red]Cannot proceed without schema. Exiting.[/bold red]")
        return
    
    game_state = load_json_file("game_state.json")
    if game_state is None:
        console.print("[bold red]Cannot proceed without game state data. Exiting.[/bold red]")
        return
    
    # Check for discrepancies
    check_discrepancies(game_state, schema)
    console.print("[bold blue]Validation complete.[/bold blue]")

if __name__ == "__main__":
    main()