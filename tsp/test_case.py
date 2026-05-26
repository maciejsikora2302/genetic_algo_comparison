import math
import random
from typing import List, Tuple

class TestCase:
    """
    Represents a specific Traveling Salesman Problem (TSP) instance.
    
    Contains the cities' coordinates, computes pair-wise distances, and provides
    static/class methods to easily generate new test scenarios.
    """

    def __init__(self, name: str, cities: List[Tuple[float, float]]):
        """
        Initializes a TestCase instance.

        Args:
            name (str): Identifier or description for this test case.
            cities (List[Tuple[float, float]]): Coordinates of each city represented as (x, y) tuples.
        """
        self.name = name
        self.cities = cities
        self.distance_matrix = self._compute_distance_matrix()

    def _compute_distance_matrix(self) -> List[List[float]]:
        """
        Computes the complete pairwise Euclidean distance matrix for the cities.

        Returns:
            List[List[float]]: A 2D list where element [i][j] is the distance between city i and city j.
        """
        n = len(self.cities)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    x1, y1 = self.cities[i]
                    x2, y2 = self.cities[j]
                    matrix[i][j] = math.hypot(x2 - x1, y2 - y1)
        return matrix

    def get_route_distance(self, route: List[int]) -> float:
        """
        Calculates the total distance of a given route (tour).

        Args:
            route (List[int]): List of city indices representing the sequence of visited cities.

        Returns:
            float: Total travel distance including return to the starting city.
        """
        if not route or len(route) != len(self.cities):
            return float('inf')
        
        total_dist = 0.0
        for i in range(len(route)):
            current_city = route[i]
            next_city = route[(i + 1) % len(route)]
            total_dist += self.distance_matrix[current_city][next_city]
        return total_dist

    @classmethod
    def generate_random(cls, name: str, num_cities: int, width: float = 100.0, height: float = 100.0, seed: int = None) -> 'TestCase':
        """
        Generates a synthetic TestCase with random 2D coordinate placements.

        Args:
            name (str): Name of the generated test case.
            num_cities (int): Total number of cities in the TSP.
            width (float, optional): Maximum X coordinate. Defaults to 100.0.
            height (float, optional): Maximum Y coordinate. Defaults to 100.0.
            seed (int, optional): Seed for reproducibility. Defaults to None.

        Returns:
            TestCase: A new TestCase instance.
        """
        if seed is not None:
            random.seed(seed)
            
        cities = [(random.uniform(0, width), random.uniform(0, height)) for _ in range(num_cities)]
        return cls(name, cities)
