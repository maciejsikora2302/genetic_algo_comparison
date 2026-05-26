import random
import math
import time
from typing import List, Tuple, Callable, Optional
from .test_case import TestCase

class EPIndividual:
    """
    Represents an individual in the continuous self-adaptive Evolutionary Programming search space.
    Uses the Random Keys paradigm to map real-valued vectors to discrete city permutations.
    """
    def __init__(self, x: List[float], sigma: List[float]):
        self.x = x
        self.sigma = sigma
        self.fitness = 0.0
        self.route: List[int] = []
        self.distance = float('inf')

    def decode(self) -> List[int]:
        """
        Decodes the continuous objective vector x (length d) into a discrete TSP route.
        Using the Random Keys paradigm, city indices 1 ... d+1 are sorted based on 
        the objective values in x, and prefixed with starting city 0.
        """
        n = len(self.x) + 1
        # Sort indices 1 ... n-1 according to corresponding values in self.x
        order = sorted(range(1, n), key=lambda i: self.x[i - 1])
        return [0] + order

    def evaluate(self, test_case: TestCase) -> float:
        """
        Computes and caches the route permutation, total path distance,
        and fitness (the reciprocal of the path distance).
        """
        self.route = self.decode()
        self.distance = test_case.get_route_distance(self.route)
        self.fitness = 1.0 / max(1e-9, self.distance)
        return self.fitness

    def mutate(self, tau: float, tau_prime: float, normal_global: float) -> 'EPIndividual':
        """
        Generates a single offspring using the self-adaptive Gaussian mutation:
        sigma'_j = sigma_j * exp(tau * N(0,1) + tau_prime * N_j(0,1))
        x'_j = x_j + sigma'_j * N_j(0,1)
        """
        d = len(self.x)
        x_c = []
        sigma_c = []
        
        for j in range(d):
            normal_local = random.normalvariate(0.0, 1.0)
            
            # Update strategic step size parameter sigma
            new_sigma = self.sigma[j] * math.exp(tau * normal_global + tau_prime * normal_local)
            # Enforce hard boundary constraints to protect against mathematical underflow/overflow
            new_sigma = max(1e-5, min(new_sigma, 10.0))
            
            # Update objective variable x
            new_x = self.x[j] + new_sigma * normal_local
            
            x_c.append(new_x)
            sigma_c.append(new_sigma)
            
        return EPIndividual(x_c, sigma_c)


class EPPopulation:
    """
    Encapsulates a collection of EPIndividuals and manages population-level operations.
    """
    def __init__(self, individuals: List[EPIndividual] = None):
        self.individuals = individuals if individuals is not None else []

    @classmethod
    def initialize_random(cls, pop_size: int, dimension: int, init_sigma: float) -> 'EPPopulation':
        """
        Factory method to initialize a population with random continuous variables.
        """
        individuals = []
        for _ in range(pop_size):
            x = [random.uniform(-1.0, 1.0) for _ in range(dimension)]
            sigma = [init_sigma for _ in range(dimension)]
            individuals.append(EPIndividual(x, sigma))
        return cls(individuals)

    def evaluate_all(self, test_case: TestCase):
        """
        Evaluates the fitness of all individuals in the population.
        """
        for ind in self.individuals:
            ind.evaluate(test_case)

    def generate_offspring(self, tau: float, tau_prime: float) -> 'EPPopulation':
        """
        Generates exactly 1 mutated offspring per parent individual.
        Uses a single global normal random variable per offspring.
        """
        offspring_list = []
        for parent in self.individuals:
            normal_global = random.normalvariate(0.0, 1.0)
            child = parent.mutate(tau, tau_prime, normal_global)
            offspring_list.append(child)
        return EPPopulation(offspring_list)

    def stochastic_tournament_selection(self, q: int, select_count: int) -> 'EPPopulation':
        """
        Selects individuals using Fogel-style stochastic tournament selection.
        Each individual competes against q randomly selected opponents from the pool,
        accumulating wins when it outperforms or matches the opponent's fitness.
        """
        pool = self.individuals
        pool_size = len(pool)
        wins = [0] * pool_size
        
        # Make sure q is within valid range
        q = max(1, min(q, pool_size - 1))
        
        for i in range(pool_size):
            # Select q distinct opponents uniformly at random from the entire pool
            opponents = random.sample(range(pool_size), q)
            for opp in opponents:
                if pool[i].fitness >= pool[opp].fitness:
                    wins[i] += 1
                    
        # Sort the entire pool by win counts in descending order
        sorted_indices = sorted(range(pool_size), key=lambda idx: wins[idx], reverse=True)
        
        # Select the top select_count individuals to form the next generation
        selected_individuals = [pool[idx] for idx in sorted_indices[:select_count]]
        return EPPopulation(selected_individuals)

    def get_best_individual(self) -> EPIndividual:
        """
        Returns the individual in the population with the highest fitness.
        """
        return max(self.individuals, key=lambda ind: ind.fitness)

    def get_mean_fitness(self) -> float:
        """
        Computes the average fitness value of the population.
        """
        if not self.individuals:
            return 0.0
        return sum(ind.fitness for ind in self.individuals) / len(self.individuals)

    def get_sigma_variance(self) -> float:
        """
        Computes the variance of the strategic step sizes (sigma) across the entire population.
        """
        if not self.individuals:
            return 0.0
        
        all_sigmas = [sig for ind in self.individuals for sig in ind.sigma]
        if not all_sigmas:
            return 0.0
            
        mean_sigma = sum(all_sigmas) / len(all_sigmas)
        variance = sum((s - mean_sigma) ** 2 for s in all_sigmas) / len(all_sigmas)
        return variance

    def __add__(self, other: 'EPPopulation') -> 'EPPopulation':
        """
        Supports combining two populations using the + operator.
        """
        return EPPopulation(self.individuals + other.individuals)


class EvolutionaryEngine:
    """
    The orchestrator running the self-adaptive continuous Evolutionary Programming pipeline.
    Strictly follows the Fogel EP model, excluding crossover operators.
    """
    def __init__(self, population_size: int = 50, tournament_size: int = 10, generations: int = 200, init_sigma: float = 1.0):
        self.pop_size = population_size
        self.q = tournament_size
        self.generations = generations
        self.init_sigma = init_sigma

    def run(self, test_case: TestCase, on_generation_callback: Optional[Callable[[int, float, List[int]], None]] = None, time_limit: float = 3.0) -> EPIndividual:
        """
        Executes the Fogel EP search loop.
        
        Args:
            test_case (TestCase): The TSP case instance to solve.
            on_generation_callback (Callable): Callback signature (generation, best_distance, best_route) to log history.
            time_limit (float): Safety execution guard time limit in seconds.
            
        Returns:
            EPIndividual: The optimized best individual.
        """
        n = len(test_case.cities)
        if n <= 1:
            # Handle trivial corner case
            dummy = EPIndividual([], [])
            dummy.route = list(range(n))
            dummy.distance = 0.0
            dummy.fitness = 1.0
            return dummy

        # Dimension of the continuous objective vector (fixing city 0)
        d = n - 1

        # Calculate self-adaptive scaling coefficients
        tau = 1.0 / math.sqrt(2.0 * d)
        tau_prime = 1.0 / math.sqrt(2.0 * math.sqrt(d))

        # 1. Initialize Population
        population = EPPopulation.initialize_random(
            pop_size=self.pop_size,
            dimension=d,
            init_sigma=self.init_sigma
        )
        population.evaluate_all(test_case)

        # Track the absolute best individual found during search
        current_best = population.get_best_individual()
        best_tour = current_best.route
        best_dist = current_best.distance
        
        if on_generation_callback is not None:
            on_generation_callback(0, best_dist, best_tour)

        start_time = time.perf_counter()

        # 2. Generational Loop
        for gen in range(1, self.generations + 1):
            # Time limit safety guard
            if time.perf_counter() - start_time > time_limit:
                print(f"Evolutionary Programming: Time limit of {time_limit}s exceeded! Terminating search early at generation {gen}.")
                break

            # 3. Mutate: generate 1 offspring per parent
            offspring = population.generate_offspring(tau, tau_prime)
            offspring.evaluate_all(test_case)

            # Combine pool to size 2P
            combined_pool = population + offspring

            # 4. Stochastic Tournament Selection
            population = combined_pool.stochastic_tournament_selection(
                q=self.q,
                select_count=self.pop_size
            )

            # Evaluate statistics
            gen_best = population.get_best_individual()
            mean_fit = population.get_mean_fitness()
            sigma_var = population.get_sigma_variance()

            # Execution logging (matches deliverables)
            log_interval = max(20, self.generations // 10)
            if gen % log_interval == 0 or gen == 1 or gen == self.generations:
                print(f"[EP Gen {gen}] Best Fitness: {gen_best.fitness:.6f} | Mean Fitness: {mean_fit:.6f} | Sigma Variance: {sigma_var:.6f}")

            # Check and record improvement
            if gen_best.distance < best_dist:
                best_dist = gen_best.distance
                best_tour = list(gen_best.route)

            # Log progress periodically
            callback_interval = max(10, self.generations // 20)
            if on_generation_callback is not None and (gen % callback_interval == 0 or gen == self.generations):
                on_generation_callback(gen, best_dist, best_tour)

        # Ensure final state is correctly updated
        final_best = population.get_best_individual()
        if final_best.distance < best_dist:
            best_dist = final_best.distance
            best_tour = list(final_best.route)
            
        if on_generation_callback is not None:
            on_generation_callback(self.generations, best_dist, best_tour)

        # Re-verify and return best
        if final_best.distance == best_dist:
            return final_best
        else:
            # Reconstruct the absolute best found
            best_ind = EPIndividual(current_best.x, current_best.sigma)
            best_ind.route = best_tour
            best_ind.distance = best_dist
            best_ind.fitness = 1.0 / max(1e-9, best_dist)
            return best_ind
