#!/usr/bin/env python3
"""
Test report generator for the combat engine.
Generates detailed reports of test results and saves them to files.
"""

import json
import os
import datetime
from typing import Dict, List, Any

class TestReportGenerator:
    def __init__(self, output_dir="test_reports"):
        self.output_dir = output_dir
        self.test_results = {
            "offensive_tests": {},
            "defensive_tests": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_date": datetime.datetime.now().isoformat()
            }
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def add_offensive_test_result(self, spell_name: str, output_text: str, analysis: Dict[str, bool]):
        """Add results from an offensive spell test."""
        self.test_results["offensive_tests"][spell_name] = {
            "type": "offensive",
            "output": output_text,
            "analysis": analysis,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.test_results["summary"]["total_tests"] += 1
        
        # Count passed/failed based on analysis
        if analysis.get("spell_casting", False) and analysis.get("condition_application", False):
            self.test_results["summary"]["passed_tests"] += 1
        else:
            self.test_results["summary"]["failed_tests"] += 1
    
    def add_defensive_test_result(self, spell_name: str, output_text: str, analysis: Dict[str, bool]):
        """Add results from a defensive spell test."""
        self.test_results["defensive_tests"][spell_name] = {
            "type": "defensive",
            "output": output_text,
            "analysis": analysis,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.test_results["summary"]["total_tests"] += 1
        
        # Count passed/failed based on analysis
        if analysis.get("spell_casting", False):
            self.test_results["summary"]["passed_tests"] += 1
        else:
            self.test_results["summary"]["failed_tests"] += 1
    
    def generate_detailed_report(self) -> str:
        """Generate a detailed HTML report."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/detailed_report_{timestamp}.html"
        
        html_content = self._generate_html_report()
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
    
    def generate_summary_report(self) -> str:
        """Generate a summary JSON report."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/summary_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        return filename
    
    def generate_markdown_report(self) -> str:
        """Generate a markdown report."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/markdown_report_{timestamp}.md"
        
        markdown_content = self._generate_markdown_report()
        
        with open(filename, 'w') as f:
            f.write(markdown_content)
        
        return filename
    
    def _generate_html_report(self) -> str:
        """Generate HTML content for the detailed report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Combat Engine Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .test-section {{ margin: 20px 0; }}
        .test-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .passed {{ border-left: 5px solid #4CAF50; }}
        .failed {{ border-left: 5px solid #f44336; }}
        .analysis {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .output {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Combat Engine Test Report</h1>
        <p>Generated on: {self.test_results['summary']['test_date']}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {self.test_results['summary']['total_tests']}</p>
        <p><strong>Passed:</strong> {self.test_results['summary']['passed_tests']}</p>
        <p><strong>Failed:</strong> {self.test_results['summary']['failed_tests']}</p>
        <p><strong>Success Rate:</strong> {(self.test_results['summary']['passed_tests'] / max(1, self.test_results['summary']['total_tests']) * 100):.1f}%</p>
    </div>
"""
        
        # Add offensive tests
        html += """
    <div class="test-section">
        <h2>Offensive Spell Tests</h2>
"""
        
        for spell_name, result in self.test_results["offensive_tests"].items():
            is_passed = result["analysis"].get("spell_casting", False) and result["analysis"].get("condition_application", False)
            css_class = "passed" if is_passed else "failed"
            
            html += f"""
        <div class="test-item {css_class}">
            <h3>{spell_name}</h3>
            <p class="timestamp">Tested: {result['timestamp']}</p>
            
            <div class="analysis">
                <h4>Analysis:</h4>
                <ul>
"""
            
            for check, passed in result["analysis"].items():
                status = "✅" if passed else "❌"
                html += f"                    <li>{status} {check.replace('_', ' ').title()}</li>\n"
            
            html += """
                </ul>
            </div>
            
            <div class="output">
                <h4>Output:</h4>
                <div class="output-content">
"""
            html += result["output"]
            html += """
                </div>
            </div>
        </div>
"""
        
        # Add defensive tests
        html += """
    </div>
    
    <div class="test-section">
        <h2>Defensive Spell Tests</h2>
"""
        
        for spell_name, result in self.test_results["defensive_tests"].items():
            is_passed = result["analysis"].get("spell_casting", False)
            css_class = "passed" if is_passed else "failed"
            
            html += f"""
        <div class="test-item {css_class}">
            <h3>{spell_name}</h3>
            <p class="timestamp">Tested: {result['timestamp']}</p>
            
            <div class="analysis">
                <h4>Analysis:</h4>
                <ul>
"""
            
            for check, passed in result["analysis"].items():
                status = "✅" if passed else "❌"
                html += f"                    <li>{status} {check.replace('_', ' ').title()}</li>\n"
            
            html += """
                </ul>
            </div>
            
            <div class="output">
                <h4>Output:</h4>
                <div class="output-content">
"""
            html += result["output"]
            html += """
                </div>
            </div>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown content for the report."""
        markdown = f"""# Combat Engine Test Report

Generated on: {self.test_results['summary']['test_date']}

## Summary

- **Total Tests:** {self.test_results['summary']['total_tests']}
- **Passed:** {self.test_results['summary']['passed_tests']}
- **Failed:** {self.test_results['summary']['failed_tests']}
- **Success Rate:** {(self.test_results['summary']['passed_tests'] / max(1, self.test_results['summary']['total_tests']) * 100):.1f}%

## Offensive Spell Tests

"""
        
        for spell_name, result in self.test_results["offensive_tests"].items():
            is_passed = result["analysis"].get("spell_casting", False) and result["analysis"].get("condition_application", False)
            status = "✅ PASSED" if is_passed else "❌ FAILED"
            
            markdown += f"### {spell_name} - {status}\n\n"
            markdown += f"**Tested:** {result['timestamp']}\n\n"
            
            markdown += "**Analysis:**\n"
            for check, passed in result["analysis"].items():
                status_icon = "✅" if passed else "❌"
                markdown += f"- {status_icon} {check.replace('_', ' ').title()}\n"
            
            markdown += "\n**Output:**\n```\n"
            markdown += result["output"]
            markdown += "\n```\n\n---\n\n"
        
        markdown += "## Defensive Spell Tests\n\n"
        
        for spell_name, result in self.test_results["defensive_tests"].items():
            is_passed = result["analysis"].get("spell_casting", False)
            status = "✅ PASSED" if is_passed else "❌ FAILED"
            
            markdown += f"### {spell_name} - {status}\n\n"
            markdown += f"**Tested:** {result['timestamp']}\n\n"
            
            markdown += "**Analysis:**\n"
            for check, passed in result["analysis"].items():
                status_icon = "✅" if passed else "❌"
                markdown += f"- {status_icon} {check.replace('_', ' ').title()}\n"
            
            markdown += "\n**Output:**\n```\n"
            markdown += result["output"]
            markdown += "\n```\n\n---\n\n"
        
        return markdown
    
    def print_summary(self):
        """Print a summary to the console."""
        print("\n" + "="*60)
        print("TEST REPORT SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.test_results['summary']['total_tests']}")
        print(f"Passed: {self.test_results['summary']['passed_tests']}")
        print(f"Failed: {self.test_results['summary']['failed_tests']}")
        print(f"Success Rate: {(self.test_results['summary']['passed_tests'] / max(1, self.test_results['summary']['total_tests']) * 100):.1f}%")
        
        if self.test_results['summary']['failed_tests'] > 0:
            print("\nFailed Tests:")
            for test_type in ['offensive_tests', 'defensive_tests']:
                for spell_name, result in self.test_results[test_type].items():
                    if test_type == 'offensive_tests':
                        is_passed = result["analysis"].get("spell_casting", False) and result["analysis"].get("condition_application", False)
                    else:
                        is_passed = result["analysis"].get("spell_casting", False)
                    
                    if not is_passed:
                        print(f"  - {spell_name} ({test_type.replace('_', ' ')})")
        
        print("="*60) 