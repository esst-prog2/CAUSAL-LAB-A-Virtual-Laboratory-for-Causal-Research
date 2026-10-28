## ADDED Requirements

### Requirement: One verified bibliography
The system SHALL keep every work its methods, checks and models rest on in one bibliography, in APA 7 style. Every journal article SHALL have a DOI or a stable URL. The BibTeX file in docs/ SHALL be generated from that bibliography.

#### Scenario: A cited key
- **WHEN** a method, check or model cites a work
- **THEN** the work is an entry of the bibliography, and the generated BibTeX file contains it

### Requirement: Sources are shown where methods are used
The system SHALL show, in the interface language, the in-text citations of the works each estimator, check and solver rests on, next to its results.

#### Scenario: Running RDD
- **WHEN** the researcher selects regression discontinuity on the Causal Methods page
- **THEN** the page shows "References: Hahn et al. (2001); Imbens & Kalyanaraman (2012); Calonico et al. (2014)"

### Requirement: The report is citable and reproducible
The exported report SHALL cite, under each method it ran, the works that method rests on. It SHALL end with the versions of Python and of the computing packages, a statement that every random draw is seeded, the citation of Causal Lab, and the full list of the works it cited.

#### Scenario: Report on Card & Krueger
- **WHEN** the researcher exports the report of the Card & Krueger data in French
- **THEN** the data section cites Card & Krueger (1994), and the "Références" section gives its full entry
