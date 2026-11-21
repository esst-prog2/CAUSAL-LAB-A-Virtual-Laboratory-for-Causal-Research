#### L'idée

Si toutes les variables qui influencent à la fois le traitement et le résultat sont mesurées, on compare chaque unité traitée à des unités non traitées qui lui ressemblent sur ces variables. Au sein de ces comparaisons appariées, le traitement est quasi aléatoire.

#### Ce qu'elle estime

Ici, l'**effet moyen du traitement sur les traités** (ATT) :

$$\tau_{ATT} = E[Y(1) - Y(0) \mid D = 1].$$

#### Sur quoi elle repose

- **Sélection sur observables (non-confusion).** $\{Y(0), Y(1)\} \perp D \mid X$. Le traitement est indépendant des résultats potentiels une fois les covariables $X$ fixées. Cela ne se vérifie pas.
- **Recouvrement (support commun).** Pour l'ATT, chaque unité traitée a des témoins comparables : $P(D=1 \mid X) < 1$.
- **Des covariables mesurées avant le traitement.** Apparier sur une variable que le traitement modifie biaise l'estimation.

#### Ce que fait Causal Lab

- **Estimateur.** Appariement au plus proche voisin sur les covariables, avec remise, en distance de Mahalanobis, avec la correction de biais d'Abadie et Imbens (2011). Le résultat du témoin apparié est ajusté par une régression sur $X$ parmi les témoins utilisés.
- **Inférence.** La variance d'Abadie–Imbens (2006) pour l'ATT. Le bootstrap n'est pas utilisé, car il n'est pas valide pour l'appariement au plus proche voisin.
- **Score de propension.** Un score de propension logit, pour le diagnostic de recouvrement et pour une estimation par pondération inverse, donnée à côté avec une erreur-type bootstrap.
- **Diagnostics.**
  - Les différences moyennes standardisées avant et après appariement, avec un avertissement au-dessus de 0,1.
  - Le nombre d'unités traitées hors de l'étendue des scores des témoins.
  - Le nombre de témoins distincts utilisés.

#### Quand elle échoue

- **Un facteur de confusion non mesuré.** Aucune table d'équilibre ne peut le révéler. Une analyse de sensibilité, comme les bornes de Rosenbaum ou les E-values, demande quelle force il devrait avoir.
- **Un mauvais recouvrement.** Des traités sans témoin comparable forcent l'extrapolation.
- **Des covariables post-traitement,** les « mauvais contrôles ».
- **Beaucoup de covariables pour peu de témoins.** Les appariements deviennent inexacts, et la correction de biais pèse plus.
