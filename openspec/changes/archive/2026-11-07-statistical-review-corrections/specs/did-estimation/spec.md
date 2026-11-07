## ADDED Requirements

### Requirement: Interval and warnings of the DiD
The DiD SHALL use complete rows only, and a Student t interval with G - 1 degrees of freedom, G being the number of clusters. It SHALL warn when there are fewer than 30 clusters or fewer than 10 treated or untreated clusters, when the treatment is not coded 0/1, and when treatment switches off. The event study SHALL use the same standard errors and interval, so that with two periods its coefficient equals the DiD with the same SE.

#### Scenario: Two periods
- **WHEN** the DiD and the event study run on a two-period panel
- **THEN** their estimate, standard error and interval are equal

#### Scenario: Few treated clusters
- **WHEN** 4 of 40 units are treated
- **THEN** the result warns that clustered inference is unreliable
