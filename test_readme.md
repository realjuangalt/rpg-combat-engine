# Combat Engine Testing Framework

This document describes the comprehensive testing framework for the D&D 5e Combat Engine, including automated tests, condition testing, integration tests, and logging systems.

## Table of Contents
- [Overview](#overview)
- [Testing Scripts](#testing-scripts)
- [Test Game States](#test-game-states)
- [Logging System](#logging-system)
- [Running Tests](#running-tests)
- [Test Reports](#test-reports)
- [Debug Mode](#debug-mode)

## Overview

The combat engine includes a comprehensive testing framework designed to validate:
- Spell casting and effects
- Condition application and removal
- AI decision making
- Combat flow and mechanics
- Unified effect system functionality
- Integration between all systems

## Testing Scripts

### 1. `automated_test.py`
**Purpose**: Comprehensive automated testing of all spells and combat mechanics

**Features**:
- Tests offensive spells (damage, conditions, debuffs)
- Tests defensive spells (healing, buffs, condition removal)
- Simulates player input automatically
- Validates spell effects and target selection
- Generates detailed pass/fail reports

**Usage**:
```bash
python3 automated_test.py
```

**Test Categories**:
- **Offensive Tests**: Fireball, Lightning Bolt, Stunning Strike, Blinding Light
- **Defensive Tests**: Cure Wounds, Bless, Lesser Restoration, Greater Restoration
- **Condition Tests**: Stunned, Blinded, Poisoned effects
- **AI Tests**: Healer and support AI decision making

### 2. `condition_test.py`
**Purpose**: Specialized testing for condition application and removal scenarios

**Features**:
- Tests condition application from spells
- Tests healer AI response to conditions
- Tests condition removal spells
- Validates unified effect system
- Tests condition stacking and duration

**Usage**:
```bash
python3 condition_test.py
```

**Test Scenarios**:
- Player applies condition to target
- Healer AI detects and attempts to remove conditions
- Condition removal spells work correctly
- Condition duration tracking

### 3. `integration_tests.py`
**Purpose**: End-to-end integration testing of combat systems

**Features**:
- Tests complete combat flow
- Validates initiative system
- Tests turn order and action resolution
- Validates combat end conditions
- Tests advantage/disadvantage mechanics

**Usage**:
```bash
python3 integration_tests.py
```

**Integration Test Areas**:
- Combat initialization and initiative
- Turn-based action resolution
- Effect processing and timing
- Combat termination conditions
- Character status tracking

### 4. `test_report_generator.py`
**Purpose**: Generates comprehensive test reports in multiple formats

**Features**:
- HTML reports with detailed analysis
- JSON reports for programmatic access
- Markdown reports for documentation
- Color-coded pass/fail indicators
- Detailed error analysis

**Output Formats**:
- `detailed_report_YYYYMMDD_HHMMSS.html`
- `test_results_YYYYMMDD_HHMMSS.json`
- `summary_report_YYYYMMDD_HHMMSS.md`

## Test Game States

### 1. `game_state_offensive_test.json`
**Purpose**: Testing offensive spells and damage mechanics

**Characters**:
- **Player**: Condition Caster (Wizard with condition spells)
- **Targets**: High HP Target (80 HP, strong melee stats)

**Spells Available**:
- Fireball (AOE damage)
- Lightning Bolt (line damage)
- Stunning Strike (condition application)
- Blinding Light (utility condition)

### 2. `game_state_defensive_test.json`
**Purpose**: Testing healing, buffing, and condition removal

**Characters**:
- **Player**: Support Caster (Cleric with healing/buff spells)
- **Targets**: Wounded Ally (low HP for healing tests)

**Spells Available**:
- Cure Wounds (healing)
- Bless (buff)
- Lesser Restoration (condition removal)
- Greater Restoration (mass condition removal)

### 3. `game_state_condition_test.json`
**Purpose**: Testing condition application and AI response

**Characters**:
- **Player**: Condition Caster (Wizard with condition spells)
- **Healer NPC**: Support AI with healing/removal spells
- **Conditioned Warrior**: NPC with conditions for testing removal
- **High HP Target**: 80 HP target for condition application

**AI Types**:
- **Healer AI**: Prioritizes healing, condition removal, buffing
- **Support AI**: Focuses on buffs and condition removal
- **Aggressive AI**: Default attack-focused behavior

## Logging System

### Debug Mode
The combat engine includes a comprehensive logging system controlled by the `DEBUG_MODE` flag:

```python
DEBUG_MODE = True  # Set to False for normal play, True for detailed logs
```

### Log Levels and Categories

#### 1. Combat Flow Logs
- Initiative rolls and order
- Turn transitions
- Action selection and execution
- Combat end conditions

#### 2. Spell Casting Logs
- Spell selection and targeting
- Attack rolls and saving throws
- Damage calculation
- Effect application

#### 3. Condition/Effect Logs
- Condition application and removal
- Effect duration tracking
- Stacking rule application
- Timing-based effect processing

#### 4. AI Decision Logs
- AI type and decision process
- Target selection reasoning
- Spell choice logic
- Priority-based decision making

#### 5. Error and Validation Logs
- Input validation
- Error handling
- State consistency checks
- Debugging information

### Log Format
Logs use Rich library formatting for enhanced readability:
- **Bold colors**: Important events (combat start, critical hits)
- **Status indicators**: Pass/fail, success/failure
- **Detailed context**: Roll results, modifiers, targets
- **Timing information**: Round numbers, turn order

### Log Output
- **Console**: Real-time colored output during execution
- **File**: `game_session.log` for persistent logging
- **Test Reports**: Structured analysis in HTML/JSON/Markdown

## Running Tests

### Basic Test Execution
```bash
# Run automated tests
python3 automated_test.py

# Run condition tests
python3 condition_test.py

# Run integration tests
python3 integration_tests.py
```

### Test Configuration
Tests can be configured with various parameters:

```python
# Limit combat rounds for testing
engine = CombatEngine(players, npcs, max_rounds=5)

# Enable debug mode for detailed logs
DEBUG_MODE = True

# Custom test scenarios
test_scenarios = [
    "offensive_spells",
    "defensive_spells", 
    "condition_application",
    "ai_decision_making"
]
```

### Test Validation
Each test validates specific aspects:

1. **Spell Validation**:
   - Correct damage calculation
   - Proper target selection
   - Effect application and duration
   - Saving throw mechanics

2. **Condition Validation**:
   - Application from spells
   - Duration tracking
   - Removal via spells/saving throws
   - Effect stacking rules

3. **AI Validation**:
   - Decision making logic
   - Target prioritization
   - Spell selection
   - Action execution

4. **Integration Validation**:
   - Combat flow integrity
   - State consistency
   - Turn order maintenance
   - End condition detection

## Test Reports

### Report Structure
Test reports include:

1. **Summary Statistics**:
   - Total tests run
   - Pass/fail counts
   - Success percentage
   - Execution time

2. **Detailed Analysis**:
   - Individual test results
   - Error descriptions
   - Expected vs actual outcomes
   - Performance metrics

3. **Recommendations**:
   - Areas for improvement
   - Bug identification
   - Optimization suggestions

### Report Formats

#### HTML Reports
- Interactive tables
- Color-coded results
- Expandable details
- Export functionality

#### JSON Reports
- Machine-readable format
- Programmatic analysis
- Integration with CI/CD
- Data processing capabilities

#### Markdown Reports
- Documentation-friendly
- Version control compatible
- Easy to read and share
- GitHub integration

## Debug Mode

### Enabling Debug Mode
```python
# In combat_engine.py
DEBUG_MODE = True  # Enable detailed logging
```

### Debug Features
- **Detailed Spell Logs**: All spell casting steps logged
- **AI Decision Logs**: AI reasoning and choices
- **Effect Tracking**: Condition/effect application and removal
- **Roll Details**: All dice rolls with modifiers
- **State Changes**: Character state modifications

### Debug Output Examples
```
[bold cyan]--- Combat Begins ---[/bold cyan]
[bold blue]Applying unified effect Stunned to High HP Target[/bold blue]
[bold green]Advantage roll: 15 and 18 - using higher: 18[/bold green]
[bold yellow]Healer AI decides to remove conditions from Conditioned Warrior[/bold yellow]
```

### Performance Considerations
- Debug mode increases execution time
- Log files can grow large
- Consider disabling for production use
- Use selective logging for specific issues

## Best Practices

### Test Development
1. **Isolate Test Cases**: Each test should focus on one specific feature
2. **Use Representative Data**: Test with realistic character stats and spells
3. **Validate Edge Cases**: Test boundary conditions and error scenarios
4. **Maintain Test Data**: Keep test game states up to date

### Logging Guidelines
1. **Use Appropriate Levels**: Info for normal flow, Debug for details
2. **Include Context**: Always log relevant state information
3. **Be Consistent**: Use consistent formatting and terminology
4. **Avoid Noise**: Don't log unnecessary information

### Report Analysis
1. **Review Failures First**: Focus on failed tests for immediate issues
2. **Check Patterns**: Look for systematic problems across multiple tests
3. **Validate Fixes**: Re-run tests after making changes
4. **Track Trends**: Monitor test success rates over time

## Troubleshooting

### Common Issues
1. **Test Failures**: Check game state files for valid data
2. **Logging Issues**: Verify DEBUG_MODE setting and file permissions
3. **AI Problems**: Validate AI type assignments in game states
4. **Effect Issues**: Check condition definitions in consolidated_conditions.json

### Debugging Steps
1. Enable debug mode
2. Run specific test scenarios
3. Review detailed logs
4. Check test report analysis
5. Validate game state consistency

This testing framework ensures the combat engine is robust, reliable, and maintains D&D 5e compliance while providing comprehensive validation of all systems. 