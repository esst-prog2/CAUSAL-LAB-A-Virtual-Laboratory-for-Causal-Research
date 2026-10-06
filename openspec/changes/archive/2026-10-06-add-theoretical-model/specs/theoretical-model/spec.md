## Purpose

Lets the researcher describe a strategic interaction as a set of agents: each agent has a strategy variable, a bounded strategy space and a utility function. The researcher picks a ready-made model or writes one, and sees the equations that govern each agent's choice.

## ADDED Requirements

### Requirement: Model structure
A model SHALL consist of named parameters with default values and descriptions, plus one or more agents. Each agent SHALL have a name, a strategy variable, lower and upper strategy bounds (numbers or expressions in the parameters), and a utility expression in the strategies and parameters. A model MAY also declare named outcome expressions, such as total effort or market price, to be reported at equilibrium.

#### Scenario: Inspecting a model
- **WHEN** a model is loaded
- **THEN** its agents, strategy variables, bounds, utilities, parameters (with defaults) and outcomes are all available for display

### Requirement: Model catalogue
The system SHALL provide these ready-made models:
- Downsian median voter
- Probabilistic voting (three voter groups)
- Tullock rent-seeking contest with N contestants
- Niskanen budget-maximizing bureaucracy
- Voluntary public-good provision with N contributors
- Cournot oligopoly with N firms
- Differentiated-products Bertrand duopoly

Each SHALL come with a description, its references, its outcome expressions, and, where one exists, the closed-form equilibrium.

#### Scenario: Choosing a catalogue model with N agents
- **WHEN** the researcher selects the Tullock contest, public-good or Cournot model and chooses N between 2 and 6
- **THEN** a model with exactly N agents is built, with one prize, endowment or cost parameter per agent

### Requirement: First-order conditions and best responses
The system SHALL derive, for each agent, the first-order condition (the derivative of its utility with respect to its own strategy, set to zero). Where the condition can be solved symbolically for the agent's own strategy, the system SHALL also derive the best-response function. Both SHALL be displayed as equations.

#### Scenario: Cournot best response
- **WHEN** the 2-firm Cournot model is loaded
- **THEN** firm 1's best response is shown as q1 = (a - c1 - b*q2) / (2*b), or an algebraically equivalent expression

#### Scenario: No closed-form best response
- **WHEN** an agent's first-order condition cannot be solved symbolically within the solver's limits
- **THEN** the first-order condition is still shown, together with a note that the best response is computed numerically

### Requirement: Free model editor with safe parsing
The system SHALL let the researcher declare parameters (name and default value) and N agents (name, strategy variable, bounds, utility expression). Expressions SHALL be written in ordinary mathematical notation (`+ - * / ^`, parentheses, numbers, declared names, and the functions `log`, `exp`, `sqrt`, `Abs`, `Min`, `Max`). Any other identifier, attribute access, indexing, string or underscore-prefixed name SHALL be rejected before evaluation, with an error naming the offending token.

#### Scenario: Valid custom model
- **WHEN** the researcher declares parameters `V, r`, agents with strategies `x1, x2` and utilities `V*x1/(x1+x2) - x1` and `V*x2/(x1+x2) - x2`
- **THEN** the model is built and can be solved like a catalogue model

#### Scenario: Undeclared name
- **WHEN** a utility expression uses a name that is neither a declared parameter, a strategy, nor an allowed function
- **THEN** the editor shows an error naming that identifier and no model is built

#### Scenario: Code injection attempt
- **WHEN** an expression contains `__`, `.` outside a number, `[`, a quote, or `lambda`
- **THEN** it is rejected before any evaluation
