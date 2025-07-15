#!/usr/bin/env python3
"""
Condition testing script for the combat engine.
Tests condition application by player and removal by healer AI.
"""

import json
import sys
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import time

# Add the current directory to the path so we can import combat_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from combat_engine import CombatEngine, load_characters_from_json
from test_report_generator import TestReportGenerator

class ConditionTester:
    def __init__(self):
        self.report_generator = TestReportGenerator("condition_reports")
        self.test_results = {}
        
    def test_condition_application_and_removal(self):
        """Test the full cycle of condition application and removal."""
        print("\n" + "="*60)
        print("TESTING CONDITION APPLICATION AND REMOVAL")
        print("="*60)
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                # Load the condition test scenario
                players, npcs = load_characters_from_json('game_state_condition_test.json')
                engine = CombatEngine(players, npcs)
                engine.max_rounds = 6
                
                # Mock inputs: Player casts conditions on High HP Target, healer removes them
                inputs = [
                    # Round 1: Cast Blinding Light on High HP Target
                    "2", "1", "2",  # Cast spell, Blinding Light, target High HP Target
                    # Round 2: Cast Poison Spray on High HP Target  
                    "2", "2", "2",  # Cast spell, Poison Spray, target High HP Target
                    # Round 3: Cast Hold Person on High HP Target
                    "2", "3", "2",  # Cast spell, Hold Person, target High HP Target
                    # Round 4: Cast Stunning Strike on High HP Target
                    "2", "4", "2",  # Cast spell, Stunning Strike, target High HP Target
                    # Round 5: Attack to see effects
                    "1", "1", "2",  # Attack, weapon, target High HP Target
                    # Round 6: Another attack
                    "1", "1", "2"   # Attack, weapon, target High HP Target
                ]
                
                self._run_with_mock_inputs(engine, inputs)
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        # Analyze results
        analysis = {
            "blinded_condition_applied": "blinded" in output_text.lower() and "applying" in output_text.lower(),
            "poisoned_condition_applied": "poisoned" in output_text.lower() and "applying" in output_text.lower(),
            "incapacitated_condition_applied": "incapacitated" in output_text.lower() and "applying" in output_text.lower(),
            "stunned_condition_applied": "stunned" in output_text.lower() and "applying" in output_text.lower(),
            "healer_ai_activated": "healer" in output_text.lower() and "decides" in output_text.lower(),
            "condition_removal_attempted": "removing" in output_text.lower() or "removal" in output_text.lower(),
            "healing_attempted": "heal" in output_text.lower() and "decides" in output_text.lower(),
            "buffing_attempted": "buff" in output_text.lower() and "decides" in output_text.lower(),
            "advantage_disadvantage_applied": "advantage" in output_text.lower() or "disadvantage" in output_text.lower(),
            "high_hp_target_targeted": "high hp target" in output_text.lower() or "target" in output_text.lower(),
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Condition Application and Removal", analysis)
        self.test_results["condition_cycle"] = {"output": output_text, "analysis": analysis}
        
        # Add to report generator
        self.report_generator.add_offensive_test_result("Condition Cycle Test", output_text, analysis)
    
    def test_healer_ai_priorities(self):
        """Test that healer AI follows proper priorities."""
        print("\n" + "="*60)
        print("TESTING HEALER AI PRIORITIES")
        print("="*60)
        
        # Create a scenario where the healer has multiple options
        test_data = {
            "players": [
                {
                    "name": "Test Player",
                    "hp": 20,
                    "ac": 15,
                    "strength": 14,
                    "dexterity": 12,
                    "constitution": 12,
                    "intelligence": 10,
                    "wisdom": 10,
                    "charisma": 8,
                    "class_type": "fighter",
                    "damage": "1d8",
                    "inventory": [{"name": "Sword", "type": "melee", "damage": "1d8", "mod": "strength"}],
                    "spells": [],
                    "conditions": {}
                }
            ],
            "npcs": [
                {
                    "name": "Smart Healer",
                    "hp": 30,
                    "ac": 14,
                    "strength": 10,
                    "dexterity": 10,
                    "constitution": 12,
                    "intelligence": 10,
                    "wisdom": 16,
                    "charisma": 12,
                    "class_type": "cleric",
                    "damage": "1d6",
                    "inventory": [{"name": "Mace", "type": "melee", "damage": "1d6", "mod": "strength"}],
                    "spells": [
                        {
                            "name": "Cure Wounds",
                            "type": "healing",
                            "healing": "1d8+3",
                            "targeting": "single"
                        },
                        {
                            "name": "Lesser Restoration",
                            "type": "utility",
                            "effect": {"attribute": "condition_removal", "modifier": "remove_one"},
                            "targeting": "single"
                        },
                        {
                            "name": "Bless",
                            "type": "buff",
                            "effect": {"attribute": "adv_disadv", "modifier": "advantage", "duration": 3},
                            "targeting": "single"
                        }
                    ],
                    "conditions": {},
                    "ai_type": "healer"
                },
                {
                    "name": "Wounded Ally",
                    "hp": 5,  # Low HP to trigger healing priority
                    "ac": 13,
                    "strength": 14,
                    "dexterity": 12,
                    "constitution": 12,
                    "intelligence": 8,
                    "wisdom": 8,
                    "charisma": 6,
                    "class_type": "fighter",
                    "damage": "1d6",
                    "inventory": [{"name": "Axe", "type": "melee", "damage": "1d6", "mod": "strength"}],
                    "spells": [],
                    "conditions": {"poisoned": {"active": True, "duration": 2}},  # Has condition
                    "ai_type": "aggressive"
                }
            ]
        }
        
        # Save test data
        with open('test_healer_priorities.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                players, npcs = load_characters_from_json('test_healer_priorities.json')
                engine = CombatEngine(players, npcs)
                engine.max_rounds = 3
                
                # Mock inputs: Just let the healer AI make decisions
                inputs = ["1", "1", "1", "1", "1", "1"]  # Player attacks
                self._run_with_mock_inputs(engine, inputs)
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        # Analyze healer AI behavior
        analysis = {
            "healer_ai_activated": "healer" in output_text.lower() and "decides" in output_text.lower(),
            "healing_priority": "heal" in output_text.lower() and "decides" in output_text.lower(),
            "condition_removal_priority": "remove conditions" in output_text.lower(),
            "buffing_priority": "buff" in output_text.lower() and "decides" in output_text.lower(),
            "proper_targeting": "wounded ally" in output_text.lower() or "ally" in output_text.lower(),
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Healer AI Priorities", analysis)
        self.test_results["healer_priorities"] = {"output": output_text, "analysis": analysis}
        
        # Add to report generator
        self.report_generator.add_defensive_test_result("Healer AI Priorities", output_text, analysis)
        
        # Cleanup
        if os.path.exists('test_healer_priorities.json'):
            os.remove('test_healer_priorities.json')
    
    def _run_with_mock_inputs(self, engine, inputs):
        """Run combat with mock inputs."""
        original_input = input
        input_index = [0]
        
        def mock_input(prompt=""):
            if input_index[0] < len(inputs):
                result = inputs[input_index[0]]
                input_index[0] += 1
                return result
            else:
                return "1"  # Default to attack
        
        import builtins
        builtins.input = mock_input
        
        try:
            engine.start_combat()
        finally:
            builtins.input = original_input
    
    def _print_analysis(self, test_name, analysis):
        """Print analysis results."""
        print(f"\nANALYSIS FOR {test_name}:")
        for check, passed in analysis.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check.replace('_', ' ').title()}")
    
    def run_all_condition_tests(self):
        """Run all condition-related tests."""
        print("STARTING CONDITION TESTS")
        print("="*60)
        
        self.test_condition_application_and_removal()
        self.test_healer_ai_priorities()
        
        # Generate reports
        print("\n" + "="*60)
        print("GENERATING CONDITION TEST REPORTS")
        print("="*60)
        
        # Generate reports
        html_report = self.report_generator.generate_detailed_report()
        json_report = self.report_generator.generate_summary_report()
        markdown_report = self.report_generator.generate_markdown_report()
        
        print(f"✅ HTML Report: {html_report}")
        print(f"✅ JSON Report: {json_report}")
        print(f"✅ Markdown Report: {markdown_report}")
        
        # Print summary
        self.report_generator.print_summary()
        
        print("\n" + "="*60)
        print("CONDITION TESTS COMPLETE")
        print("="*60)

def main():
    """Run all condition tests."""
    tester = ConditionTester()
    tester.run_all_condition_tests()

if __name__ == "__main__":
    main() 