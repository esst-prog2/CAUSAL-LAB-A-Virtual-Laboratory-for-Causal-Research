## ADDED Requirements

### Requirement: Configuration is validated before generation
The generator SHALL refuse, with an error naming the setting, a configuration it cannot honour: fewer than 2 units, a share of treated units outside the open interval (0, 1), a noise standard deviation that is not positive, or a threat level other than none, low, medium, high or severe. It SHALL NOT clip such values silently.

#### Scenario: Share of treated units above 1
- **WHEN** `generate` is called with `share_treated = 1.5`
- **THEN** it raises an error naming `share_treated`, and no data are generated

#### Scenario: Misspelt threat level
- **WHEN** `generate` is called with `spillovers = "huge"`
- **THEN** it raises an error naming the setting, the value and the allowed levels

#### Scenario: Smallest valid world
- **WHEN** `generate` is called with 2 units and `share_treated = 0.5`
- **THEN** it generates a panel with one treated and one control unit
