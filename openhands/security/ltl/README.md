# LTL Security Analyzer

## Overview

The LTL (Linear Temporal Logic) Security Analyzer is a new approach to security analysis in OpenHands that:

1. **Converts events to predicates**: Transforms OpenHands events into atomic predicates
2. **Checks LTL specifications**: Validates event histories against temporal logic specifications  
3. **Detects security violations**: Identifies when agent behavior violates security patterns

## Architecture

### Core Components

- **`ltl_analyzer.py`** - Main analyzer class that extends `SecurityAnalyzer`
- **`ltl_predicates.py`** - Predicate extraction utilities
- **`ltl_specs.py`** - LTL specification format and checker

### How It Works

1. **Event Processing**: Each event is processed to extract relevant predicates
2. **Predicate History**: Maintains a history of predicate sets over time
3. **Specification Checking**: Evaluates LTL formulas against the predicate history
4. **Violation Detection**: Reports violations with severity levels

## Predicate Examples

The analyzer extracts predicates like:

- `action_file_read` - Agent read a file
- `action_file_write_sensitive_file` - Agent wrote to a sensitive file
- `action_cmd_risky` - Agent executed a risky command
- `obs_cmd_error` - Command execution failed
- `state_high_risk` - Current action has high security risk

## LTL Specifications

### Example Specifications

1. **No write without read first**:
   ```
   G(action_file_write -> F_past(action_file_read))
   ```
   "Globally, if writing to a file, must have read a file in the past"

2. **Never access sensitive files**:
   ```
   G(!action_file_read_sensitive_file)
   ```
   "Globally, never read sensitive files"

3. **Require confirmation for risky commands**:
   ```
   G(action_cmd_risky -> confirmation_required)
   ```
   "Globally, risky commands require confirmation"

### Built-in Specifications

The analyzer comes with default specifications for:
- File access patterns
- Command execution safety
- Browsing restrictions  
- Error handling
- Package installation controls

## Usage

### Basic Setup

```python
from openhands.security.ltl_analyzer import LTLSecurityAnalyzer
from openhands.security.ltl_specs import create_default_ltl_specifications

# Create analyzer with default specs
analyzer = LTLSecurityAnalyzer(
    event_stream=event_stream,
    ltl_specs=create_default_ltl_specifications()
)
```

### Custom Specifications

```python
from openhands.security.ltl_specs import LTLSpecification

# Define custom specification
custom_spec = LTLSpecification(
    name="no_external_browsing",
    description="Never browse external URLs",
    formula="G(!action_browse_external_url)",
    severity="HIGH"
)

analyzer.add_ltl_specification(custom_spec)
```

### Monitoring Violations

```python
# Get current violations
violations = analyzer.get_violations()

# Get predicate history
history = analyzer.get_predicate_history()
```

## Implementation Status

### ✅ Completed
- Basic analyzer framework and architecture
- Predicate extraction for major event types (files, commands, browsing, etc.)
- LTL specification data structures and format
- Simple LTL checker for basic patterns:
  - Global implication: `G(p -> q)`
  - Global negation: `G(!p)` (with regex bugs)
  - Eventually: `F(p)` (basic implementation)
- Default security specifications
- Comprehensive unit test suite (72 tests covering core functionality)
- Event history tracking and violation recording

### ⚠️ Current Limitations
- **LTL checker is limited**: Only handles 3 basic patterns, has regex bugs
- **No real model checking**: Uses simple pattern matching, not formal LTL semantics
- **Predicate extraction is basic**: Limited context awareness, no structured relationships
- **Event processing is naive**: Raw event stream, no proper trace abstraction
- **Specification checking is inefficient**: Full history scan for each check

### 🚧 Next Development Session Priorities

1. **Structured Predicates**
   - Define predicate schemas with types and parameters
   - Add file identity tracking (same file across operations)
   - Command context preservation (command + arguments + environment)
   - State predicates with temporal context

2. **Predicate Extraction Refactor** 
   - More sophisticated event analysis
   - Context-aware predicate generation
   - Relationship tracking between events
   - Parameterized predicates (e.g., `file_read(path, time)`)

3. **Event Stream → Trace Abstraction**
   - Convert raw event stream to structured execution traces
   - Abstract away implementation details
   - Focus on security-relevant behavioral patterns
   - Enable more complex temporal relationships

4. **Specifications → State Machine (using ltlsynt)**
   - Replace regex-based pattern matching with proper LTL tools
   - Generate automata from LTL specifications
   - Use tools like `ltlsynt` or `spot` for formal verification
   - Enable complex temporal operators (Until, Release, past operators)

5. **State Machine-Based Checking**
   - Implement proper LTL model checking
   - Incremental checking for performance
   - Support for full LTL syntax and semantics
   - Violation trace generation and debugging

### 🔄 Refactoring Needed
- Current implementation is proof-of-concept quality
- Predicate system needs redesign for expressiveness
- LTL checker needs complete rewrite with proper tools
- Event processing pipeline needs abstraction layers

## Development Roadmap

### Phase 1: Foundation (Current State)
- ✅ Basic framework and architecture
- ✅ Simple predicate extraction
- ✅ Minimal LTL pattern matching
- ✅ Test infrastructure

### Phase 2: Structured Predicates (Next Session)
- 🎯 Define predicate schemas and types
- 🎯 Implement parameterized predicates
- 🎯 Add context tracking (file identity, command context)
- 🎯 Refactor extraction for relationships

### Phase 3: Proper LTL Implementation
- 🎯 Integrate formal LTL tools (`ltlsynt`, `spot`)
- 🎯 State machine generation from specifications
- 🎯 Full LTL operator support
- 🎯 Incremental model checking

### Phase 4: Production Features
- 🎯 Performance optimization
- 🎯 Configuration management
- 🎯 Real-time monitoring
- 🎯 Integration testing

## Integration Points

### With Existing Security
- Extends the base `SecurityAnalyzer` class
- Uses the same event stream subscription mechanism
- Returns `ActionSecurityRisk` levels for compatibility

### With Event System
- Subscribes to all events via `EventStreamSubscriber.SECURITY_ANALYZER`
- Processes both Actions and Observations
- Maintains temporal ordering through event history

## Current Implementation Notes

This is a **proof-of-concept/skeleton implementation** with a solid foundation but significant limitations:

### What Actually Works
- ✅ Event subscription and processing pipeline
- ✅ Basic predicate extraction (file patterns, command patterns, URL analysis)
- ✅ Simple LTL pattern matching for `G(p -> q)` implications
- ✅ Violation recording and history tracking
- ✅ Integration with existing security infrastructure
- ✅ Comprehensive test coverage of implemented features

### What's Stubbed/Incomplete
- ❌ **LTL checker has major gaps**: Global negation regex is broken, Eventually pattern is basic
- ❌ **No real model checking**: Uses regex matching instead of formal LTL semantics
- ❌ **Predicates are flat strings**: No structure, parameters, or relationships
- ❌ **No temporal context**: Cannot track "same file" or command sequences
- ❌ **Performance issues**: Scans full history for each specification check
- ❌ **Limited LTL operators**: No Until, Release, or past-time operators

### Test Coverage Reality
- 72 tests pass, but many use mocking or test the implemented subset
- Tests validate framework structure rather than complex LTL functionality
- Unsupported patterns return `None` (no violation), which tests accept
- Real LTL violations may not be detected due to implementation gaps

## Future Enhancements

### Advanced Features
- **Stateful predicates**: Track file identities, command contexts, etc.
- **Complex temporal relationships**: Full LTL with past operators
- **Machine learning integration**: Learn normal patterns, detect anomalies
- **Policy synthesis**: Auto-generate specifications from examples

### Production Features  
- **Configuration management**: Load/save specifications
- **Performance optimization**: Sliding windows, incremental checking
- **Monitoring dashboard**: Real-time violation visualization
- **Integration testing**: Comprehensive test suite for specifications

## Example Use Cases

1. **Prevent data exfiltration**: Never read sensitive files then browse external URLs
2. **Enforce development practices**: Always run tests after code changes
3. **Detect reconnaissance**: Flag repeated failed commands or file access attempts
4. **Ensure cleanup**: Temporary files must be deleted after use
5. **Command validation**: Certain commands require specific preconditions

This LTL analyzer provides a foundation for sophisticated temporal security analysis that can catch complex behavioral patterns that simple rule-based systems might miss.