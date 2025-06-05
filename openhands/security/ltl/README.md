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
- Basic analyzer framework
- Predicate extraction for major event types
- LTL specification format
- Simple LTL checker for common patterns
- Default security specifications

### 🚧 TODO (Future Development)
- Full LTL parser and model checker
- Advanced temporal patterns (past operators, complex nesting)
- Configuration file loading
- Integration with existing security infrastructure
- Performance optimization for large event histories
- Real-time violation alerts and responses
- Custom predicate definitions
- Specification validation and testing

## Integration Points

### With Existing Security
- Extends the base `SecurityAnalyzer` class
- Uses the same event stream subscription mechanism
- Returns `ActionSecurityRisk` levels for compatibility

### With Event System
- Subscribes to all events via `EventStreamSubscriber.SECURITY_ANALYZER`
- Processes both Actions and Observations
- Maintains temporal ordering through event history

## Limitations

This is a proof-of-concept implementation with several limitations:

1. **Simplified LTL checker** - Only handles basic patterns, not full LTL
2. **No past operators** - Cannot easily express "something happened before"
3. **Limited predicate relationships** - No file identity tracking across events
4. **Memory usage** - Stores full event and predicate history
5. **Performance** - Not optimized for large numbers of events or specifications

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