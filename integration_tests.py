#!/usr/bin/env python3
"""
Integration tests for the combat engine.
Tests the entire system end-to-end with various scenarios.
"""

import json
import sys
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import time
from typing import Dict, List, Any

# Add the current directory to the path so we can import combat_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from combat_engine import CombatEngine, load_characters_from_json, UnifiedEffect, EffectDuration, EffectTiming
from test_report_generator import TestReportGenerator

class IntegrationTester:
    def __init__(self):
        self.report_generator = TestReportGenerator("integration_reports")
        self.test_results = {}
        
    def test_basic_combat_flow(self):
        """Test basic combat flow without spells."""
        print("\n" + "="*60)
        print("TESTING BASIC COMBAT FLOW")
        print("="*60)
        
        # Create simple test scenario
        test_data = {
            "players": [
                {
                    "name": "Test Fighter",
                    "hp": 30,
                    "ac": 15,
                    "strength": 16,
                    "dexterity": 14,
                    "constitution": 14,
                    "intelligence": 10,
                    "wisdom": 12,
                    "charisma": 8,
                    "class_type": "fighter",
                    "damage": "1d8",
                    "inventory": [{"name": "Longsword", "type": "melee", "damage": "1d8", "mod": "strength"}],
                    "spells": [],
                    "conditions": {}
                }
            ],
            "npcs": [
                {
                    "name": "Test Goblin",
                    "hp": 15,
                    "ac": 13,
                    "strength": 12,
                    "dexterity": 14,
                    "constitution": 10,
                    "intelligence": 8,
                    "wisdom": 8,
                    "charisma": 6,
                    "class_type": "fighter",
                    "damage": "1d6",
                    "inventory": [{"name": "Scimitar", "type": "melee", "damage": "1d6", "mod": "dexterity"}],
                    "spells": [],
                    "conditions": {}
                }
            ]
        }
        
        # Save test data
        with open('test_basic_combat.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        # Run test
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                players, npcs = load_characters_from_json('test_basic_combat.json')
                engine = CombatEngine(players, npcs)
                engine.max_rounds = 3
                
                # Mock inputs for basic combat
                inputs = ["1", "1", "1", "1", "1", "1", "1", "1", "1"]  # Attack, weapon, target repeated
                self._run_with_mock_inputs(engine, inputs)
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        # Analyze results
        analysis = {
            "combat_started": "Combat Begins" in output_text,
            "initiative_rolled": "rolls" in output_text and "for initiative" in output_text,
            "attacks_processed": "attacks" in output_text and "with" in output_text,
            "damage_applied": "takes" in output_text and "damage" in output_text,
            "combat_ended": "Combat has ended" in output_text,
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Basic Combat Flow", analysis)
        self.test_results["basic_combat"] = {"output": output_text, "analysis": analysis}
        
        # Cleanup
        if os.path.exists('test_basic_combat.json'):
            os.remove('test_basic_combat.json')
    
    def test_unified_effect_system(self):
        """Test the unified effect system thoroughly."""
        print("\n" + "="*60)
        print("TESTING UNIFIED EFFECT SYSTEM")
        print("="*60)
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                # Test effect creation and application
                effect = UnifiedEffect(
                    name="Test Effect",
                    effect_type="buff",
                    source="test",
                    duration_type=EffectDuration.FIXED,
                    duration_value=2,
                    timing=EffectTiming.END_OF_TURN,
                    attributes={"strength": 2, "adv_disadv": "advantage"}
                )
                
                # Create a test character
                from combat_engine import Character
                char = Character(
                    name="Test Char",
                    hp=20, ac=15, strength=14, dexterity=12, constitution=12,
                    intelligence=10, wisdom=10, charisma=8,
                    damage="1d6", inventory=[], class_type="fighter"
                )
                
                # Apply effect
                effect.apply(char)
                print(f"Applied effect. Strength: {char.strength}, Adv/Disadv: {char.adv_disadv}")
                
                # Test duration decrement
                expired = effect.decrement_duration()
                print(f"Duration after decrement: {effect.current_duration}, Expired: {expired}")
                
                # Test removal
                effect.remove(char)
                print(f"After removal. Strength: {char.strength}, Adv/Disadv: {char.adv_disadv}")
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        analysis = {
            "effect_created": "Test Effect" in output_text,
            "effect_applied": "Applied effect" in output_text,
            "attributes_modified": "Strength:" in output_text and "Adv/Disadv:" in output_text,
            "duration_tracked": "Duration after decrement" in output_text,
            "effect_removed": "After removal" in output_text,
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Unified Effect System", analysis)
        self.test_results["unified_effects"] = {"output": output_text, "analysis": analysis}
    
    def test_condition_application_and_removal(self):
        """Test condition application and removal through saving throws."""
        print("\n" + "="*60)
        print("TESTING CONDITION APPLICATION AND REMOVAL")
        print("="*60)
        
        # Create test scenario with conditions
        test_data = {
            "players": [
                {
                    "name": "Test Caster",
                    "hp": 25,
                    "ac": 14,
                    "strength": 10,
                    "dexterity": 12,
                    "constitution": 12,
                    "intelligence": 16,
                    "wisdom": 14,
                    "charisma": 10,
                    "class_type": "wizard",
                    "damage": "1d4",
                    "inventory": [{"name": "Dagger", "type": "melee", "damage": "1d4", "mod": "dexterity"}],
                    "spells": [
                        {
                            "name": "Test Stun",
                            "type": "condition",
                            "effect": {"attribute": "actions", "modifier": "stunned", "duration": 2},
                            "save": "constitution",
                            "dc": 12,
                            "targeting": "single"
                        }
                    ],
                    "conditions": {}
                }
            ],
            "npcs": [
                {
                    "name": "Test Target",
                    "hp": 20,
                    "ac": 12,
                    "strength": 12,
                    "dexterity": 10,
                    "constitution": 10,
                    "intelligence": 8,
                    "wisdom": 8,
                    "charisma": 6,
                    "class_type": "fighter",
                    "damage": "1d6",
                    "inventory": [{"name": "Club", "type": "melee", "damage": "1d6", "mod": "strength"}],
                    "spells": [],
                    "conditions": {}
                }
            ]
        }
        
        # Save test data
        with open('test_conditions.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                players, npcs = load_characters_from_json('test_conditions.json')
                engine = CombatEngine(players, npcs)
                engine.max_rounds = 4
                
                # Mock inputs: cast spell, then wait for condition to expire
                inputs = ["2", "1", "1", "3", "3", "3", "3"]  # Cast spell, target, then move actions
                self._run_with_mock_inputs(engine, inputs)
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        analysis = {
            "spell_casted": "Test Stun" in output_text,
            "condition_applied": "stunned" in output_text.lower(),
            "saving_throw_processed": "saving throw" in output_text.lower(),
            "condition_expired": "Removed expired effect" in output_text,
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Condition Application and Removal", analysis)
        self.test_results["condition_removal"] = {"output": output_text, "analysis": analysis}
        
        # Cleanup
        if os.path.exists('test_conditions.json'):
            os.remove('test_conditions.json')
    
    def test_advantage_disadvantage_system(self):
        """Test the advantage/disadvantage system."""
        print("\n" + "="*60)
        print("TESTING ADVANTAGE/DISADVANTAGE SYSTEM")
        print("="*60)
        
        # Create test scenario with blinded condition
        test_data = {
            "players": [
                {
                    "name": "Test Fighter",
                    "hp": 30,
                    "ac": 15,
                    "strength": 16,
                    "dexterity": 14,
                    "constitution": 14,
                    "intelligence": 10,
                    "wisdom": 12,
                    "charisma": 8,
                    "class_type": "fighter",
                    "damage": "1d8",
                    "inventory": [{"name": "Longsword", "type": "melee", "damage": "1d8", "mod": "strength"}],
                    "spells": [
                        {
                            "name": "Blinding Light",
                            "type": "utility",
                            "effect": {"attribute": "vision", "modifier": "blinded", "duration": 2},
                            "save": "constitution",
                            "dc": 14,
                            "targeting": "single"
                        }
                    ],
                    "conditions": {}
                }
            ],
            "npcs": [
                {
                    "name": "Test Target",
                    "hp": 25,
                    "ac": 13,
                    "strength": 12,
                    "dexterity": 10,
                    "constitution": 10,
                    "intelligence": 8,
                    "wisdom": 8,
                    "charisma": 6,
                    "class_type": "fighter",
                    "damage": "1d6",
                    "inventory": [{"name": "Club", "type": "melee", "damage": "1d6", "mod": "strength"}],
                    "spells": [],
                    "conditions": {}
                }
            ]
        }
        
        # Save test data
        with open('test_advantage.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                players, npcs = load_characters_from_json('test_advantage.json')
                engine = CombatEngine(players, npcs)
                engine.max_rounds = 3
                
                # Mock inputs: cast blinding spell, then attack
                inputs = ["2", "1", "1", "1", "1", "1"]  # Cast spell, target, then attack
                self._run_with_mock_inputs(engine, inputs)
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        analysis = {
            "blinding_spell_casted": "Blinding Light" in output_text,
            "blinded_condition_applied": "blinded" in output_text.lower(),
            "disadvantage_applied": "disadvantage" in output_text.lower(),
            "disadvantage_rolls_logged": "Disadvantage roll:" in output_text,
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Advantage/Disadvantage System", analysis)
        self.test_results["advantage_disadvantage"] = {"output": output_text, "analysis": analysis}
        
        # Cleanup
        if os.path.exists('test_advantage.json'):
            os.remove('test_advantage.json')
    
    def test_combat_end_conditions(self):
        """Test that combat ends properly when all characters are defeated."""
        print("\n" + "="*60)
        print("TESTING COMBAT END CONDITIONS")
        print("="*60)
        
        # Create test scenario with low HP characters
        test_data = {
            "players": [
                {
                    "name": "Weak Fighter",
                    "hp": 5,
                    "ac": 15,
                    "strength": 16,
                    "dexterity": 14,
                    "constitution": 14,
                    "intelligence": 10,
                    "wisdom": 12,
                    "charisma": 8,
                    "class_type": "fighter",
                    "damage": "1d8",
                    "inventory": [{"name": "Longsword", "type": "melee", "damage": "1d8", "mod": "strength"}],
                    "spells": [],
                    "conditions": {}
                }
            ],
            "npcs": [
                {
                    "name": "Weak Goblin",
                    "hp": 3,
                    "ac": 13,
                    "strength": 12,
                    "dexterity": 14,
                    "constitution": 10,
                    "intelligence": 8,
                    "wisdom": 8,
                    "charisma": 6,
                    "class_type": "fighter",
                    "damage": "1d6",
                    "inventory": [{"name": "Scimitar", "type": "melee", "damage": "1d6", "mod": "dexterity"}],
                    "spells": [],
                    "conditions": {}
                }
            ]
        }
        
        # Save test data
        with open('test_combat_end.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                players, npcs = load_characters_from_json('test_combat_end.json')
                engine = CombatEngine(players, npcs)
                engine.max_rounds = 5
                
                # Mock inputs: attack until someone dies
                inputs = ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"]
                self._run_with_mock_inputs(engine, inputs)
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        output_text = output.getvalue()
        
        analysis = {
            "combat_started": "Combat Begins" in output_text,
            "characters_defeated": "has been defeated" in output_text,
            "combat_ended": "Combat has ended" in output_text,
            "proper_ending_message": "victorious" in output_text or "defeated" in output_text,
            "no_errors": "ERROR" not in output_text and "Traceback" not in output_text
        }
        
        self._print_analysis("Combat End Conditions", analysis)
        self.test_results["combat_end"] = {"output": output_text, "analysis": analysis}
        
        # Cleanup
        if os.path.exists('test_combat_end.json'):
            os.remove('test_combat_end.json')
    
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
    
    def run_all_integration_tests(self):
        """Run all integration tests."""
        print("STARTING INTEGRATION TESTS")
        print("="*60)
        
        self.test_basic_combat_flow()
        self.test_unified_effect_system()
        self.test_condition_application_and_removal()
        self.test_advantage_disadvantage_system()
        self.test_combat_end_conditions()
        
        # Generate reports
        print("\n" + "="*60)
        print("GENERATING INTEGRATION TEST REPORTS")
        print("="*60)
        
        # Add all test results to report generator
        for test_name, result in self.test_results.items():
            if "basic_combat" in test_name or "advantage_disadvantage" in test_name or "combat_end" in test_name:
                # These are offensive-style tests
                self.report_generator.add_offensive_test_result(test_name, result["output"], result["analysis"])
            else:
                # These are defensive-style tests
                self.report_generator.add_defensive_test_result(test_name, result["output"], result["analysis"])
        
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
        print("INTEGRATION TESTS COMPLETE")
        print("="*60)

def main():
    """Run all integration tests."""
    tester = IntegrationTester()
    tester.run_all_integration_tests()

if __name__ == "__main__":
    main() 