#### L'idée

Le traitement est décidé, ou fortement encouragé, selon qu'une **variable de score** $X$ franchit un **seuil** connu $c$. Par exemple, une note au-dessus de la barre de la bourse, ou un revenu sous un plafond d'éligibilité. Les unités juste en dessous et juste au-dessus du seuil se ressemblent en tout sauf le traitement : le saut du résultat au seuil est l'effet du traitement à cet endroit.

#### Ce qu'elle estime

- **Design net (sharp)**, où tout le monde au-dessus du seuil est traité : l'effet au seuil, $\tau = E[Y(1) - Y(0) \mid X = c]$.
- **Design flou (fuzzy)**, où franchir le seuil ne change que la probabilité d'être traité : le rapport entre le saut du résultat et le saut du traitement. C'est l'effet pour les **compliers** au seuil, les unités dont le seuil change le statut de traitement.

Dans les deux cas l'effet est **local** : il ne dit rien des unités éloignées du seuil.

#### Sur quoi elle repose

- **Continuité.** Sans traitement, le résultat moyen varierait sans saut au passage du seuil.
- **Pas de manipulation précise.** Les unités ne peuvent pas se placer exactement du bon côté du seuil. Si elles le peuvent, celles juste au-dessus diffèrent systématiquement de celles juste en dessous.
- **Un seuil réel et connu**, qui n'est pas partagé par d'autres politiques au même point.
- **Design flou seulement :** monotonie (franchir le seuil ne rend jamais une unité moins susceptible d'être traitée) et exclusion (le seuil n'agit sur le résultat qu'à travers le traitement).

#### Ce que fait Causal Lab

- **Estimateur.** Régression linéaire locale de chaque côté du seuil, avec un noyau triangulaire. La largeur de fenêtre $h$ par défaut est celle d'Imbens et Kalyanaraman, optimale au sens de l'erreur quadratique moyenne. L'estimation floue est le rapport de Wald local.
- **Inférence.** Par défaut, l'intervalle robuste corrigé du biais de Calonico, Cattaneo et Titiunik (2014) : le biais est estimé par une régression quadratique locale, et l'intervalle tient compte de cette estimation. L'intervalle conventionnel est aussi donné. Erreurs-types HC1 de chaque côté ; méthode delta pour la variance floue.
- **Diagnostics.**
  - Les estimations à $h/2$ et $2h$, pour la sensibilité à la fenêtre.
  - Des seuils placebo, dans le test de robustesse de la page Méthodes causales, à la médiane de la variable de score de chaque côté, où il ne devrait y avoir aucun saut.
  - En design flou, le saut de première étape et sa statistique $F$.
  - Un contrôle de manipulation : le test de densité de Cattaneo, Jansson et Ma (2020), avec le paquet `rddensity` de ses auteurs. Dans une simulation de 500 mondes par scénario, il a donné une fausse alerte dans 4,0 % des cas et détecté le tri plus souvent que la simple comparaison d'effectifs qu'il remplace. S'il ne peut pas tourner sur les données, Causal Lab revient à un test binomial des effectifs près du seuil, et le dit.

#### Quand elle échoue

- **Tri au seuil.** Un amas d'observations juste au-dessus de la barre en est le signe classique.
- **Une autre discontinuité au même seuil**, par exemple un second programme qui utilise le même seuil.
- **Trop peu d'observations près du seuil.** L'estimation repose alors sur la forme fonctionnelle, et l'intervalle est large.
- **L'extrapolation.** Un effet local en $c$ lu comme un effet moyen pour tous.
