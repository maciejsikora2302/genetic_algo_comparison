# TSP Algorithm Comparison Framework

A highly modular, extensible Python benchmarking framework designed to compare multiple algorithms on the same instances of the **Traveling Salesman Problem (TSP)**. 

This framework cleanly separates the problem data representation (`TestCase`), the solver interfaces (`Algorithm`), the advanced visualization engine (`Visualize`), and the multi-objective benchmarking pipeline (`Comparator`).

---

## 📂 Project Architecture & Output Directory Layout

```
genetic_algo_comparison/
├── tsp/
│   ├── __init__.py       # Package entry point exposing TestCase, Visualize, Comparator, and Solvers
│   ├── test_case.py      # TestCase class: holds city positions & calculates distance matrices
│   ├── algorithm.py      # Algorithm class: base class providing telemetry, loggers & safety attributes
│   ├── evolutionary_programming.py  # [NEW] EP engine: EPIndividual, EPPopulation, EvolutionaryEngine
│   ├── solvers.py        # Implemented TSP solvers (including GA and EP) delegating to engines
│   ├── visualize.py      # Visualize class: renders route plots and compiles progress GIFs
│   └── comparator.py     # Comparator class: benchmarks solvers and plots performance indices
├── outputs/              # Benchmarking output repository
│   └── medium_15-city_benchmark/       # Structured output folder per TestCase
│       ├── initial_state.png           # Map of unlinked city coordinate positions
│       ├── execution_time.png          # Bar chart comparing compute speed (Log Y-scale, tilted labels)
│       ├── convergence.png             # Convergence graph tracking optimization (Symlog X-axis, layered)
│       ├── performance_ranking.png     # Dual-panel Optimality-vs-Efficiency ranking chart
│       ├── final_routes/               # Folder containing static final route plots
│       │   ├── brute_force.png
│       │   ├── held_karp_dp.png
│       │   ├── nearest_neighbor.png
│       │   ├── 2_opt_random_init.png
│       │   ├── 2_opt_nn_init.png
│       │   ├── simulated_annealing_random_init.png
│       │   └── simulated_annealing_nn_init.png
│       └── progressions/               # Detailed progression histories per solver
│           ├── 2_opt_random_init/      # Progression folder for 2-Opt (Random Init)
│           │   ├── frame_000.png       # Sequential progress frame PNGs (up to 100 frames)
│           │   ├── frame_001.png
│           │   ├── ...
│           │   ├── animation_1fps.gif  # Very slow speed profile GIF
│           │   ├── animation_3fps.gif  # Slow speed profile GIF
│           │   ├── animation_5fps.gif  # Standard speed profile GIF
│           │   ├── animation_10fps.gif # Fast speed profile GIF
│           │   └── animation_20fps.gif # Very fast transition sweep GIF
│           └── ...
├── main.py               # Main CLI runner script (supports argparse fast iterations)
│   └── README.md             # Framework reference documentation (This file)
```

---

## 🚀 Implemented Algorithms & Variations

We support **9 distinct solver configurations** representing exact methods, constructive heuristics, local searches, metaheuristics, and evolutionary optimizers:

### 1. Brute Force (Permutations)
*   **Class**: Exact Search ($\mathcal{O}(N!)$ time complexity).
*   **Logic**: Evaluates all permutations of city indices. Fixes the starting city to `0` to prune circular replicates.
*   **Safety Threshold**: Dynamically bypassed for test cases exceeding **10** cities.

### 2. Held-Karp (Dynamic Programming)
*   **Class**: Exact Dynamic Programming ($\mathcal{O}(N^2 2^N)$ time complexity).
*   **Logic**: Solves subproblems recursively using bitwise mask state memoization. Reconstructs the exact optimal path via back-pointers.
*   **Safety Threshold**: Dynamically bypassed for test cases exceeding **18** cities.

### 3. Nearest Neighbor
*   **Class**: Greedy Constructive Heuristic ($\mathcal{O}(N^2)$ time complexity).
*   **Logic**: Starts at city `0` and iteratively appends the nearest unvisited node.

### 4. 2-Opt (Random Init)
*   **Class**: Local Search ($\mathcal{O}(N^2)$ pass complexity).
*   **Logic**: Starts from a **completely random shuffled route** (rotated so city `0` is at index 0). Systematically reverses segments to resolve crossing edges. Illustrates path untangling clearly in progressions (~20+ frames).

### 5. 2-Opt (NN Init)
*   **Class**: Local Search.
*   **Logic**: Starts from a pre-optimized **Nearest Neighbor** route, leading to rapid refinement in very few steps (~4 frames).

### 6. Simulated Annealing (Random Init)
*   **Class**: Metaheuristic Global Search.
*   **Logic**: Starts from a chaotic random tour. Explores the neighborhood by swapping edges, accepting worse paths with a probability $P = e^{-\frac{\Delta E}{T}}$ that decays over time ($T \leftarrow T \times \alpha$) to escape local minima.

### 7. Simulated Annealing (NN Init)
*   **Class**: Metaheuristic Global Search.
*   **Logic**: Starts search from a pre-optimized **Nearest Neighbor** route, demonstrating high-quality convergence.

### 8. Genetic Algorithm (GA)
*   **Class**: Generational Evolutionary Optimizer.
*   **Logic**: Maintains a population of path permutations starting with city `0`. Standard genetic operators breed successive generations:
    *   **Selection**: Fitness proportionate (Roulette Wheel) selection.
    *   **Crossover**: Ordered Crossover (OX1) preserves parent ordering segments without duplicating cities.
    *   **Mutation**: Swap Mutation applied with a low probability ($p_m \in [0.01, 0.05]$) to avoid premature convergence.
    *   **Survivorship**: Generational elitism keeps the best individuals unchanged between steps.
*   **Safety Guard**: Search executes with a strict **5.0-second** execution timeout limit (returning the best solution found so far if breached).

### 9. Evolutionary Programming (EP)
*   **Class**: Behavioral Evolutionary Optimizer (Fogel continuous paradigm).
*   **OOP Abstractions**: Exposes clean modularity through a dedicated engine under `tsp/evolutionary_programming.py`:
    *   `EPIndividual`: Represents objective real-valued variables $x$ and self-adaptive mutation step sizes $\sigma$. Decodes tours using the **Random Keys** paradigm.
    *   `EPPopulation`: Handles initialization, evaluation, offspring production, and selection.
    *   `EvolutionaryEngine`: Executes the central pipeline and exports stats (variance, mean, and best fitness).
*   **Logic**: Strictly follows behavioral evolution principles (excluding crossover entirely):
    *   **Representation**: Decodes continuous variables using **Random Keys** (sorting coordinates $1 \dots n-1$ relative to start city `0`).
    *   **Mutation**: Self-adaptive Gaussian mutation updates the step size $\sigma$ alongside continuous variables:
        $$\sigma'_i(j) = \sigma_i(j) \cdot \exp\left(\tau \cdot N(0,1) + \tau' \cdot N_j(0,1)\right)$$
        $$x'_i(j) = x_i(j) + \sigma'_i(j) \cdot N_j(0,1)$$
        where standard scaling coefficients are $\tau = (2d)^{-1/2}$ and $\tau' = (2\sqrt{d})^{-1/2}$ for dimension $d = n - 1$.
    *   **Selection**: Stochastic tournament selection. Individuals in the combined population (size $2P$) compete in head-to-head fitness matches against $q$ random opponents, ranking them by win counts to preserve the top $P$ parents.
*   **Safety Guard**: Search executes with a strict **5.0-second** execution timeout limit (returning the best solution found so far if breached).

---

## 📊 Premium Visualization & Layout Features

To make comparisons publication-ready and eliminate visual outliers, the framework implements the following layout features:

### 1. Symmetrical Logarithmic X-Axis (`symlog`)
Convergence plots use a `symlog` scale on the X-axis (`plt.xscale('symlog')`). This allows fast constructive solvers (finishing in 1–10 iterations) to show their step-by-step improvements clearly on the left side of the chart, alongside metaheuristics running for 300,000+ steps on the right.

### 2. Logarithmic Y-Axis (`log`)
Execution time plots use a `log` scale on the Y-axis (`plt.yscale('log')`). Sub-millisecond heuristic runs (e.g. $0.00005$ seconds) are plotted clearly next to computationally heavy algorithms without being squashed.

### 3. Tilted Tick Labels
Tick labels on the execution time chart are rotated by 20 degrees and right-aligned (`plt.xticks(rotation=20, ha='right')`) to prevent text overlap.

### 4. Concentric Path Layering (Overlay Mitigation)
When exact solvers overlay identical trajectories, convergence lines will sit directly on top of each other. We resolve this using a concentric style engine:
*   **Line Width Scaling**: Varies thickness from thickest (drawn first) to thinnest (drawn last).
*   **Marker & Style Cycling**: Cycles through distinct markers (circles, squares, triangles) and line patterns (`solid`, `dashed`, `dotted`).
*   **Alpha Transparency**: `alpha=0.85` opacity blending ensures lower lines peek out inside the hollow centers of upper lines.

### 5. Dual-Panel Performance Ranking (`performance_ranking.png`)
Computes a **Combined Performance Score (0 to 100)**:
*   **Optimality Component (50%)**: $100 \times (\text{Best Distance} / \text{Solver Distance})$
*   **Efficiency Component (50%)**: Log-normalized execution speed score to balance speed outliers.
*   **Dual Panel**:
    *   *Left*: Optimality Gap (%) vs. Execution Time (seconds, log scale) scatter plot highlighting a shaded **"High-Performance Zone"**.
    *   *Right*: Sorted horizontal bar chart ranking all 7 solvers based on their balanced value score.

---

## 🏎️ Multiple Speed Profile GIF Animations

Frame progressions are generated frame-by-frame (up to 100 frames) showing optimization progression, and compiled into **5 distinct speed profile GIFs** inside the progressions subfolders:
*   `animation_1fps.gif` (very slow speed visual audit)
*   `animation_3fps.gif` (slow speed)
*   `animation_5fps.gif` (standard speed)
*   `animation_10fps.gif` (fast speed)
*   `animation_20fps.gif` (very fast sweep transition)

---

## 🛡️ Unified Timeout Safety Guards (5.0s Max per Run)

To protect execution runtimes against excessive computational delays on high-dimensional instances, the framework enforces a **strict, unified 5.0-second execution timeout guard** across **all** optimization algorithms:
*   **Constructive Heuristics / Local Searches (2-Opt & SA)**: Periodically check elapsed compute time within their search loops. If it exceeds 5.0s, they terminate iteration sweeps immediately and return their best-known path discovered up to that fraction of a second.
*   **Evolutionary Solvers (GA & EP)**: Monitor absolute time budgets during generational iteration cycles, breaking out of recombination/selection/mutation phases early if the timeout threshold is reached.
*   **Exact Solvers (Brute Force & HK)**: In addition to their hard-coded city scaling caps, they actively check time offsets within recursion frames/permutation loops, exiting immediately if the limit is breached.

---

## 🏆 Benchmark Scenarios & Scales

The suite supports **5 scale benchmarks** to systematically stress-test exact and heuristic algorithms side-by-side:
1.  **Small (8 Cities)**: Evaluates exact global optima across all solvers.
2.  **Standard (10 Cities)**: Standard comparison checking execution scaling curves.
3.  **Medium (15 Cities)**: Bypasses brute force, comparing dynamic programming (HK) and metaheuristics.
4.  **Large (30 Cities)**: Bypasses exact solvers, comparing heuristics and evolutionary algorithms.
5.  **Huge (50 Cities) [NEW]**: Bypasses exact solvers, presenting a highly challenging search space of $(50-1)!/2 \approx 3.04 \times 10^{62}$ possible routes. This scale emphasizes how constructive starts (like NN Init) and self-adaptive mutation parameters (EP) scale under tight 5.0s limits.

---

## ⚡ Command-Line Interface & Fast Iterations

The runner script support command-line arguments to speed up code iteration.

### Run All Benchmarks:
To run the full suite (Small, Standard, Medium, Large benchmarks):
```bash
python main.py
```

### Scale-Specific Iterations (Fast Evaluation):
You can isolate benchmarking runs to a specific problem scale to iterate quickly:
*   **Medium-Only (15 Cities)**:
    ```bash
    python main.py --medium-only
    ```
    or `python main.py -m`
*   **Large-Only (30 Cities)**:
    ```bash
    python main.py --large-only
    ```
    or `python main.py -l`
*   **Huge-Only (50 Cities)**:
    ```bash
    python main.py --huge-only
    ```
    or `python main.py -g`
