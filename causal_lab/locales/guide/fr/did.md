#### L'idée

Comparer l'**évolution** du résultat dans le temps entre un groupe qui reçoit le traitement et un groupe qui ne le reçoit pas. L'évolution du groupe témoin tient lieu de ce qui serait arrivé au groupe traité sans traitement. La soustraire retire tout ce qui est fixe au sein des unités et tout ce qui fait bouger les deux groupes de la même façon.

#### Ce qu'elle estime

L'**effet moyen du traitement sur les traités** (ATT) :

$$\tau_{ATT} = E[Y_{post}(1) - Y_{post}(0) \mid D = 1],$$

estimé, dans le cas à deux groupes et deux périodes, par
$(\bar Y^{T}_{post} - \bar Y^{T}_{pre}) - (\bar Y^{C}_{post} - \bar Y^{C}_{pre})$.

#### Sur quoi elle repose

- **Tendances parallèles.** Sans traitement, traités et témoins auraient suivi la même tendance moyenne. L'hypothèse porte sur un contrefactuel non observé et ne se teste pas ; les tendances d'avant traitement la rendent seulement plus ou moins plausible.
- **Pas d'anticipation.** Les résultats ne bougent pas avant le traitement parce que les unités l'attendent.
- **Pas de débordement** sur les témoins, et une **composition stable** des groupes.
- **Avec une adoption échelonnée,** des effets homogènes dans le temps et entre cohortes, ou un estimateur qui n'en a pas besoin.

#### Ce que fait Causal Lab

- **Estimateur.** Doubles effets fixes, $Y_{it} = \alpha_i + \gamma_t + \beta D_{it} + \varepsilon_{it}$.
- **Inférence.** Erreurs-types clusterisées par unité (Bertrand, Duflo et Mullainathan, 2004), avec le facteur de petit échantillon CR1, où les indicatrices d'unité ne sont pas comptées, comme dans `xtreg, fe` de Stata. L'intervalle utilise une loi de Student à $G-1$ degrés de liberté, $G$ étant le nombre de clusters. Le résultat avertit sous 30 clusters ou sous 10 par bras.
- **Adoption échelonnée.** L'estimateur robuste à l'hétérogénéité de Callaway et Sant'Anna (2021) est disponible. Il estime un effet par cohorte d'adoption et par période, face aux unités jamais traitées ou pas encore traitées, les agrège, et utilise une variance analytique avec les degrés de liberté de Welch–Satterthwaite.
- **Diagnostics.**
  - Le test joint des avances (leads) d'avant traitement, avec une $p$-valeur par wild cluster bootstrap.
  - Des avertissements pour un traitement non binaire et pour un traitement qui s'arrête.
  - L'étude de simulation de la Démo guidée : 4 menaces × 5 niveaux × 1 000 mondes, jugés par une règle fixée d'avance, et un supplément où l'effet diffère d'une unité à l'autre.
- **Sensibilité aux violations des tendances parallèles** (page Estimation, onglet étude d'événement). Comme Rambachan et Roth (2023), l'écart de tendance peut se courber d'au plus $M$ par période. Pour chaque $M$, un intervalle de longueur fixe (Armstrong et Kolesár, 2018) couvre l'effet moyen après traitement avec une probabilité d'au moins 95 % sous toute violation de ce type ; $M = 0$ n'autorise que les tendances linéaires vues avant le traitement. Il faut une seule date de traitement et un panel cylindré. Les poids de l'estimateur sont choisis avec une covariance de travail et son erreur-type estimée à partir des unités : avec peu d'unités traitées, le choix du papier sur la covariance estimée couvrait trop peu (88,5 % sur 200 mondes de l'étude).

#### Quand elle échoue

- **Des pré-tendances divergentes.** Dans l'étude stockée, une divergence faible donne un biais de 47 % de l'effet vrai et une couverture de 31,3 %, alors que le test de pré-tendance n'avertit que dans 14,2 % des mondes.
- **Un pré-test réussi est une preuve faible.** Conditionner sur lui peut aggraver le biais (Roth, 2022). Rambachan et Roth (2023) montrent comment présenter des résultats sous des violations bornées ; Causal Lab le fait sur la page Estimation (voir plus haut).
- **Un calendrier échelonné avec des effets qui changent dans le temps.** Les doubles effets fixes comparent alors les adoptants tardifs aux précoces, dont les effets croissent encore (Goodman-Bacon, 2021 ; de Chaisemartin et D'Haultfœuille, 2020).
- **Peu de clusters traités.** L'inférence clusterisée n'est alors pas fiable.
