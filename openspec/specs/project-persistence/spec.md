# project-persistence Specification

## Purpose
TBD - created by archiving change project-save-and-open. Update Purpose after archive.

## Requirements

### Requirement: Saving a project
The system SHALL let the researcher save the current project from the Settings page as a `.causallab` file, which the browser downloads to the researcher's computer. The file SHALL be a zip archive that holds a `manifest.json` and one Parquet file per dataset. It SHALL contain:
- the research design and whether it was diagnosed;
- the language and the current page;
- the Virtual Lab settings, and the configuration and ground truth of the generated Virtual World;
- the uploaded or bundled real data;
- the data, column mapping and options of every Causal Methods page that has data.

It SHALL NOT contain pickled objects, and it SHALL NOT contain estimation results.

#### Scenario: Saving after generating a Virtual World
- **WHEN** the researcher generates a Virtual World and clicks "Save project"
- **THEN** a `.causallab` file named after the research question is downloaded, and its archive holds only `manifest.json` and `data/*.parquet` members

### Requirement: Opening a project
The system SHALL let the researcher open a `.causallab` file from the Settings page. The opened project SHALL replace the current one, with every dataset identical in values and dtypes. The diagnosis and recommendations SHALL be recomputed when the saved project had them, and the saved language SHALL be restored. A setting missing from the file SHALL take its default value, and a setting this version does not know SHALL be ignored.

#### Scenario: Round trip
- **WHEN** a project with a Virtual World, real data or Causal Methods data is saved and opened again
- **THEN** its datasets, ground truth (unit-keyed entries included), settings and mappings are equal to the saved ones, and every page renders without error

#### Scenario: A file that is not a valid project
- **WHEN** the opened file is not a zip archive, has no `manifest.json` or another format, has a damaged manifest or dataset, lacks a dataset the manifest names, comes from a newer format version, or unpacks to more than 1 GB
- **THEN** the system leaves the current project unchanged and shows an error that names the reason

### Requirement: Opened panels are checked like uploads
The system SHALL check the panel datasets of an opened project file as it checks an uploaded CSV. A panel that lacks a required column, or whose indicators are not 0/1, SHALL make the file be refused with the reason. Rows with a missing unit, period or outcome SHALL be left out.

#### Scenario: A hand-edited project without treated_unit
- **WHEN** the researcher opens a project file whose uploaded panel has no treated_unit column
- **THEN** the file is refused, the message names the column, and the current project is kept
