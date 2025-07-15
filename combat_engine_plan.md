# Combat Engine Upgrade Plan

## 📊 Current State Analysis

### ✅ Working Systems
- Basic character creation and stats
- Initiative system
- Attack mechanics with weapons
- Spell casting framework
- Condition application system
- Effect system (partially working)
- Saving throw mechanics
- Combat loop structure

### ❌ Critical Issues Identified

#### 1. **Effect System Bugs**
- Effects are applied but not properly removed
- Duration counting is broken
- Advantage/disadvantage not applying correctly
- Effect removal logic has inconsistencies

#### 2. **Input Validation Issues**
- Empty spell lists cause crashes when selecting "Cast Spell"
- Invalid input (empty enter) crashes the engine
- No validation for weapon/spell selection

#### 3. **Condition System Problems**
- Charmed effect has no logic to affect targeting
- Mute/silence conditions don't exist
- Entangled/restrained conditions don't work properly
- Conditions don't properly affect spell casting abilities

#### 4. **Spatial System Missing**
- No distance/range calculations
- No movement system
- Melee vs ranged attack distinction missing
- No line of sight or positioning

#### 5. **Combat Loop Issues**
- Dead players not properly recognized
- Combat doesn't end when all players are defeated
- Initiative order not properly updated

#### 6. **Data Structure Issues**
- Duplicate condition files (conditions_apply.json vs action_restrictions.json)
- Schema needs descriptions for items/spells
- No real-time state management for multiple users

---

## 🎯 Phase 1: Core Bug Fixes (Priority 1)

### 1.1 Implement Unified Effect System
**Goal**: Replace dual condition/effect system with single unified system

**Tasks**:
- [ ] Create `UnifiedEffect` class to handle all character modifications
- [ ] Update `Character` class to use unified effects storage
- [ ] Create conversion functions for existing condition and spell data
- [ ] Implement proper stacking and duration tracking
- [ ] Add D&D 5e timing rules (end of turn, start of turn processing)
- [ ] Implement round-based vs turn-based effect expiration
- [ ] Add unified effect validation and error handling
- [ ] Create unit tests for unified effect system

**Files to modify**:
- `combat_engine.py` (add UnifiedEffect class, update Character class, remove old Effect class, add timing methods)
- `test_unified_effects.py` (new test file)

### 1.2 Fix Input Validation
**Goal**: Prevent crashes from invalid user input

**Tasks**:
- [ ] Add input validation in `get_player_action()`
- [ ] Handle empty spell lists gracefully
- [ ] Add try/catch blocks for integer conversion
- [ ] Provide default actions when invalid input is given
- [ ] Add input sanitization

**Files to modify**:
- `combat_engine.py` (get_player_action method)

### 1.3 Fix Combat Loop Issues
**Goal**: Ensure combat ends properly and dead characters are handled correctly

**Tasks**:
- [ ] Fix `is_combat_over()` to properly detect all players defeated
- [ ] Update initiative order when characters die
- [ ] Add proper death state handling
- [ ] Fix round counting and turn management
- [ ] Add combat state validation
- [ ] Implement proper effect timing (end of turn vs start of turn processing)

**Files to modify**:
- `combat_engine.py` (CombatEngine class)

---

## 🎯 Phase 2: Condition System Overhaul (Priority 2)

### 2.1 Consolidate and Migrate to Unified Effect System
**Goal**: Consolidate duplicate condition files and convert to unified format

**Tasks**:
- [ ] **Consolidate condition files**: Merge `conditions_apply.json` and `action_restrictions.json` into single file
- [ ] **Use better structure**: Adopt the comprehensive structure from `conditions_apply.json`
- [ ] **Add missing conditions**: Include all 14 D&D 5e conditions (blinded, charmed, deafened, frightened, grappled, incapacitated, invisible, paralyzed, petrified, poisoned, prone, restrained, stunned, unconscious)
- [ ] **Update to unified format**: Convert consolidated conditions to unified effect structure
- [ ] **Add D&D 5e timing**: Include proper timing rules (end_of_turn, start_of_turn)
- [ ] **Add stacking rules**: Define how conditions stack and interact
- [ ] **Update application logic**: Modify combat engine to use unified system
- [ ] **Test all conditions**: Verify all conditions work correctly

**Files to modify**:
- `combat_engine/conditions/consolidated_conditions.json` (new unified file)
- `combat_engine/conditions/conditions_apply.json` (remove after consolidation)
- `combat_engine/action_restrictions.json` (remove after consolidation)
- `combat_engine.py` (update to use unified system, add conversion functions)

### 2.2 Implement Advanced Effect Logic
**Goal**: Make unified effects affect all relevant systems (targeting, spell casting, etc.)

**Tasks**:
- [ ] Implement charmed effect targeting logic
- [ ] Add mute/silence effects for spell casting
- [ ] Fix entangled/restrained movement restrictions
- [ ] Add effect-based action restrictions
- [ ] Implement effect stacking and interaction rules
- [ ] Add effect interaction with spatial system (when implemented)

**Files to modify**:
- `combat_engine.py` (Character and CombatEngine classes, add interaction logic)

### 2.3 Add Unified Effect Testing
**Goal**: Ensure all unified effects work correctly with automated tests

**Tasks**:
- [ ] Create comprehensive unified effect test suite
- [ ] Test effect application and removal
- [ ] Test effect interactions and stacking
- [ ] Test effect duration tracking
- [ ] Test effect effects on combat actions
- [ ] Test conversion from old condition/effect formats

**Files to create**:
- `test_unified_effects.py`

---

## 🎯 Phase 3: Spatial System Implementation (Priority 3)

### 3.1 Add Position and Movement System
**Goal**: Implement grid-based positioning and movement

**Tasks**:
- [ ] Add position attributes to Character class (x, y coordinates)
- [ ] Implement movement validation and pathfinding
- [ ] Add distance calculation methods
- [ ] Implement movement action system
- [ ] Add movement range indicators

**Files to modify**:
- `combat_engine.py` (Character class)
- `spatial_system.py` (new file)

### 3.2 Implement Range and Line of Sight
**Goal**: Add proper range calculations and targeting restrictions

**Tasks**:
- [ ] Implement melee range checking (5 feet)
- [ ] Add ranged weapon range calculations
- [ ] Implement spell range checking
- [ ] Add line of sight calculations
- [ ] Implement cover and obstacle system

**Files to modify**:
- `combat_engine.py` (Character and CombatEngine classes)
- `spatial_system.py`

### 3.3 Update Schema for Spatial Data
**Goal**: Add position and movement data to character schema

**Tasks**:
- [ ] Update `gs_schema.json` to include position data
- [ ] Update `schema_template.md` with new fields
- [ ] Add movement speed and range fields
- [ ] Add weapon/spell range information
- [ ] Update character loading system

**Files to modify**:
- `gs_schema.json`
- `schema_template.md`
- `combat_engine.py` (load_characters_from_json)

---

## 🎯 Phase 4: Schema and Data Improvements (Priority 4)

### 4.1 Add Descriptions to Items and Spells
**Goal**: Enhance data structure with descriptive information

**Tasks**:
- [ ] Add description field to all items in schema
- [ ] Add description field to all spells in schema
- [ ] Update existing character data with descriptions
- [ ] Create description generation system
- [ ] Update VTT to display descriptions

**Files to modify**:
- `gs_schema.json`
- `schema_template.md`
- Character JSON files

### 4.2 Improve Data Validation
**Goal**: Ensure all data conforms to schema and is valid

**Tasks**:
- [ ] Add JSON schema validation to character loading
- [ ] Implement data integrity checks
- [ ] Add automatic data repair for common issues
- [ ] Create data validation tests
- [ ] Add error reporting for invalid data

**Files to modify**:
- `combat_engine.py` (load_characters_from_json)
- `data_validator.py` (new file)

---

## 🎯 Phase 5: Real-time State Management (Priority 5)

### 5.1 Design State Management Architecture
**Goal**: Create system for managing multiple users' game states

**Options to consider**:
1. **Centralized State Server**: Single source of truth with WebSocket connections
2. **Distributed State**: Each client maintains state with synchronization
3. **Hybrid Approach**: Centralized combat state, distributed character state

**Recommendation**: Start with centralized state server for combat, distributed for character management

### 5.2 Implement State Synchronization
**Goal**: Ensure all clients see the same game state

**Tasks**:
- [ ] Design state update protocol
- [ ] Implement state serialization/deserialization
- [ ] Add state validation and conflict resolution
- [ ] Create state change logging
- [ ] Implement rollback capabilities

**Files to create**:
- `state_manager.py`
- `state_sync.py`
- `game_state.py`

### 5.3 Add Multi-user Support
**Goal**: Support multiple players in the same combat session

**Tasks**:
- [ ] Add user session management
- [ ] Implement turn-based action queuing
- [ ] Add player permission system
- [ ] Create spectator mode
- [ ] Add session persistence

**Files to modify**:
- `combat_engine.py` (CombatEngine class)
- `session_manager.py` (new file)

---

## 🎯 Phase 6: Testing and Quality Assurance (Ongoing)

### 6.1 Create Comprehensive Test Suite
**Goal**: Ensure all systems work correctly with automated testing

**Tasks**:
- [ ] Unit tests for all classes and methods
- [ ] Integration tests for combat scenarios
- [ ] Performance tests for real-time operations
- [ ] Stress tests for multi-user scenarios
- [ ] Edge case testing

**Files to create**:
- `tests/` directory with comprehensive test suite
- `test_combat.py`
- `test_characters.py`
- `test_spells.py`
- `test_conditions.py`
- `test_spatial.py`

### 6.2 Add Error Handling and Logging
**Goal**: Improve debugging and error recovery

**Tasks**:
- [ ] Add comprehensive error handling
- [ ] Implement structured logging
- [ ] Add error recovery mechanisms
- [ ] Create error reporting system
- [ ] Add performance monitoring

**Files to modify**:
- All combat engine files
- `logger.py` (new file)

---

## 🎯 Phase 7: VTT Integration Preparation (Priority 6)

### 7.1 Create API Interface
**Goal**: Prepare combat engine for VTT integration

**Tasks**:
- [ ] Design REST API for combat actions
- [ ] Implement WebSocket interface for real-time updates
- [ ] Add action validation endpoints
- [ ] Create state query endpoints
- [ ] Add authentication and authorization

**Files to create**:
- `api/` directory
- `combat_api.py`
- `websocket_handler.py`

### 7.2 Add VTT-Specific Features
**Goal**: Add features needed by the VTT interface

**Tasks**:
- [ ] Add action preview system
- [ ] Implement range indicator calculations
- [ ] Add movement path validation
- [ ] Create target highlighting system
- [ ] Add action undo/redo capability

**Files to modify**:
- `combat_engine.py`
- `vtt_interface.py` (new file)

---

## 📋 Implementation Strategy

### Development Approach
1. **Start with Phase 1**: Implement unified effect system in combat_engine.py
2. **Incremental Development**: Test each phase thoroughly before moving to next
3. **Backward Compatibility**: Ensure existing character data still works
4. **Documentation**: Update documentation with each change
5. **Testing**: Write tests for all new features
6. **Refactor Later**: Consider extracting to separate files only if combat_engine.py becomes unwieldy

### File Organization
```
combat_engine/
├── core/
│   ├── combat_engine.py (refactored with unified effects)
│   ├── character.py (extracted)
│   └── spatial_system.py (new)
├── data/
│   ├── consolidated_conditions.json (unified conditions + effects)
│   ├── class_data.py
│   └── schema/
├── api/
│   ├── combat_api.py (new)
│   └── websocket_handler.py (new)
├── tests/
│   ├── test_combat.py
│   ├── test_unified_effects.py
│   └── test_spatial.py
└── utils/
    ├── logger.py (new)
    ├── validator.py (new)
    └── state_manager.py (new)
```

### Timeline Estimate
- **Phase 1**: 1-2 weeks (critical bugs)
- **Phase 2**: 2-3 weeks (condition system)
- **Phase 3**: 3-4 weeks (spatial system)
- **Phase 4**: 1 week (schema updates)
- **Phase 5**: 2-3 weeks (state management)
- **Phase 6**: Ongoing (testing)
- **Phase 7**: 2-3 weeks (VTT integration)

**Total Estimated Time**: 11-16 weeks

---

## 🚀 Success Criteria

### Phase 1 Success
- [ ] All effects apply and remove correctly
- [ ] No crashes from invalid input
- [ ] Combat ends properly when all players are defeated
- [ ] All existing tests pass

### Phase 2 Success
- [ ] All conditions work as expected
- [ ] Charmed condition affects targeting
- [ ] Mute/silence prevents spell casting
- [ ] Entangled/restrained affects movement and attacks

### Phase 3 Success
- [ ] Characters can move on grid
- [ ] Range calculations work correctly
- [ ] Line of sight affects targeting
- [ ] Movement validation prevents invalid moves

### Overall Success
- [ ] Combat engine is stable and bug-free
- [ ] All systems integrate properly
- [ ] VTT can successfully connect and use combat engine
- [ ] Multi-user sessions work correctly
- [ ] Performance is acceptable for real-time use

---

## 🔧 Technical Considerations

### Performance Requirements
- Combat actions must complete in <100ms
- State updates must propagate in <50ms
- Support for 10+ concurrent users
- Memory usage <100MB per session

### Scalability Considerations
- Modular design for easy extension
- Plugin system for custom conditions/effects
- Database integration for persistent state
- Load balancing for multiple combat sessions

### Security Considerations
- Input validation and sanitization
- Authentication for user actions
- Authorization for game state changes
- Audit logging for all actions

This plan provides a comprehensive roadmap for upgrading the combat engine while maintaining stability and preparing it for VTT integration. 