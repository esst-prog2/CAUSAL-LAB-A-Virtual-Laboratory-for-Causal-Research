#### L'idée

Une seule série, comme des hospitalisations mensuelles ou des accidents annuels, est observée longtemps avant et après une intervention à une date connue. La tendance d'avant l'intervention est prolongée comme contrefactuel. Un changement de **niveau** ou de **pente** à la date de l'intervention est lu comme son effet.

#### Ce qu'elle estime

Le changement de niveau et de tendance à la date de l'intervention, en général par une régression segmentée :

$$Y_t = \beta_0 + \beta_1 t + \beta_2 \mathbf{1}[t \ge T_0] + \beta_3 (t - T_0)\,\mathbf{1}[t \ge T_0] + \varepsilon_t,$$

où $\beta_2$ est le changement immédiat de niveau et $\beta_3$ le changement de pente.

#### Sur quoi elle repose

- **La tendance d'avant l'intervention aurait continué,** saisonnalité comprise.
- **Rien d'autre n'a changé à la même date,** ni une autre politique, ni la façon de mesurer le résultat.
- **Assez de points avant et après,** et une modélisation de l'autocorrélation et de la saisonnalité.

#### Ce que fait Causal Lab

**Conseil seulement : Causal Lab n'a pas d'estimateur de série temporelle interrompue.** Il envisage ce design quand la question et les données s'y prêtent : une seule série, une date d'intervention connue et aucun groupe de comparaison. Il énonce alors les hypothèses ci-dessus. Pour estimer, utilisez une régression segmentée avec des erreurs-types robustes à l'autocorrélation (Newey–West), ou un modèle ARIMA avec un terme d'intervention. S'il existe une série comparable non touchée, une différence de différences ou un contrôle synthétique est en général plus crédible.

#### Quand elle échoue

- **Un autre événement à la date de l'intervention.** Sans groupe de comparaison, rien ne sépare son effet de celui de l'intervention.
- **Des tendances non linéaires, une saisonnalité ou une régression vers la moyenne,** par exemple une intervention lancée parce que le résultat venait d'atteindre un pic.
- **Trop peu d'observations** pour estimer la tendance d'avant l'intervention.
