#### L'idée

Le double machine learning garde l'hypothèse de sélection sur observables de l'appariement, mais laisse des modèles d'apprentissage automatique flexibles absorber l'effet des covariables sur le traitement et sur le résultat. Il estime ensuite l'effet à partir de ce que ces modèles n'expliquent pas. L'ajustement croisé (cross-fitting), où chaque prédiction vient d'un modèle entraîné sur d'autres données, empêche le surapprentissage de biaiser l'estimation (Chernozhukov et al., 2018).

#### Ce qu'elle estime

Causal Lab utilise le **modèle partiellement linéaire**

$$Y = \theta D + g(X) + \varepsilon, \qquad D = m(X) + v.$$

$\theta$ est l'effet s'il est le même pour tous. Quand l'effet varie avec $X$, $\theta$ est une **moyenne pondérée par la variance** des effets conditionnels, chaque $X$ pesant $\mathrm{Var}(D \mid X)$. Ce n'est alors **pas l'ATE** ; le modèle interactif vise l'ATE.

#### Sur quoi elle repose

- **Sélection sur observables,** comme pour l'appariement : pas de facteur de confusion non mesuré.
- **Recouvrement.** Le traitement varie à chaque valeur de $X$. Si $m(X)$ prédit $D$ presque parfaitement, il ne reste rien à apprendre.
- **Des fonctions de nuisance assez bien apprises.** Le produit des erreurs de prédiction de $Y$ et de $D$ doit décroître assez vite, en gros plus vite que $n^{-1/2}$.

#### Ce que fait Causal Lab

- **Estimateur.** Ajustement croisé à 5 plis. Dans chaque pli, des forêts aléatoires (200 arbres, au moins 5 observations par feuille) entraînées sur les autres plis prédisent $\ell(X)=E[Y \mid X]$ et $m(X)=E[D \mid X]$. $\theta$ est la pente des résidus du résultat sur les résidus du traitement (Robinson, 1988).
- **Inférence.** Une erreur-type tirée de la fonction d'influence $\psi = (u - \theta v)\,v$, et un intervalle normal à 95 %.
- **Diagnostics.**
  - Le $R^2$ en ajustement croisé des deux modèles.
  - Un avertissement quand le $R^2$ du traitement dépasse 0,95, signe d'un mauvais recouvrement.
  - Le coefficient des MCO avec contrôles linéaires, pour comparaison.

#### Quand elle échoue

- **Un facteur de confusion non mesuré.** L'apprentissage automatique ne le supprime pas.
- **Un traitement presque déterministe** (mauvais recouvrement).
- **Lire $\theta$ comme l'ATE** quand les effets sont hétérogènes.
- **Un seul découpage aléatoire.** Les résultats peuvent bouger avec l'affectation des plis. Répéter l'ajustement croisé et prendre la médiane est le remède habituel ; Causal Lab utilise une seule graine fixe.
