#### L'idée

Le traitement $D$ est confondu, mais une variable $Z$, l'**instrument**, fait varier $D$ sans autre chemin vers le résultat $Y$. La part de la variation de $D$ qui vient de $Z$ est quasi aléatoire, et elle identifie donc l'effet. Les instruments classiques sont les loteries, la distance à un établissement et les règles qui changent l'éligibilité.

#### Ce qu'elle estime

Avec un instrument et un traitement binaires, sous monotonie, l'**effet moyen local du traitement** (LATE) : l'effet pour les **compliers**, les unités qui prennent le traitement à cause de l'instrument (Imbens et Angrist, 1994) :

$$\tau_{LATE} = \frac{E[Y \mid Z=1] - E[Y \mid Z=0]}{E[D \mid Z=1] - E[D \mid Z=0]}.$$

Avec un effet constant, c'est l'effet de $D$ pour tous.

#### Sur quoi elle repose

- **Pertinence.** $Z$ fait varier $D$. C'est la seule hypothèse testable.
- **Exclusion.** $Z$ n'agit sur $Y$ qu'à travers $D$. Elle ne se teste pas et doit être argumentée.
- **Indépendance.** $Z$ est quasi aléatoirement attribué.
- **Monotonie.** Personne ne prend *moins* le traitement à cause de l'instrument (pas de defiers).

#### Ce que fait Causal Lab

- **Estimateur.** Doubles moindres carrés, avec contrôles éventuels et erreurs-types robustes à l'hétéroscédasticité. Le coefficient des MCO est affiché pour comparaison.
- **Force de l'instrument.** La statistique $F$ de première étape et le $R^2$ partiel. Sous $F = 10$, l'instrument est signalé comme faible. Avec un seul instrument et $10 < F < 104,7$, le résultat indique que le test $t$ habituel à 5 % ne garde pas son niveau (Lee, McCrary, Moreira et Porter, 2022).
- **Inférence robuste aux instruments faibles.** L'ensemble de confiance d'Anderson–Rubin, valide quelle que soit la force de l'instrument. Ce peut être un intervalle, deux demi-droites, ou toute la droite quand l'instrument n'apporte aucune information.
- **Sur-identification.** Avec plusieurs instruments, le test de robustesse de la page Méthodes causales vérifie s'ils concordent. Il ne peut pas montrer que l'exclusion tient.

#### Quand elle échoue

- **Des instruments faibles.** Les doubles moindres carrés sont alors biaisés vers les MCO, et leur intervalle de Wald n'est pas fiable.
- **Une exclusion violée.** Par exemple, la distance à l'université peut aussi agir sur les salaires par le marché du travail local.
- **Des defiers,** qui cassent l'interprétation en LATE.
- **Lire un LATE comme un ATE.** Les compliers peuvent différer de la population.
