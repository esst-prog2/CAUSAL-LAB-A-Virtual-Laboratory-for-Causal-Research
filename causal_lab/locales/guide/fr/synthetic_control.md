#### L'idée

Quand **une seule unité** est traitée, un pays, une région ou une ville, on construit son contrefactuel comme une **moyenne pondérée d'unités donneuses non traitées**. Les poids sont choisis pour que l'unité synthétique reproduise la trajectoire de l'unité traitée avant le traitement. Après le traitement, l'écart entre l'unité traitée et son jumeau synthétique estime l'effet.

#### Ce qu'elle estime

L'effet sur l'unité traitée à chaque période après traitement, $\tau_t = Y_{1t} - \sum_j w_j Y_{jt}$, avec $w_j \ge 0$ et $\sum_j w_j = 1$. Le chiffre principal de Causal Lab est l'écart moyen après traitement.

#### Sur quoi elle repose

- **Un bon ajustement avant traitement**, sur une période assez longue. Sans lui, les poids ne reproduisent pas la dynamique de l'unité traitée.
- **L'ajustement se prolonge.** Les mêmes poids auraient suivi l'unité traitée sans traitement. C'est plausible quand le résultat dépend de facteurs communs que les donneurs partagent.
- **Pas de choc à la même date** propre à l'unité traitée, et **pas de débordement sur les donneurs**.
- **Enveloppe convexe.** L'unité traitée n'est pas extrême, si bien qu'une combinaison convexe de donneurs peut la reproduire.

#### Ce que fait Causal Lab

- **Estimateur.** Les poids minimisent la distance avant traitement $\lVert y_{1,pre} - Y_{0,pre} w \rVert^2$ sur le simplexe. Avec des covariables, les poids ajustent plutôt des prédicteurs standardisés, avec une matrice d'importance $V$ choisie pour minimiser l'erreur de prédiction avant traitement (Abadie, Diamond et Hainmueller, 2010).
- **Inférence.** Permutation placebo dans l'espace : chaque donneur est traité à son tour comme s'il était l'unité traitée. La $p$-valeur est le rang du ratio RMSPE après/avant de l'unité traitée. Aucune erreur-type n'est donnée.
- **Diagnostics.**
  - Le RMSPE avant traitement, et un avertissement si l'ajustement est mauvais.
  - Les poids des donneurs et l'équilibre des prédicteurs.
  - Un avertissement sous 19 donneurs. La $p$-valeur ne peut alors pas descendre sous 5 %, quelle que soit la taille de l'effet.

#### Quand elle échoue

- Une période d'avant traitement courte ou mal ajustée.
- Peu de donneurs, ou des donneurs touchés par la politique ou par des débordements.
- Une unité traitée hors de l'étendue des donneurs.
- Lire la $p$-valeur de permutation comme un test d'échantillonnage. C'est un rang parmi les unités observées.
