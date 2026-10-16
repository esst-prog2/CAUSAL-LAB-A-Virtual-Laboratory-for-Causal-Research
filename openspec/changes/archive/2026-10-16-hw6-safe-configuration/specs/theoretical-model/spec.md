## ADDED Requirements

### Requirement: Bounded constants in the free editor
The system SHALL bound the size of every constant sub-expression of an editor expression before evaluating it. A constant that would have more than 1000 decimal digits SHALL be rejected with an error, without being computed.

#### Scenario: Power tower
- **WHEN** an expression contains `9**9**9` (or the same constant inside an exponent or a function)
- **THEN** it is rejected within milliseconds with an error stating the 1000-digit limit, and the server is not blocked

#### Scenario: Ordinary constants
- **WHEN** an expression contains constants such as `10**3`, `2^3` or `10**999`
- **THEN** it is accepted and evaluated as before
