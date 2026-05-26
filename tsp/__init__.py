"""
TSP Algorithm Comparison Package.
This package provides a modular structure to define TSP instances,
implement search/optimization algorithms, visualize routes/animations,
and compare multiple algorithms.
"""

from .test_case import TestCase
from .algorithm import Algorithm
from .visualize import Visualize
from .comparator import Comparator
from .solvers import (
    BruteForceTSP,
    HeldKarpTSP,
    NearestNeighborTSP,
    TwoOptTSP,
    SimulatedAnnealingTSP,
    GeneticAlgorithmTSP,
    EvolutionaryProgrammingTSP
)

__all__ = [
    "TestCase", 
    "Algorithm", 
    "Visualize", 
    "Comparator",
    "BruteForceTSP",
    "HeldKarpTSP",
    "NearestNeighborTSP",
    "TwoOptTSP",
    "SimulatedAnnealingTSP",
    "GeneticAlgorithmTSP",
    "EvolutionaryProgrammingTSP"
]
