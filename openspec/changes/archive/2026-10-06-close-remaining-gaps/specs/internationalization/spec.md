## MODIFIED Requirements

### Requirement: Deliberate English exceptions
The system SHALL leave untranslated only text that is not interface text:
- bibliographic references (author names, years);
- the names of columns, units and values from the researcher's own data;
- programming-language keywords and function names in generated scripts.

Everything else SHALL follow the interface language, including the comments and printed labels of generated scripts and the per-method technical summary.

#### Scenario: Technical summary
- **WHEN** a Causal Methods result is shown in French
- **THEN** the technical summary is inside an expander titled "Résumé technique", and its lines (headline, inference, method-specific details) are in French

#### Scenario: French audit including code blocks
- **WHEN** the French render audit also inspects code blocks (generated scripts and technical summaries)
- **THEN** it finds no English interface sentence
