import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from .test_case import TestCase

class Algorithm(ABC):
    """
    Abstract Base Class for Traveling Salesman Problem (TSP) solvers.
    
    Provides standardized quality-of-life utilities to capture:
    - Route improvements over iterations (history tracking)
    - Execution time
    - Performance metrics
    """

    def __init__(self, name: str):
        """
        Initializes the base algorithm instance.

        Args:
            name (str): Human-readable name of the algorithm (e.g., 'Genetic Algorithm').
        """
        self.name = name
        self.history: List[Tuple[int, float, List[int]]] = []  # List of (iteration, distance, route)
        self.execution_time: float = 0.0
        self.max_supported_cities: int = float('inf')  # Limit on problem size for safety


    def record_progress(self, iteration: int, distance: float, route: List[int]):
        """
        QoL Utility: Logs the progress/improvement of the algorithm at a given iteration.

        Args:
            iteration (int): The current iteration, epoch, or generation.
            distance (float): The total route distance at this step.
            route (List[int]): The sequence of city indices.
        """
        # Save a copy of the route to prevent reference mutation issues
        self.history.append((iteration, distance, list(route)))

    def clear_history(self):
        """
        Resets history logs and timing records. Useful before re-running.
        """
        self.history.clear()
        self.execution_time = 0.0

    def run(self, test_case: TestCase, timeout: float = 5.0) -> List[int]:
        """
        Wraps the abstract `_solve` method with timing, timeout, and resetting mechanics.

        Args:
            test_case (TestCase): The TSP instance to solve.
            timeout (float): Max execution time in seconds. Defaults to 5.0.

        Returns:
            List[int]: The final computed route.
        """
        self.clear_history()
        self.start_time = time.perf_counter()
        self.timeout = timeout
        
        # Call the underlying implementation
        best_route = self._solve(test_case)
        
        self.execution_time = time.perf_counter() - self.start_time
        return best_route

    @abstractmethod
    def _solve(self, test_case: TestCase) -> List[int]:
        """
        The core solving algorithm logic. Must be implemented by subclasses.

        Args:
            test_case (TestCase): The TSP instance to solve.

        Returns:
            List[int]: The final computed route.
        """
        pass

    def get_summary(self) -> Dict[str, Any]:
        """
        QoL Utility: Retrieves execution telemetry.

        Returns:
            Dict[str, Any]: Metrics including name, time, best distance, and iteration count.
        """
        best_distance = self.history[-1][1] if self.history else float('inf')
        return {
            "algorithm_name": self.name,
            "execution_time_seconds": self.execution_time,
            "best_distance": best_distance,
            "iterations_logged": len(self.history)
        }
