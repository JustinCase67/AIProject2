import numpy as np
import random

from gacvm import MutationStrategy, Domains


class MultiMutationStrategy(MutationStrategy):
    """Stratégie de mutation qui mute 1 à tous les gènes d'un individu à la fois.
    La mutation est effectuée sur 1 à tous gènes d'un individu avec la probabilité donnée.

    L'objectif de cette stratégie de mutation est d'introduire une diversité génétique au sein de la population
    d'un algorithme génétique en mutant une fraction variable des gènes d'un individu à chaque génération.
    Contrairement aux stratégies existantes qui mutent un seul gène ou tous les gènes simultanément,
    cette approche intermédiaire permet de muter de 1 à n gènes, où n est le nombre total de gènes de l'individu, selon une probabilité définie.
    La capacité de muter une plage variable de gènes offre une flexibilité accrue par rapport aux stratégies
    qui mutent systématiquement un seul gène ou tous les gènes.

    Cette approche permet de s'adapter dynamiquement
    aux besoins spécifiques de l'algorithme. En effet, en mutant un nombre
    aléatoire de gènes, cette stratégie peut générer des solutions nécessitant des mutations à des gènes spécifiques tout en
    gardant une grande couverture des solutions possibles à travers les domaines.
    Comme ses prédécésseurs, cette stratégie demeure générique et peut être appliquée à des problèmes
    de toute dimensionnalité. En étant capable de muter une fraction variable de gènes, l'algorithme peut s'adapter à la complexité
    et à la structure des problèmes à n dimensions, même lorsque ces structures ne sont pas encore connues.

    En l'appliquant sur le "shape optimizer", elle permet de trouver plus rapidement les solutions qui sont
    proche de la solution actuelle mais requièrent la mutation de plus d'un paramètre, tout en gardant une couverture
    de même envergure que la stratégie de mutation de tous les gènes. Donc, si une meilleure solution est possible
    mais requiert une rotation et une translation, elle serait presque impossible à trouver avec les deux premières stratégies.
    En permettant la mutation de 1 à n gènes, cette stratégie offre un bon équilibre entre
    l'exploration de nouvelles solutions et l'exploitation des solutions existantes.

    En ce qui concerne notre problème de balistique, la stratégie de mutation qui permet de muter de 1 à n gènes à la fois
    est particulièrement pertinente ici car elle peut introduire des variations significatives dans les paramètres clés
    (comme la vitesse initiale, l'angle de propulsion et la force d'explosion). De plus, certains paramètres tels que le pourcentage de trajectoire avant détonation
    et le pourcentage de force d'explosion sont particulièrement sensibles et peuvent nécessiter des ajustements précis pour améliorer la trajectoire
    et l'impact des projectiles. La stratégie de mutation permet de cibler ces gènes spécifiques pour des ajustements fins,
    ce qui peut être crucial pour éviter les zones protégées et maximiser le nombre de cibles atteintes."""

    def __init__(self) -> None:
        super().__init__('Mutate Single to All Genes')

    def mutate(self, offsprings: np.ndarray, mutation_rate: float,
               domains: Domains) -> None:
        def do_mutation(offspring, mutation_rate, domains):
            if self._rng.random() <= mutation_rate:
                nb_index = random.randint(1, domains.dimension)
                mutation_mask = np.zeros(domains.dimension, dtype=bool)
                mutation_indices = self._rng.choice(domains.dimension,
                                                    nb_index, replace=False)
                mutation_mask[mutation_indices] = True
                new_values = domains.random_values()
                offspring[mutation_mask] = new_values[mutation_mask]

        np.apply_along_axis(do_mutation, 1, offsprings, mutation_rate, domains)
