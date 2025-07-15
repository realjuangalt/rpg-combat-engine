#!/usr/bin/env python3
"""
Automated testing script for the combat engine.
Tests all spells systematically in both offensive and defensive scenarios.
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

class AutomatedTester:
    def __init__(self):
        self.test_results = []
        self.current_test = None
        self.report_generator = TestReportGenerator()
        
    def run_offensive_test(self, spell_index, spell_name):
        """Run a test for a specific offensive spell."""
        print(f"\n{'='*60}")
        print(f"TESTING OFFENSIVE SPELL: {spell_name}")
        print(f"{'='*60}")
        
        # Load the offensive test scenario
        players, npcs = load_characters_from_json('game_state_offensive_test.json')
        engine = CombatEngine(players, npcs)
        
        # Set up automated input for this test
        test_inputs = self._get_offensive_test_inputs(spell_index)
        
        # Capture output
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                # Start combat and run for a few rounds
                self._run_automated_combat(engine, test_inputs, max_rounds=3)
            except Exception as e:
                print(f"ERROR in test: {e}")
        
        # Analyze results
        output_text = output.getvalue()
        self._analyze_offensive_results(spell_name, output_text)
        
    def run_defensive_test(self, spell_index, spell_name):
        """Run a test for a specific defensive spell."""
        print(f"\n{'='*60}")
        print(f"TESTING DEFENSIVE SPELL: {spell_name}")
        print(f"{'='*60}")
        
        # Load the defensive test scenario
        players, npcs = load_characters_from_json('game_state_defensive_test.json')
        engine = CombatEngine(players, npcs)
        
        # Set up automated input for this test
        test_inputs = self._get_defensive_test_inputs(spell_index)
        
        # Capture output
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            try:
                # Start combat and run for a few rounds
                self._run_automated_combat(engine, test_inputs, max_rounds=3)
            except Exception as e:
                print(f"ERROR in test: {e}")
        
        # Analyze results
        output_text = output.getvalue()
        self._analyze_defensive_results(spell_name, output_text)
    
    def _get_offensive_test_inputs(self, spell_index):
        """Generate input sequence for offensive spell testing."""
        inputs = []
        
        # Round 1: Cast the spell
        inputs.extend([
            "2",  # Cast a Spell
            str(spell_index + 1),  # Spell number (1-indexed)
            "1"   # Target the first (and only) enemy
        ])
        
        # Round 2: Attack to see effects
        inputs.extend([
            "1",  # Attack
            "1",  # First weapon
            "1"   # Target the enemy
        ])
        
        # Round 3: Another spell or attack
        inputs.extend([
            "2",  # Cast a Spell
            "1",  # First spell
            "1"   # Target the enemy
        ])
        
        return inputs
    
    def _get_defensive_test_inputs(self, spell_index):
        """Generate input sequence for defensive spell testing."""
        inputs = []
        
        # Round 1: Cast the defensive spell
        inputs.extend([
            "2",  # Cast a Spell
            str(spell_index + 1),  # Spell number (1-indexed)
            "1"   # Target first ally (self)
        ])
        
        # Round 2: Attack to see if buffs work
        inputs.extend([
            "1",  # Attack
            "1",  # First weapon
            "1"   # Target first enemy
        ])
        
        # Round 3: Another defensive spell
        inputs.extend([
            "2",  # Cast a Spell
            "1",  # First spell
            "1"   # Target self
        ])
        
        return inputs
    
    def _run_automated_combat(self, engine, inputs, max_rounds=3):
        """Run combat with automated inputs."""
        # Monkey patch input function to return our test inputs
        original_input = input
        input_index = [0]
        
        def mock_input(prompt=""):
            if input_index[0] < len(inputs):
                result = inputs[input_index[0]]
                input_index[0] += 1
                return result
            else:
                return "1"  # Default to attack if we run out of inputs
        
        # Replace input function
        import builtins
        builtins.input = mock_input
        
        try:
            # Start combat but limit rounds
            engine.max_rounds = max_rounds
            engine.start_combat()
        finally:
            # Restore original input function
            builtins.input = original_input
    
    def _analyze_offensive_results(self, spell_name, output_text):
        """Analyze the results of an offensive spell test."""
        print(f"\nANALYSIS FOR {spell_name}:")
        
        # Get the condition this spell applies
        condition_name = self._get_spell_condition(spell_name)
        
        # Initialize analysis results
        analysis = {
            "spell_casting": False,
            "condition_application": False,
            "advantage_disadvantage": False,
            "effect_removal": False,
            "saving_throws": False,
            "damage_application": False,
            "condition_specific_effects": False,
            "stat_modifications": False,
            "no_errors": True
        }
        
        # Check for successful spell casting
        if f"successfully cast {spell_name}" in output_text:
            print("✅ Spell was cast successfully")
            analysis["spell_casting"] = True
        else:
            print("❌ Spell casting failed or not logged")
        
        # Check for condition application
        if "Applying unified effect" in output_text:
            print("✅ Condition/effect was applied")
            analysis["condition_application"] = True
        else:
            print("❌ No condition/effect application found")
        
        # Check for advantage/disadvantage
        if "Advantage roll:" in output_text or "Disadvantage roll:" in output_text:
            print("✅ Advantage/disadvantage rolls were logged")
            analysis["advantage_disadvantage"] = True
        
        # Check for effect removal
        if "Removing unified effect" in output_text:
            print("✅ Effects were properly removed")
            analysis["effect_removal"] = True
        
        # Check for saving throws
        if "saving throw" in output_text.lower():
            print("✅ Saving throws were processed")
            analysis["saving_throws"] = True
        
        # Check for damage application
        if "takes" in output_text and "damage" in output_text:
            print("✅ Damage was applied")
            analysis["damage_application"] = True
        
        # Check for condition-specific effects based on consolidated_conditions.json
        if condition_name:
            analysis["condition_specific_effects"] = self._check_condition_effects(condition_name, output_text)
            if analysis["condition_specific_effects"]:
                print(f"✅ {condition_name.title()} condition effects properly applied")
            else:
                print(f"❌ {condition_name.title()} condition effects not found")
        
        # Check for stat modifications (buffs/debuffs)
        if self._check_stat_modifications(spell_name, output_text):
            print("✅ Stat modifications applied")
            analysis["stat_modifications"] = True
        
        # Check for errors
        if "ERROR" in output_text or "Traceback" in output_text:
            print("❌ Errors found in test")
            analysis["no_errors"] = False
        else:
            print("✅ No errors detected")
        
        # Add to report generator
        self.report_generator.add_offensive_test_result(spell_name, output_text, analysis)
        
        return analysis
    
    def _get_spell_condition(self, spell_name):
        """Get the condition name that a spell applies based on spell name patterns."""
        spell_name_lower = spell_name.lower()
        
        # Map spell names to conditions
        spell_to_condition = {
            "blinding light": "blinded",
            "charm person": "charmed", 
            "thunderclap": "deafened",
            "cause fear": "frightened",
            "grasping vines": "grappled",
            "hold person": "incapacitated",
            "hold monster": "paralyzed",
            "flesh to stone": "petrified",
            "poison spray": "poisoned",
            "earth tremor": "prone",
            "entangle": "restrained",
            "stunning strike": "stunned",
            "sleep": "unconscious",
            "invisibility": "invisible"
        }
        
        return spell_to_condition.get(spell_name_lower)
    
    def _check_condition_effects(self, condition_name, output_text):
        """Check if the specific condition effects are properly applied."""
        condition_name_lower = condition_name.lower()
        
        # Check based on consolidated_conditions.json effects
        if condition_name_lower == "blinded":
            return ("disadvantage on attack rolls" in output_text or 
                   "disadvantage" in output_text and "attack" in output_text)
        
        elif condition_name_lower == "charmed":
            return "charmed" in output_text.lower()
        
        elif condition_name_lower == "deafened":
            return "deafened" in output_text.lower()
        
        elif condition_name_lower == "frightened":
            return ("frightened" in output_text.lower() or 
                   "disadvantage" in output_text and "fear" in output_text)
        
        elif condition_name_lower == "grappled":
            return ("grappled" in output_text.lower() or 
                   "movement" in output_text and "0" in output_text)
        
        elif condition_name_lower == "incapacitated":
            return ("incapacitated" in output_text.lower() or
                   "cannot act" in output_text.lower())
        
        elif condition_name_lower == "invisible":
            return ("invisible" in output_text.lower() or
                   "advantage" in output_text and "attack" in output_text)
        
        elif condition_name_lower == "paralyzed":
            return ("paralyzed" in output_text.lower() or
                   "advantage when attacking" in output_text)
        
        elif condition_name_lower == "petrified":
            return ("petrified" in output_text.lower() or
                   "stone" in output_text.lower())
        
        elif condition_name_lower == "poisoned":
            return ("poisoned" in output_text.lower() or
                   "disadvantage" in output_text and "poison" in output_text)
        
        elif condition_name_lower == "prone":
            return ("prone" in output_text.lower() or
                   "knocked down" in output_text.lower())
        
        elif condition_name_lower == "restrained":
            return ("restrained" in output_text.lower() or
                   "movement" in output_text and "0" in output_text)
        
        elif condition_name_lower == "stunned":
            return ("stunned" in output_text.lower() or
                   "cannot act" in output_text.lower())
        
        elif condition_name_lower == "unconscious":
            return ("unconscious" in output_text.lower() or
                   "sleep" in output_text.lower())
        
        return False
    
    def _check_stat_modifications(self, spell_name, output_text):
        """Check if stat modifications (buffs/debuffs) are applied."""
        spell_name_lower = spell_name.lower()
        
        # Check for common stat modification patterns
        stat_indicators = [
            "advantage", "disadvantage", "ac", "strength", "dexterity", 
            "constitution", "intelligence", "wisdom", "charisma", "hp",
            "movement", "speed", "damage", "attack", "saving throw"
        ]
        
        # Check if any stat modifications are mentioned
        for stat in stat_indicators:
            if stat in output_text.lower():
                return True
        
        return False
    
    def _analyze_defensive_results(self, spell_name, output_text):
        """Analyze the results of a defensive spell test."""
        print(f"\nANALYSIS FOR {spell_name}:")
        
        # Initialize analysis results
        analysis = {
            "spell_casting": False,
            "healing_applied": False,
            "buffs_applied": False,
            "condition_removal": False,
            "specific_defensive_effects": False,
            "no_errors": True
        }
        
        # Check for successful spell casting
        if f"successfully cast {spell_name}" in output_text or "cast buff" in output_text:
            print("✅ Spell was cast successfully")
            analysis["spell_casting"] = True
        else:
            print("❌ Spell casting failed or not logged")
        
        # Check for healing
        if "healed for" in output_text:
            print("✅ Healing was applied")
            analysis["healing_applied"] = True
        
        # Check for buffs
        if "advantage" in output_text.lower() or "buff" in output_text.lower():
            print("✅ Buffs were applied")
            analysis["buffs_applied"] = True
        
        # Check for condition removal
        if "removes" in output_text.lower() or "removal" in output_text.lower():
            print("✅ Condition removal was attempted")
            analysis["condition_removal"] = True
        
        # Check for specific defensive effects
        if "bless" in spell_name.lower() and "advantage" in output_text.lower():
            print("✅ Bless spell grants advantage")
            analysis["specific_defensive_effects"] = True
        elif "shield of faith" in spell_name.lower() and "ac" in output_text.lower():
            print("✅ Shield of Faith increases AC")
            analysis["specific_defensive_effects"] = True
        elif "lesser restoration" in spell_name.lower() and "removing" in output_text.lower():
            print("✅ Lesser Restoration removes conditions")
            analysis["specific_defensive_effects"] = True
        elif "greater restoration" in spell_name.lower() and "removing all conditions" in output_text.lower():
            print("✅ Greater Restoration removes all conditions")
            analysis["specific_defensive_effects"] = True
        elif "aid" in spell_name.lower() and "hp" in output_text.lower():
            print("✅ Aid spell increases HP")
            analysis["specific_defensive_effects"] = True
        
        # Check for errors
        if "ERROR" in output_text or "Traceback" in output_text:
            print("❌ Errors found in test")
            analysis["no_errors"] = False
        else:
            print("✅ No errors detected")
        
        # Add to report generator
        self.report_generator.add_defensive_test_result(spell_name, output_text, analysis)
        
        return analysis
    
    def run_all_offensive_tests(self):
        """Run tests for all offensive spells."""
        print("RUNNING ALL OFFENSIVE SPELL TESTS")
        print("="*60)
        
        # Load offensive test data to get spell list
        with open('game_state_offensive_test.json', 'r') as f:
            data = json.load(f)
        
        spells = data['players'][0]['spells']
        
        for i, spell in enumerate(spells):
            self.run_offensive_test(i, spell['name'])
            time.sleep(1)  # Brief pause between tests
    
    def run_all_defensive_tests(self):
        """Run tests for all defensive spells."""
        print("RUNNING ALL DEFENSIVE SPELL TESTS")
        print("="*60)
        
        # Load defensive test data to get spell list
        with open('game_state_defensive_test.json', 'r') as f:
            data = json.load(f)
        
        spells = data['players'][0]['spells']
        
        for i, spell in enumerate(spells):
            self.run_defensive_test(i, spell['name'])
            time.sleep(1)  # Brief pause between tests

def main():
    """Main function to run all tests."""
    tester = AutomatedTester()
    
    print("COMBAT ENGINE AUTOMATED TESTING")
    print("="*60)
    
    # Run offensive tests
    tester.run_all_offensive_tests()
    
    print("\n" + "="*60)
    print("OFFENSIVE TESTS COMPLETE")
    print("="*60)
    
    # Run defensive tests
    tester.run_all_defensive_tests()
    
    print("\n" + "="*60)
    print("GENERATING TEST REPORTS")
    print("="*60)
    
    # Generate all report types
    html_report = tester.report_generator.generate_detailed_report()
    json_report = tester.report_generator.generate_summary_report()
    markdown_report = tester.report_generator.generate_markdown_report()
    
    print(f"✅ HTML Report: {html_report}")
    print(f"✅ JSON Report: {json_report}")
    print(f"✅ Markdown Report: {markdown_report}")
    
    # Print summary
    tester.report_generator.print_summary()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main() 