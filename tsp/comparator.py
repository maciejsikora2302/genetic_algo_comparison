import time
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from .test_case import TestCase
from .algorithm import Algorithm

class Comparator:
    """
    Benchmarks, coordinates, and visually compares the performance of different TSP algorithms.
    
    Allows registering multiple algorithms, running them on shared TestCases,
    and plotting benchmarking graphs (e.g. execution time and route convergence).
    """

    def __init__(self):
        self.algorithms: List[Algorithm] = []
        self.results: Dict[str, Dict[str, Any]] = {}

    def register_algorithm(self, algorithm: Algorithm):
        """
        Adds an algorithm to the benchmark list.

        Args:
            algorithm (Algorithm): The algorithm instance to register.
        """
        self.algorithms.append(algorithm)
        print(f"Registered algorithm: {algorithm.name}")

    def run_comparison(self, test_case: TestCase) -> Dict[str, Dict[str, Any]]:
        """
        Runs all registered algorithms on a specific TSP test case.

        Args:
            test_case (TestCase): The TSP TestCase to solve.

        Returns:
            Dict[str, Dict[str, Any]]: Mapping of algorithm name to execution statistics.
        """
        self.results.clear()
        print(f"\n--- Running Benchmark for TestCase: '{test_case.name}' ---")
        n = len(test_case.cities)
        
        for algo in self.algorithms:
            if n > algo.max_supported_cities:
                print(f"Skipping {algo.name} (Problem size {n} exceeds limit of {algo.max_supported_cities} cities).")
                continue
                
            print(f"Executing {algo.name}...")
            best_route = algo.run(test_case, timeout=5.0)
            summary = algo.get_summary()
            
            self.results[algo.name] = {
                **summary,
                "best_route": best_route,
                "history": list(algo.history)  # Shallow copy of the progress history
            }
            print(f"Finished {algo.name}. Time: {summary['execution_time_seconds']:.4f}s | Best Dist: {summary['best_distance']:.2f}")
            
        return self.results

    def plot_time_comparison(self, save_path: str = None, show: bool = False, use_log: bool = True):
        """
        Generates a bar chart comparing execution times.

        Args:
            save_path (str, optional): Target image filepath. Defaults to None.
            show (bool, optional): Whether to display the plot. Defaults to False.
            use_log (bool, optional): If True, uses a logarithmic Y-axis to handle outliers. Defaults to True.
        """
        if not self.results:
            print("No benchmark results found. Run run_comparison first.")
            return

        names = list(self.results.keys())
        times = [res["execution_time_seconds"] for res in self.results.values()]

        style_map = {
            "Brute Force": {"color": "#7f8c8d"},
            "Held-Karp (DP)": {"color": "#95a5a6"},
            "Nearest Neighbor": {"color": "#1abc9c"},
            "2-Opt (Random Init)": {"color": "#3498db"},
            "2-Opt (NN Init)": {"color": "#3498db"},
            "Simulated Annealing (Random Init)": {"color": "#e67e22"},
            "Simulated Annealing (NN Init)": {"color": "#e67e22"},
            "Genetic Algorithm": {"color": "#9b59b6"},
            "Evolutionary Programming": {"color": "#2ecc71"}
        }
        
        def get_color(name: str, index: int) -> str:
            if name in style_map:
                return style_map[name]["color"]
            fallback_colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c']
            return fallback_colors[index % len(fallback_colors)]

        colors = [get_color(name, idx) for idx, name in enumerate(names)]

        plt.figure(figsize=(9, 6))
        bars = plt.bar(names, times, color=colors)
        
        # Annotate height values on top of bars
        for bar in bars:
            height = bar.get_height()
            # If height is extremely small, write it in scientific notation
            label_text = f"{height:.4f}s" if height >= 0.0001 else f"{height:.2e}s"
            plt.annotate(label_text,
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold', fontsize=9)

        # Tilt names slightly to be readable and prevent overlap
        plt.xticks(rotation=20, ha='right')

        if use_log:
            plt.yscale('log')
            plt.title("Execution Time Comparison (Logarithmic Scale - Lower is Better)")
            plt.ylabel("Time (Seconds, Log Scale)")
        else:
            plt.title("Execution Time Comparison (Lower is Better)")
            plt.ylabel("Time (Seconds)")

        plt.grid(axis='y', linestyle='--', alpha=0.5, which="both")

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        plt.close()

    def plot_convergence(self, save_path: str = None, show: bool = False, use_log_x: bool = True):
        """
        Plots a line chart showing progress of best distance over iterations.

        Args:
            save_path (str, optional): Target image filepath. Defaults to None.
            show (bool, optional): Whether to display the plot. Defaults to False.
            use_log_x (bool, optional): If True, uses a symmetrical log scale for the X-axis
                                        to prevent fast-converging algorithms from being squashed. Defaults to True.
        """
        if not self.results:
            print("No benchmark results found. Run run_comparison first.")
            return

        # Curated, consistent color, marker, and linestyle mapping for Premium UI
        style_map = {
            "Brute Force": {"color": "#7f8c8d", "marker": "x", "linestyle": ":"},
            "Held-Karp (DP)": {"color": "#95a5a6", "marker": "d", "linestyle": "-."},
            "Nearest Neighbor": {"color": "#1abc9c", "marker": "*", "linestyle": "--"},
            "2-Opt (Random Init)": {"color": "#3498db", "marker": "o", "linestyle": "-"},
            "2-Opt (NN Init)": {"color": "#3498db", "marker": "s", "linestyle": "--"},
            "Simulated Annealing (Random Init)": {"color": "#e67e22", "marker": "^", "linestyle": "-"},
            "Simulated Annealing (NN Init)": {"color": "#e67e22", "marker": "v", "linestyle": "--"},
            "Genetic Algorithm": {"color": "#9b59b6", "marker": "p", "linestyle": "-"},
            "Evolutionary Programming": {"color": "#2ecc71", "marker": "h", "linestyle": "-"}
        }
        
        def get_style(name: str, index: int) -> dict:
            if name in style_map:
                return style_map[name]
            fallback_colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c']
            fallback_markers = ['o', 's', '^', 'd', 'x', 'v', '*']
            fallback_linestyles = ['-', '--', ':', '-.']
            return {
                "color": fallback_colors[index % len(fallback_colors)],
                "marker": fallback_markers[index % len(fallback_markers)],
                "linestyle": fallback_linestyles[index % len(fallback_linestyles)]
            }

        # Varying line widths and drawing order so that overlapping lines are layered:
        num_algos = len(self.results)
        linewidths = [max(1.5, 4.5 - i * 0.8) for i in range(num_algos)]

        plt.figure(figsize=(10, 6))

        for idx, (name, data) in enumerate(self.results.items()):
            history = data["history"]
            if not history:
                continue
            
            iterations, distances, _ = zip(*history)
            
            style = get_style(name, idx)
            clr = style["color"]
            lst = style["linestyle"]
            mkr = style["marker"]
            lw = linewidths[idx % len(linewidths)]
            
            plt.plot(
                iterations, 
                distances, 
                label=name, 
                color=clr,
                marker=mkr, 
                markersize=6 - (idx % 3), 
                linewidth=lw,
                linestyle=lst,
                alpha=0.85  # Transparency helps see overlap intersections
            )

        if use_log_x:
            plt.xscale('symlog')
            plt.title("Convergence Comparison (Route Distance over Iterations - Log-X Scale)")
            plt.xlabel("Iteration / Epoch (Symlog Scale)")
        else:
            plt.title("Convergence Comparison (Route Distance over Iterations)")
            plt.xlabel("Iteration / Epoch")

        plt.ylabel("Total Route Distance")
        plt.legend(loc="upper right")
        plt.grid(True, linestyle='--', alpha=0.5, which="both")

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        plt.close()

    def plot_performance_ranking(self, save_path: str = None, show: bool = False):
        """
        Generates a dual-panel visualization comparing the algorithms across a new metric:
        Optimality vs Efficiency (time).
        
        Left Panel: A trade-off scatter plot of Optimality Gap (%) vs Execution Time (Log Scale).
        Right Panel: A ranked Performance Score Index combining both route quality and speed.
        """
        if not self.results:
            print("No benchmark results found. Run run_comparison first.")
            return

        import math
        
        # 1. Identify the best distance found across all executed algorithms
        best_dist = min(res["best_distance"] for res in self.results.values())
        if best_dist == 0 or math.isinf(best_dist):
            print("Error calculating best distance for performance ranking.")
            return

        # 2. Gather data and compute scores
        names = []
        gaps = []
        times = []
        combined_scores = []
        
        log_times = [math.log10(max(1e-9, res["execution_time_seconds"])) for res in self.results.values()]
        min_log = min(log_times)
        max_log = max(log_times)
        log_range = max_log - min_log if max_log != min_log else 1.0

        for name, res in self.results.items():
            dist = res["best_distance"]
            time_s = max(1e-9, res["execution_time_seconds"])
            
            # Optimality Gap (%)
            gap = ((dist - best_dist) / best_dist) * 100.0
            
            # Distance Score: 100 means global best, drops as route gets worse
            dist_score = 100.0 * (best_dist / dist)
            
            # Time Score: 100 means fastest solver, 0 means slowest solver (logarithmic scale)
            curr_log = math.log10(time_s)
            time_score = 100.0 * (1.0 - (curr_log - min_log) / log_range)
            
            # Combined performance score: 50% speed + 50% route quality
            score = 0.5 * dist_score + 0.5 * time_score
            
            names.append(name)
            gaps.append(gap)
            times.append(time_s)
            combined_scores.append(score)

        # Create the figure with two subplots side-by-side
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
        fig.suptitle("Algorithm Performance Analysis: Efficiency vs. Route Quality", fontsize=16, fontweight='bold')

        # --- LEFT PANEL: Optimality vs. Time Scatter Plot ---
        # Ideal solver is in the bottom-left corner
        style_map = {
            "Brute Force": {"color": "#7f8c8d"},
            "Held-Karp (DP)": {"color": "#95a5a6"},
            "Nearest Neighbor": {"color": "#1abc9c"},
            "2-Opt (Random Init)": {"color": "#3498db"},
            "2-Opt (NN Init)": {"color": "#3498db"},
            "Simulated Annealing (Random Init)": {"color": "#e67e22"},
            "Simulated Annealing (NN Init)": {"color": "#e67e22"},
            "Genetic Algorithm": {"color": "#9b59b6"},
            "Evolutionary Programming": {"color": "#2ecc71"}
        }

        def get_scatter_color(name: str, index: int) -> str:
            if name in style_map:
                return style_map[name]["color"]
            fallback_colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c']
            return fallback_colors[index % len(fallback_colors)]

        for i, name in enumerate(names):
            color = get_scatter_color(name, i)
            ax1.scatter(times[i], gaps[i], color=color, s=180, edgecolors='black', zorder=5, label=name)
            # Annotate names slightly above the points
            ax1.annotate(name, (times[i], gaps[i]), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='bold', fontsize=8)

        ax1.set_xscale('log')
        ax1.set_xlabel("Execution Time (Seconds, Log Scale)", fontsize=11)
        ax1.set_ylabel("Optimality Gap (%) - Lower is Better", fontsize=11)
        ax1.set_title("Time-Optimality Trade-off Plane", fontsize=13, fontweight='bold')
        ax1.grid(True, which="both", linestyle='--', alpha=0.5)
        
        # Highlight a hypothetical "ideal region" near the bottom left
        xlims = ax1.get_xlim()
        ylims = ax1.get_ylim()
        ax1.axvspan(xlims[0], xlims[0] * 5.0, color='green', alpha=0.08, label="High-Performance Zone")
        ax1.legend(loc="upper right", fontsize=8)

        # --- RIGHT PANEL: Ranked Combined Performance Index ---
        # Sort data by combined score in descending order
        sorted_indices = sorted(range(len(combined_scores)), key=lambda k: combined_scores[k], reverse=True)
        sorted_names = [names[i] for i in sorted_indices]
        sorted_scores = [combined_scores[i] for i in sorted_indices]
        
        y_pos = range(len(sorted_names))
        bars = ax2.barh(y_pos, sorted_scores, color=['#2ecc71' if s >= 80 else '#3498db' if s >= 50 else '#e74c3c' for s in sorted_scores], edgecolor='black')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(sorted_names, fontsize=10, fontweight='bold')
        ax2.invert_yaxis()  # top-down ranking
        
        ax2.set_xlabel("Performance Score (0 to 100, Combined)", fontsize=11)
        ax2.set_title("Overall Algorithm Value Ranking (Quality & Speed)", fontsize=13, fontweight='bold')
        ax2.set_xlim(0, 110)
        ax2.grid(axis='x', linestyle='--', alpha=0.5)

        # Annotate rank and scores on top of bars
        for idx, bar in enumerate(bars):
            width = bar.get_width()
            rank_label = f"#{idx+1} (Score: {width:.1f})"
            ax2.text(width + 2, bar.get_y() + bar.get_height()/2, rank_label, 
                     ha='left', va='center', fontweight='bold', fontsize=9)

        plt.tight_layout()

        if save_path:
            import os
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        plt.close()
