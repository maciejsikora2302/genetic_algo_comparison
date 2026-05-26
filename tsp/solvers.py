import itertools
import math
import random
import time
from typing import List, Tuple
from .algorithm import Algorithm
from .test_case import TestCase
from .evolutionary_programming import EvolutionaryEngine

class BruteForceTSP(Algorithm):
    """
    Solves the TSP using an exact Brute Force search of all permutations.
    Guarantees finding the global optimum, but is O(N!) complexity.
    Now supports running on any scale due to the strict 3.0s execution timeout guard.
    """
    def __init__(self):
        super().__init__("Brute Force")
        self.max_supported_cities = float('inf')

    def run(self, test_case: TestCase, timeout: float = 3.0) -> List[int]:
        # Enforce that Brute Force runs for at most 3.0 seconds
        effective_timeout = min(timeout, 3.0)
        return super().run(test_case, timeout=effective_timeout)

    def _solve(self, test_case: TestCase) -> List[int]:
        n = len(test_case.cities)
        if n == 0:
            return []
        if n == 1:
            return [0]

        best_route = list(range(n))
        best_dist = test_case.get_route_distance(best_route)
        self.record_progress(0, best_dist, best_route)

        # Fix the starting city to index 0 to avoid evaluating redundant circular shifts
        other_cities = list(range(1, n))
        iteration = 0
        
        for perm in itertools.permutations(other_cities):
            iteration += 1
            route = [0] + list(perm)
            dist = test_case.get_route_distance(route)
            
            if dist < best_dist:
                best_dist = dist
                best_route = route
                self.record_progress(iteration, best_dist, best_route)
            elif iteration % 50000 == 0:
                # Log periodically for long searches to avoid completely silent execution
                self.record_progress(iteration, best_dist, best_route)
                
            if iteration % 10000 == 0 and time.perf_counter() - self.start_time > self.timeout:
                print(f"Brute Force: Timeout of {self.timeout}s exceeded! Returning best route found so far.")
                break

        self.record_progress(iteration, best_dist, best_route)
        return best_route


class HeldKarpTSP(Algorithm):
    """
    An exact TSP solver using the Held-Karp Dynamic Programming algorithm.
    Reduces time complexity to O(N^2 * 2^N) using memoization and bitmasks.
    Suitable for medium-sized test cases (N <= 18).
    """
    def __init__(self):
        super().__init__("Held-Karp (DP)")
        self.max_supported_cities = 18

    def _solve(self, test_case: TestCase) -> List[int]:
        n = len(test_case.cities)
        if n == 0:
            return []
        if n == 1:
            return [0]

        dist_matrix = test_case.distance_matrix
        memo = {}
        parent = {}

        # Log an initial state for comparison
        initial_route = list(range(n))
        self.record_progress(0, test_case.get_route_distance(initial_route), initial_route)

        # dp(mask, u) returns the minimum distance to visit all remaining unvisited cities
        # starting from city u, ending back at city 0.
        # mask is a bitmask where the i-th bit is 1 if city i has been visited.
        def dp(mask: int, u: int) -> float:
            if time.perf_counter() - self.start_time > self.timeout:
                return dist_matrix[u][0]

            if mask == (1 << n) - 1:
                return dist_matrix[u][0]

            state = (mask, u)
            if state in memo:
                return memo[state]

            min_dist = float('inf')
            best_next = -1

            for v in range(n):
                # If city v is not visited yet
                if not (mask & (1 << v)):
                    new_dist = dist_matrix[u][v] + dp(mask | (1 << v), v)
                    if new_dist < min_dist:
                        min_dist = new_dist
                        best_next = v

            memo[state] = min_dist
            if best_next != -1:
                parent[state] = best_next
            return min_dist

        # Compute the optimal distance starting from city 0 (mask = 1)
        opt_dist = dp(1, 0)

        # Reconstruct the optimal route path using the parent transition matrix
        route = [0]
        curr_mask = 1
        curr_node = 0
        while len(route) < n:
            next_node = parent.get((curr_mask, curr_node))
            if next_node is None:
                break
            route.append(next_node)
            curr_mask |= (1 << next_node)
            curr_node = next_node

        self.record_progress(1, opt_dist, route)
        return route


class NearestNeighborTSP(Algorithm):
    """
    A constructive greedy heuristic for the TSP.
    Always moves to the closest unvisited city. O(N^2) complexity.
    Very fast, but can produce suboptimal results.
    """
    def __init__(self):
        super().__init__("Nearest Neighbor")

    def _solve(self, test_case: TestCase) -> List[int]:
        n = len(test_case.cities)
        if n == 0:
            return []
        if n == 1:
            return [0]

        dist_matrix = test_case.distance_matrix
        path = [0]
        unvisited = set(range(1, n))
        current_city = 0

        # Log initial sequential route
        initial_route = list(range(n))
        self.record_progress(0, test_case.get_route_distance(initial_route), initial_route)

        step = 1
        while unvisited:
            next_city = min(unvisited, key=lambda city: dist_matrix[current_city][city])
            unvisited.remove(next_city)
            path.append(next_city)
            current_city = next_city

            # Log current partial path (padded with remaining unvisited cities for visualization)
            padded_route = path + list(unvisited)
            current_dist = test_case.get_route_distance(padded_route)
            self.record_progress(step, current_dist, padded_route)
            step += 1

        return path


class TwoOptTSP(Algorithm):
    """
    A local search algorithm that optimizes an existing tour by systematically
    reversing path segments to remove crossing edges (2-opt swaps).
    """
    def __init__(self, init_with_nn: bool = False):
        name = "2-Opt (NN Init)" if init_with_nn else "2-Opt (Random Init)"
        super().__init__(name)
        self.init_with_nn = init_with_nn

    def _get_nearest_neighbor_route(self, test_case: TestCase) -> List[int]:
        n = len(test_case.cities)
        path = [0]
        unvisited = set(range(1, n))
        current_city = 0
        while unvisited:
            next_city = min(unvisited, key=lambda city: test_case.distance_matrix[current_city][city])
            unvisited.remove(next_city)
            path.append(next_city)
            current_city = next_city
        return path

    def _solve(self, test_case: TestCase) -> List[int]:
        n = len(test_case.cities)
        if n <= 3:
            return list(range(n))

        if self.init_with_nn:
            path = self._get_nearest_neighbor_route(test_case)
        else:
            # Start with a truly random initial tour starting at city 0
            path = list(range(n))
            random.shuffle(path)
            idx_zero = path.index(0)
            path = path[idx_zero:] + path[:idx_zero]
        
        dist_matrix = test_case.distance_matrix
        
        current_dist = test_case.get_route_distance(path)
        self.record_progress(0, current_dist, path)

        improved = True
        iteration = 1
        
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    # Check timeout safety
                    if time.perf_counter() - self.start_time > self.timeout:
                        print(f"{self.name}: Timeout of {self.timeout}s exceeded! Returning best route found so far.")
                        improved = False
                        break
                        
                    # Nodes to inspect for the 2-opt swap
                    node_i_minus_1 = path[i - 1]
                    node_i = path[i]
                    node_j = path[j]
                    node_j_plus_1 = path[(j + 1) % n]

                    # Calculate the cost change (delta) using only local edges
                    d_broken = dist_matrix[node_i_minus_1][node_i] + dist_matrix[node_j][node_j_plus_1]
                    d_created = dist_matrix[node_i_minus_1][node_j] + dist_matrix[node_i][node_j_plus_1]
                    delta = d_created - d_broken

                    # If swapping shortens the route, commit and restart search
                    if delta < -1e-9:
                        path[i:j+1] = path[i:j+1][::-1]
                        current_dist += delta
                        self.record_progress(iteration, current_dist, path)
                        iteration += 1
                        improved = True
                        break
                if improved:
                    break

        self.record_progress(iteration, current_dist, path)
        return path


class SimulatedAnnealingTSP(Algorithm):
    """
    A metaheuristic optimization algorithm that explores the search space and
    avoids local minima by accepting worse paths with a probability that decays over time.
    """
    def __init__(self, t_max: float = 100.0, alpha: float = 0.995, t_min: float = 0.001, seed: int = None, init_with_nn: bool = False):
        """
        Args:
            t_max (float): Starting high temperature.
            alpha (float): Cooling rate (multiplicative factor).
            t_min (float): Stopping temperature.
            seed (int, optional): Random seed. Defaults to None.
            init_with_nn (bool): If True, starts search from Nearest Neighbor route. Defaults to False.
        """
        name = "Simulated Annealing (NN Init)" if init_with_nn else "Simulated Annealing (Random Init)"
        super().__init__(name)
        self.t_max = t_max
        self.alpha = alpha
        self.t_min = t_min
        self.seed = seed
        self.init_with_nn = init_with_nn

    def _get_nearest_neighbor_route(self, test_case: TestCase) -> List[int]:
        n = len(test_case.cities)
        path = [0]
        unvisited = set(range(1, n))
        current_city = 0
        while unvisited:
            next_city = min(unvisited, key=lambda city: test_case.distance_matrix[current_city][city])
            unvisited.remove(next_city)
            path.append(next_city)
            current_city = next_city
        return path

    def _solve(self, test_case: TestCase) -> List[int]:
        if self.seed is not None:
            random.seed(self.seed)

        n = len(test_case.cities)
        if n <= 3:
            return list(range(n))

        if self.init_with_nn:
            current_tour = self._get_nearest_neighbor_route(test_case)
        else:
            # Start with a truly random initial tour starting at city 0
            current_tour = list(range(n))
            random.shuffle(current_tour)
            idx_zero = current_tour.index(0)
            current_tour = current_tour[idx_zero:] + current_tour[:idx_zero]
        
        current_dist = test_case.get_route_distance(current_tour)

        best_tour = list(current_tour)
        best_dist = current_dist

        self.record_progress(0, best_dist, best_tour)

        temperature = self.t_max
        iteration = 1

        while temperature > self.t_min:
            # Check timeout safety
            if iteration % 100 == 0 and time.perf_counter() - self.start_time > self.timeout:
                print(f"{self.name}: Timeout of {self.timeout}s exceeded! Returning best route found so far.")
                break

            # Generate a neighboring tour by swapping two random cities
            neighbor = list(current_tour)
            idx1, idx2 = random.sample(range(1, n), 2)
            neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]

            neighbor_dist = test_case.get_route_distance(neighbor)
            delta_e = neighbor_dist - current_dist

            # Accept if better, or with a probability if worse
            if delta_e < 0:
                current_tour = neighbor
                current_dist = neighbor_dist
                if neighbor_dist < best_dist:
                    best_dist = neighbor_dist
                    best_tour = list(neighbor)
                    self.record_progress(iteration, best_dist, best_tour)
            else:
                prob = math.exp(-delta_e / temperature)
                if random.random() < prob:
                    current_tour = neighbor
                    current_dist = neighbor_dist

            # Sample progress logging periodically to avoid bloated history size
            if iteration % 100 == 0:
                self.record_progress(iteration, best_dist, best_tour)

            temperature *= self.alpha
            iteration += 1

        self.record_progress(iteration, best_dist, best_tour)
        return best_tour


class GeneticAlgorithmTSP(Algorithm):
    """
    Permutation-based Genetic Algorithm designed to solve the TSP.
    Emphasizes explicit recombination (Ordered Crossover OX1) and Generational Elitism.
    """
    def __init__(self, population_size: int = 100, mutation_rate: float = 0.03, generations: int = 200, elite_count: int = 2, seed: int = None):
        super().__init__("Genetic Algorithm")
        self.pop_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.elite_count = elite_count
        self.seed = seed

    def _solve(self, test_case: TestCase) -> List[int]:
        if self.seed is not None:
            random.seed(self.seed)

        n = len(test_case.cities)
        if n <= 3:
            return list(range(n))

        # 1. Initialize Population of permutations (fixing start city 0)
        population = []
        for _ in range(self.pop_size):
            individual = list(range(1, n))
            random.shuffle(individual)
            population.append([0] + individual)

        # Helper to compute fitness (reciprocal of total distance)
        def get_fitness(ind: List[int]) -> float:
            dist = test_case.get_route_distance(ind)
            return 1.0 / max(1e-9, dist)

        # Track the global best historical individual
        best_tour = list(population[0])
        best_dist = test_case.get_route_distance(best_tour)
        self.record_progress(0, best_dist, best_tour)

        # 2. Recombination Helper: Ordered Crossover (OX1)
        # Leaving the first city index 0 fixed!
        def crossover_ox1(parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
            # Crossover points in index range [1, n-1]
            p1, p2 = sorted(random.sample(range(1, n), 2))
            
            def build_child(p_donor: List[int], p_filler: List[int]) -> List[int]:
                child = [-1] * n
                child[0] = 0
                # Copy segment between p1 and p2 from donor
                child[p1:p2+1] = p_donor[p1:p2+1]
                
                # Unfilled indices starting after p2 and wrapping around (skipping donor segment & city 0)
                unfilled_indices = []
                idx = (p2 + 1) % n
                while len(unfilled_indices) < n - (p2 - p1 + 1) - 1:
                    if idx != 0 and (idx < p1 or idx > p2):
                        unfilled_indices.append(idx)
                    idx = (idx + 1) % n
                
                # Elements from filler parent that are not in donor segment and not 0
                donor_set = set(p_donor[p1:p2+1])
                filler_elements = [val for val in p_filler if val != 0 and val not in donor_set]
                
                # Fill them in sequential order
                for target_idx, val in zip(unfilled_indices, filler_elements):
                    child[target_idx] = val
                    
                return child

            return build_child(parent1, parent2), build_child(parent2, parent1)

        # 3. Mutation Helper: Swap Mutation (excluding city index 0)
        def mutate_swap(ind: List[int]):
            if random.random() < self.mutation_rate:
                idx1, idx2 = random.sample(range(1, n), 2)
                ind[idx1], ind[idx2] = ind[idx2], ind[idx1]

        # 4. Selection Helper: Roulette Wheel (Fitness Proportionate)
        def select_parent(pop: List[List[int]], fitnesses: List[float], total_fit: float) -> List[int]:
            r = random.uniform(0, total_fit)
            curr = 0.0
            for ind, fit in zip(pop, fitnesses):
                curr += fit
                if curr >= r:
                    return ind
            return pop[-1]

        # Main Generational Loop
        for gen in range(1, self.generations + 1):
            # Guard: prevent execution from running longer than self.timeout seconds
            if time.perf_counter() - self.start_time > self.timeout:
                print(f"Genetic Algorithm: Timeout of {self.timeout}s exceeded! Terminating search early at generation {gen}.")
                break
                
            # Compute fitness scores for current population
            fitnesses = [get_fitness(ind) for ind in population]
            total_fitness = sum(fitnesses)
            
            # Record current generation's best individual
            gen_best_idx = max(range(self.pop_size), key=lambda i: fitnesses[i])
            gen_best_tour = population[gen_best_idx]
            gen_best_dist = test_case.get_route_distance(gen_best_tour)

            if gen_best_dist < best_dist:
                best_dist = gen_best_dist
                best_tour = list(gen_best_tour)
                self.record_progress(gen, best_dist, best_tour)

            # Implement Elitism: Gather the E absolute best individuals of the current population
            elites = []
            if self.elite_count > 0:
                elite_indices = sorted(range(self.pop_size), key=lambda i: fitnesses[i], reverse=True)[:self.elite_count]
                elites = [list(population[i]) for i in elite_indices]

            # Breed new offspring population
            offspring_pool = []
            while len(offspring_pool) < self.pop_size:
                # Select parents
                p1 = select_parent(population, fitnesses, total_fitness)
                p2 = select_parent(population, fitnesses, total_fitness)
                
                # Crossover
                c1, c2 = crossover_ox1(p1, p2)
                
                # Mutation
                mutate_swap(c1)
                mutate_swap(c2)
                
                offspring_pool.append(c1)
                if len(offspring_pool) < self.pop_size:
                    offspring_pool.append(c2)

            # Survivorship Replacement
            population = offspring_pool

            # Re-inject Elites by replacing the worst performing offspring in the pool
            if self.elite_count > 0:
                offspring_fitnesses = [get_fitness(ind) for ind in population]
                worst_indices = sorted(range(self.pop_size), key=lambda i: offspring_fitnesses[i])[:self.elite_count]
                for i, elite in zip(worst_indices, elites):
                    population[i] = list(elite)

            # Sample progress periodically
            if gen % 10 == 0:
                self.record_progress(gen, best_dist, best_tour)

        # Record final best tour
        self.record_progress(self.generations, best_dist, best_tour)
        return best_tour


class EvolutionaryProgrammingTSP(Algorithm):
    """
    Modern Continuous Evolutionary Programming (EP) designed to solve the TSP.
    Exposes a dynamic hyperparameters interface (population size, tournament size,
    generations, init_sigma) and leverages the clean OOP-based EvolutionaryEngine.
    """
    def __init__(self, population_size: int = 50, tournament_size: int = 10, generations: int = 200, init_sigma: float = 1.0, seed: int = None):
        super().__init__("Evolutionary Programming")
        self.pop_size = population_size
        self.q = tournament_size
        self.generations = generations
        self.init_sigma = init_sigma
        self.seed = seed

    def _solve(self, test_case: TestCase) -> List[int]:
        if self.seed is not None:
            random.seed(self.seed)

        # 1. Instantiate the dynamic OOP EvolutionaryEngine
        engine = EvolutionaryEngine(
            population_size=self.pop_size,
            tournament_size=self.q,
            generations=self.generations,
            init_sigma=self.init_sigma
        )

        # 2. Define callback to feed progress telemetries back to the Comparator framework
        def record_callback(generation: int, distance: float, route: List[int]):
            self.record_progress(generation, distance, route)

        # 3. Execute the OOP engine
        best_ind = engine.run(
            test_case=test_case,
            on_generation_callback=record_callback,
            time_limit=self.timeout  # Dynamic time safety guard
        )

        return best_ind.route
