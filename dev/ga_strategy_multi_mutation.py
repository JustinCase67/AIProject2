import numpy as np
from numpy.typing import NDArray
import random

from gacvm import MutationStrategy, Domains


class GenesMutationStrategy(MutationStrategy):
    """Stratégie de mutation qui mute tous les gènes d'un individu à la fois.

    La mutation est effectuée sur chaque gène d'un individu avec la probabilité donnée.
    """

    def __init__(self) -> None:
        super().__init__('Mutate All Genes')

    def mutate(self, offsprings: NDArray, mutation_rate: float,
               domains: Domains) -> None:
        def do_mutation(offspring, mutation_rate, domains):
            if self._rng.random() <= mutation_rate:
                offspring[:] = domains.random_values()

        np.apply_along_axis(do_mutation, 1, offsprings, mutation_rate, domains)


class MultiMutationStrategy(MutationStrategy):
    """Stratégie de mutation qui mute 1 à tous les gènes d'un individu à la fois.

    La mutation est effectuée sur 1 à tous gènes d'un individu avec la probabilité donnée.
    """

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
