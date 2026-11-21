#### L'idée

Le chercheur attribue le traitement par un mécanisme de hasard : pile ou face, loterie, tirage informatique. L'attribution est alors indépendante de tout ce qui pourrait influencer le résultat, observé ou non. Les groupes traité et témoin ne diffèrent que par le hasard et par le traitement, si bien que l'écart entre leurs moyennes estime l'effet du traitement.

#### Ce qu'elle estime

L'**effet moyen du traitement** (ATE) dans l'échantillon étudié :

$$\tau = E[Y_i(1) - Y_i(0)],$$

où $Y_i(1)$ et $Y_i(0)$ sont les résultats que l'unité $i$ aurait avec et sans traitement. On n'en observe jamais qu'un seul ; la randomisation rend les groupes échangeables, donc $E[Y \mid D=1] - E[Y \mid D=0] = \tau$.

#### Sur quoi elle repose

- **Une randomisation menée comme décrit.** Personne n'a choisi ni pu prévoir qui serait traité.
- **Pas d'interférence (SUTVA).** Le traitement d'une unité ne modifie pas le résultat d'une autre.
- **Observance et pas d'attrition différentielle.** Les unités reçoivent le traitement attribué, et les résultats ne manquent pas plus souvent dans un groupe que dans l'autre. Sinon, la comparaison des groupes tels qu'attribués estime l'effet de l'intention de traiter, pas l'effet du traitement reçu.

#### Ce que fait Causal Lab

- **Estimateur.** La différence de moyennes, par régression de $Y$ sur $D$. Avec des covariables de base, l'estimateur ajusté de Lin (2013) : covariables centrées et croisées avec $D$. Il garde la même estimande et n'est asymptotiquement jamais moins précis que la différence de moyennes.
- **Inférence.** Erreurs-types robustes à l'hétéroscédasticité HC2 et intervalle normal à 95 %.
- **Diagnostics.** Une table d'équilibre des différences moyennes standardisées. Un avertissement nomme chaque covariable dont l'écart dépasse 0,1. Le test de robustesse de la page Méthodes causales fait un test de Wald joint : les covariables prédisent-elles l'attribution ?

#### Quand elle échoue

- Une attribution qui n'était pas aléatoire en pratique, par exemple une liste manipulée ou un déploiement partiel.
- Une attrition différente selon le groupe.
- Des effets de débordement, par exemple des voisins vaccinés qui protègent les non-vaccinés.
- Un échantillon différent de la population visée : l'effet est valide en interne mais peut ne pas se transposer (validité externe).
- Un déséquilibre dû au hasard dans un petit échantillon. L'ajustement sur les covariables aide, mais ne répare pas une randomisation défaillante.
