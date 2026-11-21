#### L'idée

Une étude d'événement est une différence de différences avec **un coefficient par période relative au traitement**. Elle montre comment l'effet se construit après le traitement. Les coefficients d'avant traitement montrent si traités et témoins s'écartaient déjà.

#### Ce qu'elle estime

Un profil d'effets dynamiques $\beta_k$, pour les périodes $k$ avant ($k<0$) et après ($k \ge 0$) le traitement, par rapport à une période de référence, en général $k=-1$ :

$$Y_{it} = \alpha_i + \gamma_t + \sum_{k \ne -1} \beta_k \, \mathbf{1}[t - T_{0i} = k] + \varepsilon_{it}.$$

Sous tendances parallèles et sans anticipation, $\beta_k$ pour $k \ge 0$ est l'ATT $k$ périodes après l'adoption, et $\beta_k = 0$ pour $k < -1$.

#### Sur quoi elle repose

- **Des tendances parallèles à chaque période**, pas seulement en moyenne.
- **Pas d'anticipation.**
- **Avec une adoption échelonnée,** un estimateur qui ne compare pas les cohortes traitées à des cohortes déjà traitées. Sinon chaque $\beta_k$ peut mêler des effets d'autres périodes (Sun et Abraham, 2021).

#### Ce que fait Causal Lab

- **Estimateur.** Avances et retards avec effets fixes d'unité et de période, période de référence $k=-1$, périodes relatives regroupées à $\pm 6$. Les unités jamais traitées partagent la catégorie de référence.
- **Inférence.** Erreurs-types clusterisées par unité, avec la même convention de petit échantillon que la DiD et une loi de Student à $G-1$ degrés de liberté.
- **Adoption échelonnée.** L'agrégation en étude d'événement de Callaway et Sant'Anna (2021) est disponible : chaque $ATT(e)$ est une moyenne des effets groupe–période pondérée par la taille des cohortes, avec un intervalle analytique.
- **Diagnostics.** Les avances sont tracées avec leurs intervalles. Leur test joint, avec une $p$-valeur par wild cluster bootstrap, tourne sur la page Fragiliser mon design. Causal Lab dit clairement qu'un pré-test silencieux n'établit pas les tendances parallèles.

#### Quand elle échoue

- **Des pré-tendances trop faibles pour que les avances les détectent.** Les avances paraissent plates alors que le biais est grand. C'est le résultat principal de la Démo guidée.
- **Les doubles effets fixes sous calendrier échelonné et effets hétérogènes.** Les coefficients peuvent mêler des effets d'autres périodes, et ceux d'avant traitement peuvent montrer de fausses « pré-tendances ».
- **Les extrémités regroupées,** qui absorbent toutes les périodes hors de la fenêtre dans un seul coefficient.
