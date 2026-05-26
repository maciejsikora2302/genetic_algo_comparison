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

    @classmethod
    def generate_clustered(cls, name: str, num_cities: int, num_clusters: int = 3, cluster_radius: float = 8.0, width: float = 100.0, height: float = 100.0, seed: int = None) -> 'TestCase':
        """
        Generates a synthetic TestCase with cities placed in tight clusters that are far apart.

        Args:
            name (str): Name of the generated test case.
            num_cities (int): Total number of cities in the TSP.
            num_clusters (int, optional): Number of distinct clusters. Defaults to 3.
            cluster_radius (float, optional): Maximum radius of a city from its cluster center. Defaults to 8.0.
            width (float, optional): Maximum X coordinate for cluster centers. Defaults to 100.0.
            height (float, optional): Maximum Y coordinate for cluster centers. Defaults to 100.0.
            seed (int, optional): Seed for reproducibility. Defaults to None.

        Returns:
            TestCase: A new TestCase instance.
        """
        if seed is not None:
            random.seed(seed)

        if num_clusters <= 0:
            num_clusters = 1

        # Generate cluster centers, leaving padding so clusters don't get generated outside the canvas
        padding = cluster_radius
        centers = []
        for _ in range(num_clusters):
            cx = random.uniform(padding, width - padding)
            cy = random.uniform(padding, height - padding)
            centers.append((cx, cy))

        # Distribute cities among clusters
        cities_per_cluster = [num_cities // num_clusters] * num_clusters
        for i in range(num_cities % num_clusters):
            cities_per_cluster[i] += 1

        cities = []
        for cluster_idx, count in enumerate(cities_per_cluster):
            cx, cy = centers[cluster_idx]
            for _ in range(count):
                # Generate a city in a random circular offset around the cluster center
                r = random.uniform(0, cluster_radius)
                theta = random.uniform(0, 2 * math.pi)
                x = cx + r * math.cos(theta)
                y = cy + r * math.sin(theta)
                cities.append((x, y))

        return cls(name, cities)

