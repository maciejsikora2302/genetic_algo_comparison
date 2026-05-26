# TSP Algorithm Comparison Framework

A highly modular, extensible Python benchmarking framework designed to compare multiple algorithms on the same instances of the **Traveling Salesman Problem (TSP)**. 

This framework cleanly separates the problem data representation (`TestCase`), the solver interfaces (`Algorithm`), the advanced visualization engine (`Visualize`), and the multi-objective benchmarking pipeline (`Comparator`).

---

## 📂 Project Architecture & Code Structure ("What is What")

The framework is organized into a modular structure where concerns (data, solving logic, visualization, comparison) are isolated.

```
genetic_algo_comparison/
├── tsp/                              # Core TSP Framework Package
│   ├── __init__.py                   # Package entry point exposing TestCase, Visualize, Comparator, and Solvers
│   ├── test_case.py                  # TestCase class: holds city positions & calculates distance matrices
│   ├── algorithm.py                  # Algorithm class: base class providing telemetry, loggers & safety attributes
│   ├── evolutionary_programming.py    # EP engine: EPIndividual, EPPopulation, EvolutionaryEngine
│   ├── solvers.py                    # Implemented TSP solvers (including GA and EP) delegating to engines
│   ├── visualize.py                  # Visualize class: renders route plots and compiles progress GIFs
│   └── comparator.py                 # Comparator class: benchmarks solvers and plots performance indices
├── outputs/                          # Benchmarking output repository
│   └── [benchmark_name]/             # Structured output folder per TestCase (e.g. medium_15-city_benchmark)
│       ├── initial_state.png         # Map of unlinked city coordinate positions
│       ├── execution_time.png        # Bar chart comparing compute speed (Log Y-scale, tilted labels)
│       ├── convergence.png           # Convergence graph tracking optimization (Symlog X-axis, layered)
│       ├── performance_ranking.png   # Dual-panel Optimality-vs-Efficiency ranking chart
│       ├── best_route_[winning_algorithm].png # Visual route plot of the single overall winning algorithm (shortest distance)
│       ├── final_routes/             # Folder containing static final route plots per solver
│       └── progressions/             # Detailed progression histories and animated GIFs per solver
├── main.py                           # Main CLI runner script (supports argparse fast iterations)
└── README.md                         # Framework reference documentation (This file)
```

### Detailed Component Analysis ("What is What")

*   **`main.py`**: The central execution entry point. It parses command-line arguments to support targeted benchmark runs (e.g. `--medium-only`, `--large-only`, or `--huge-only`), instantiates the problem scales (`TestCase`), registers all 9 solver variations to the comparison suite, and triggers the automated visualization and output-saving pipeline.
*   **`tsp/test_case.py`**: Holds problem definitions. The `TestCase` class contains the spatial coordinates of each city. Upon initialization, it computes a complete, pairwise Euclidean distance matrix using `math.hypot` to allow fast constant-time edge queries during search. It provides methods to calculate the total path distance of any circular route (including return to start) and generates random 2D coordinate placements using seed-based synthetic generators, as well as clustered distributions where tight clusters are located far apart from one another.
*   **`tsp/algorithm.py`**: Defines the `Algorithm` Abstract Base Class (ABC). Every TSP solver subclasses this base. It provides standard execution controls: resetting history, timing execution speed using a high-precision performance counter (`time.perf_counter`), enforcing execution timeouts, tracking intermediate search paths via `record_progress`, and generating standardized performance summary dictionaries.
*   **`tsp/evolutionary_programming.py`**: Houses the dedicated continuous self-adaptive Evolutionary Programming (EP) engine. Rather than cluttering the solver interface, it defines:
    *   `EPIndividual`: A candidate solution containing real-valued coordinates $x$ and self-adaptive standard deviations $\sigma$. Includes decoding logic and fitness caching.
    *   `EPPopulation`: Manages collection-level routines (initialization, mutation, parallel evaluation, and stochastic selection).
    *   `EvolutionaryEngine`: Executes the generational loop, monitors timeout safety limits, and prints runtime telemetry (best fitness, mean fitness, and mutation step variance).
*   **`tsp/solvers.py`**: Houses the actual algorithmic implementations. By subclassing `Algorithm` and implementing the `_solve` method, it exposes 7 concrete solver classes (yielding 9 benchmark configurations when varying starting route initializations) and coordinates their execution safely.
*   **`tsp/visualize.py`**: Renders all visual outputs. Using `matplotlib` and `Pillow`, it generates static plots of city layouts and final computed routes, saves individual transition frames tracking optimization progress, and compiles these frames into 5 distinct speed-profile animated GIFs.
*   **`tsp/comparator.py`**: Runs registered solvers on shared `TestCase` instances. It gathers performance summaries and generates comparison figures, including execution-time comparisons (log scale), convergence logs over search iterations (symmetrical log X-axis), and the custom dual-panel value-ranking chart.

---

## 🚀 Implemented Algorithms & Deep-Dive Descriptions

The framework implements **7 unique algorithms** representing distinct optimization paradigms, expanding into **9 total solver configurations** via alternative initializations. Each algorithm is detailed below, outlining its class type, time and space complexity, core principles, and step-by-step operation.

---

### 1. Brute Force (Exact Search)
*   **Class/Type**: Exact Exhaustive Search
*   **Complexity**:
    *   **Time Complexity**: $\mathcal{O}(N!)$ — grows factorially, restricting practical usage to very small dimensions.
    *   **Space Complexity**: $\mathcal{O}(1)$ auxiliary space — only tracks the current permutation and best route.
*   **Key Principles**:
    *   **Exhaustive Space Exploration**: Evaluates every single possible city ordering to guarantee the absolute global optimum.
    *   **Circular Pruning (Symmetry Breaking)**: Fixes the starting city at index `0` and permutes only the remaining $N-1$ cities. Since any tour is circular and has $N$ equivalent cyclic shifts, this optimization divides the search space by $N$, reducing permutations from $N!$ to $(N-1)!$.
*   **How It Works**:
    1.  Computes and records the distance of the initial sequential route `[0, 1, 2, ..., N-1]`.
    2.  Generates all permutations of the city indices $\{1, 2, ..., N-1\}$ using Python's `itertools.permutations`.
    3.  For each permutation, constructs a full route `[0] + list(perm)`.
    4.  Calculates the total tour distance. If the new distance is strictly shorter than the current minimum, records it as the new best.
    5.  Periodically checks the execution timer. If the runtime exceeds the hard safety limit (3.0 seconds), breaks the loop early and returns the best route discovered up to that point.
*   **Safety Threshold**: Hard-coded scaling bypass for test cases exceeding **10** cities (unless forced, to prevent excessive delays).

---

### 2. Held-Karp (Dynamic Programming)
*   **Class/Type**: Exact Dynamic Programming
*   **Complexity**:
    *   **Time Complexity**: $\mathcal{O}(N^2 2^N)$ — dramatically superior to brute force, making exact solutions feasible for medium scales.
    *   **Space Complexity**: $\mathcal{O}(N 2^N)$ — requires substantial memory to store the memoization table.
*   **Key Principles**:
    *   **Optimal Substructure**: The principle that any sub-tour of an optimal TSP tour must itself be an optimal path between those sub-tour endpoints.
    *   **State Compression (Bitmasking)**: Encodes the set of visited cities as an integer bitmask. If city $i$ is visited, the $i$-th bit of the mask is set to `1`.
    *   **Memoization**: Stores the results of recursive subproblems in a dictionary indexed by the state tuple `(mask, current_city)` to prevent redundant calculations.
*   **How It Works**:
    1.  Defines a recursive function `dp(mask, u)` which calculates the minimum cost to visit all remaining unvisited cities starting from city `u` and returning ultimately to the starting city `0`.
    2.  **Base Case**: When the bitmask equals $(1 \ll N) - 1$ (all bits are `1`, meaning all cities have been visited), the function returns the direct distance from `u` back to `0`.
    3.  **Recursive Step**: If the state `(mask, u)` is already in the memo table, returns the cached distance. Otherwise, it iterates through all unvisited cities $v$ (where the $v$-th bit in `mask` is `0`), computes the cost of going to $v$ and solving the remaining subproblem: $\text{dist}(u, v) + \text{dp}(\text{mask} \mid (1 \ll v), v)$.
    4.  Selects the minimum cost among all possible choices of $v$, records it in the memo table, and logs $v$ in a `parent` dictionary to reconstruct the optimal transitions.
    5.  Computes the global optimum by invoking `dp(1, 0)` (meaning we start at city `0` with only city `0` visited).
    6.  Reconstructs the optimal route by tracing back through the `parent` transitions from city `0` to the end.
*   **Safety Threshold**: Hard-coded scaling bypass for test cases exceeding **18** cities to prevent system memory exhaustion.

---

### 3. Nearest Neighbor
*   **Class/Type**: Greedy Constructive Heuristic
*   **Complexity**:
    *   **Time Complexity**: $\mathcal{O}(N^2)$ — highly efficient, completing sub-millisecond runs even on large scales.
    *   **Space Complexity**: $\mathcal{O}(N)$ — to store the active path and the set of unvisited cities.
*   **Key Principles**:
    *   **Local Greediness**: Makes the locally optimal choice at each step without looking ahead or considering global route structures.
    *   **Constructive Growth**: Builds a valid route step-by-step from scratch.
*   **How It Works**:
    1.  Establishes the starting position at city `0` and adds it to the path.
    2.  Maintains a set of `unvisited` cities initialized to contain $\{1, 2, ..., N-1\}$.
    3.  While the `unvisited` set is not empty, queries the precomputed distance matrix to locate the city $v \in \text{unvisited}$ that is closest to the current city.
    4.  Removes $v$ from the `unvisited` set, appends it to the path, and updates the current city to $v$.
    5.  Records intermediate partial tours (padded with the remaining unvisited nodes) at each step to allow visual step-by-step progressions.
    6.  Once all cities have been visited, appends the closing edge back to city `0` to complete the tour.
*   **Characteristics**: Very fast, but vulnerable to the "greedy trap" (where the final few cities are located far away, forcing the route to take extremely long, crossing lines to close the tour).

---

### 4. 2-Opt (Local Search)
*   **Class/Type**: Local Search / Hill-Climbing Heuristic
*   **Complexity**:
    *   **Time Complexity**: $\mathcal{O}(N^2)$ per complete sweep. Swaps continue iteratively until no further improvements are possible (typically taking $\mathcal{O}(K \cdot N^2)$ where $K$ is the number of improvements).
    *   **Space Complexity**: $\mathcal{O}(N)$ — stores the active route path coordinates.
*   **Key Principles**:
    *   **Neighborhood Search**: Explores the local neighborhood of a route by swapping pairs of edges.
    *   **Path Untangling**: Identifies crossing edges (which violate the triangle inequality in Euclidean space) and reverses the intermediate segment to uncross them.
    *   **Local Delta Evaluation**: Evaluates the cost change of a swap by calculating only the differences in the 4 affected edges, avoiding a full $O(N)$ path sum computation.
*   **How It Works**:
    1.  **Initialization**: Launches from one of two starting states:
        *   **Random Init**: Starts from a completely randomized shuffle of cities (rotated to begin with city `0`).
        *   **NN Init**: Starts from a pre-optimized **Nearest Neighbor** route.
    2.  Runs a loop looking for improvements. For every pair of indices $(i, j)$ where $1 \le i < j < N$:
        *   Identifies the edges that would be broken: $(path[i-1] \to path[i])$ and $(path[j] \to path[j+1])$.
        *   Identifies the new edges that would be created: $(path[i-1] \to path[j])$ and $(path[i] \to path[j+1])$.
        *   Computes the cost delta: $\Delta = [\text{dist}(path[i-1], path[j]) + \text{dist}(path[i], path[j+1])] - [\text{dist}(path[i-1], path[i]) + \text{dist}(path[j], path[j+1])]$.
    3.  If $\Delta < 0$ (the swap shortens the route):
        *   Reverses the entire path segment from index $i$ to $j$ in-place: `path[i:j+1] = path[i:j+1][::-1]`.
        *   Updates the total distance by adding $\Delta$.
        *   Logs the progress telemetry and restarts the scan from the beginning (first-improvement local search strategy).
    4.  If a full scan completes with no improving swaps, the route is "2-optimal" and the loop terminates.
*   **Configurations**:
    *   **2-Opt (Random Init)**: Excellent for demonstrating local search mechanics, showing dramatic visual "untangling" of highly chaotic paths across ~20+ steps.
    *   **2-Opt (NN Init)**: A powerful hybrid heuristic that converges extremely fast (often in under 4 steps) to very high-quality solutions.

---

### 5. Simulated Annealing (SA)
*   **Class/Type**: Metaheuristic Global Search
*   **Complexity**:
    *   **Time Complexity**: Controlled by the cooling schedule: $\mathcal{O}(M)$ where $M$ is the number of temperature steps, which is $\approx \log(T_{min}/T_{max}) / \log(\alpha)$. Each step performs a constant-time neighborhood mutation.
    *   **Space Complexity**: $\mathcal{O}(N)$ — stores the current, candidate, and best-known routes.
*   **Key Principles**:
    *   **Thermodynamic Analogy**: Models the physical cooling of a solid. At high temperatures, the system has high energy and can explore widely. As the temperature cools, it stabilizes into a low-energy state.
    *   **Metropolis Acceptance Criterion**: Accepts worse candidate solutions with a probability $P = \exp(-\Delta E / T)$, where $\Delta E$ is the increase in tour distance and $T$ is the current temperature. This allows the solver to escape local minima.
*   **How It Works**:
    1.  **Initialization**: Starts from either a **Random** or **Nearest Neighbor** route. Measures the initial distance.
    2.  Sets the starting temperature $T = T_{max}$ (default `100.0`), the cooling rate $\alpha$ (default `0.995`), and the minimum temperature $T_{min}$ (default `0.001`).
    3.  **Annealing Loop**: While $T > T_{min}$:
        *   Generates a candidate neighbor by randomly selecting two cities (excluding the fixed start city `0`) and swapping their positions in the tour.
        *   Computes the cost change $\Delta E = \text{distance(neighbor)} - \text{distance(current)}$.
        *   If $\Delta E < 0$ (the neighbor is better), accepts it immediately: `current = neighbor`. If it is also a global historical best, records it.
        *   If $\Delta E \ge 0$ (the neighbor is worse), draws a random float $r \sim U(0, 1)$. If $r < \exp(-\Delta E / T)$, accepts the worse candidate anyway to continue exploring.
        *   Updates the temperature: $T \leftarrow T \times \alpha$.
        *   Logs telemetry periodically (every 100 iterations) to track convergence without bloating history logs.
*   **Configurations**:
    *   **Simulated Annealing (Random Init)**: Standard SA search. Highly exploratory early on, eventually settling into a high-quality global optimum as the temperature approaches zero.
    *   **Simulated Annealing (NN Init)**: Fine-tuned SA search starting from a greedy route, designed to refine the constructive heuristic without disrupting its initial high quality.

---

### 6. Genetic Algorithm (GA)
*   **Class/Type**: Permutation-Based Evolutionary Optimizer
*   **Complexity**:
    *   **Time Complexity**: $\mathcal{O}(G \times P \times N)$ — where $G$ is the number of generations, $P$ is the population size, and $N$ is the number of cities.
    *   **Space Complexity**: $\mathcal{O}(P \times N)$ — to store the active chromosome populations.
*   **Key Principles**:
    *   **Darwinian Evolution**: Simulates natural selection where fitter individuals have a higher probability of passing their genetic material to the next generation.
    *   **Ordered Crossover (OX1)**: A specialized permutation crossover that preserves the relative sequence and ordering of cities from parents without producing duplicates.
    *   **Generational Elitism**: Copies the top $E$ best individuals of the current generation directly into the next, ensuring the absolute best solution never degrades.
*   **How It Works**:
    1.  **Population Initialization**: Generates $P$ random permutations of cities $\{1, ..., N-1\}$ prefixed with city `0` to build the initial population.
    2.  **Fitness Evaluation**: Evaluates each individual's route distance and assigns a fitness score $f = 1.0 / \text{distance}$.
    3.  **Generational Loop** (up to $G$ generations):
        *   **Elitism Step**: Sorts the population by fitness and copies the top $E$ (default `2`) individuals into an elite buffer.
        *   **Parent Selection (Roulette Wheel)**: Accumulates total population fitness and selects parents using a cumulative distribution sweep. Fitter individuals occupy larger segments of the wheel and are chosen more frequently.
        *   **Reproduction (Crossover)**: Breeds pairs of offspring using **Ordered Crossover (OX1)**:
            *   Selects two random crossover cut points.
            *   Copies the segment between the cuts directly from parent 1 to the offspring.
            *   Fills the remaining slots in the offspring using the cities of parent 2 in their exact relative order of appearance, wrapping around the cut points and skipping cities already copied.
            *   Repeats the process in reverse to build a second offspring.
        *   **Mutation**: Applies swap mutation with a low probability $p_m$ (default `0.03`). If triggered, swaps two random cities (excluding index `0`) to inject new genetic diversity.
        *   **Survivorship Replacement**: Replaces the parent population with the new offspring pool, and re-injects the elite individuals by overwriting the poorest performing offspring.
        *   Logs progress periodically and monitors the 5.0-second timeout safety guard.

---

### 7. Evolutionary Programming (EP)
*   **Class/Type**: Continuous Self-Adaptive Evolutionary Optimizer (Fogel Paradigm)
*   **Complexity**:
    *   **Time Complexity**: $\mathcal{O}(G \times P \times N \log N)$ — sorting continuous coordinates for Random Keys decoding adds a logarithmic scaling factor.
    *   **Space Complexity**: $\mathcal{O}(P \times N)$ — stores continuous variable arrays $x$ and step sizes $\sigma$.
*   **Key Principles**:
    *   **Behavioral Evolution**: Evolves species through continuous behavioral mutations rather than discrete gene swaps. Excludes sexual crossover entirely, relying solely on asexual reproduction.
    *   **Continuous Mapping (Random Keys)**: Converts the discrete TSP permutation space into a continuous space. An individual's state is a real-valued coordinate vector $x \in \mathbb{R}^{N-1}$. The discrete tour is decoded by sorting the indices of $x$ (prefixed with city `0`), guaranteeing valid tours.
    *   **Self-Adaptive Mutation**: Mutates both the objective variables $x$ and their corresponding strategic step sizes (standard deviations $\sigma$) simultaneously. This allows the algorithm to adaptively tune its own search step size, transitioning from broad exploration to localized exploitation.
    *   **Stochastic Tournament Selection**: A Fogel-style selection mechanism where candidates compete against random opponents in round-robin tournaments to earn wins, preserving elite behaviors without strict deterministic sorting.
*   **How It Works**:
    1.  **Continuous Initialization**: Creates $P$ individuals. Each individual is initialized with a continuous vector $x$ (drawn from $U(-1, 1)$) and a step-size vector $\sigma$ filled with a default initial standard deviation (default `1.0`).
    2.  **Decoding and Evaluation**: Decodes each continuous vector $x$ into a discrete path using the Random Keys sort. Computes the path distance and assigns fitness $f = 1.0 / \text{distance}$.
    3.  **Generational Loop** (up to $G$ generations):
        *   **Offspring Generation (Asexual Mutation)**: Each parent creates exactly one offspring. For each index $j$ in the continuous vector:
            *   Calculates a new step size: $\sigma'_j = \sigma_j \cdot \exp(\tau \cdot N(0, 1) + \tau' \cdot N_j(0, 1))$, where $\tau = (2d)^{-1/2}$ and $\tau' = (2\sqrt{d})^{-1/2}$ are standard evolutionary coefficients for dimension $d = N - 1$.
            *   Enforces boundary controls on $\sigma'_j$ ($[10^{-5}, 10.0]$) to protect against mathematical underflow or overflow.
            *   Calculates the mutated objective coordinate: $x'_j = x_j + \sigma'_j \cdot N_j(0, 1)$.
        *   **Offspring Evaluation**: Decodes and evaluates the fitness of the new $P$ offspring.
        *   **Stochastic Tournament Selection**: Combines parents and offspring into a pool of size $2P$.
            *   For each individual in the pool, selects $q$ (default `10`) random opponents from the pool.
            *   Compares fitness: the individual earns a win point for each opponent it matches or outperforms.
            *   Sorts the pool by win counts in descending order.
            *   Selects the top $P$ individuals to form the next generation.
        *   Logs step statistics (best fitness, mean fitness, and step-size variance) and monitors the 5.0s execution timeout guard.

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
    *   *Right*: Sorted horizontal bar chart ranking all solvers based on their balanced value score.

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

The suite supports **8 scale and topology benchmarks** to systematically stress-test exact and heuristic algorithms side-by-side:
1.  **Small (8 Cities)**: Evaluates exact global optima across all solvers.
2.  **Standard (10 Cities)**: Standard comparison checking execution scaling curves.
3.  **Medium (15 Cities)**: Bypasses brute force, comparing dynamic programming (HK) and metaheuristics.
4.  **Clustered Medium (18 Cities)**: Generates 18 cities clustered in 3 groups that are highly separated from each other. Evaluates how well solvers navigate isolated local subproblems vs. global connections. Runs exact solvers like Held-Karp to measure optimal bounds.
5.  **Large (30 Cities)**: Bypasses exact solvers, comparing heuristics and evolutionary algorithms.
6.  **Clustered Large (30 Cities)**: Generates 30 cities clustered in 5 tight groups. Stresses local search and metaheuristics under uneven clustered topological conditions.
7.  **Huge (50 Cities)**: Bypasses exact solvers, presenting a highly challenging search space of $(50-1)!/2 \approx 3.04 \times 10^{62}$ possible routes. This scale emphasizes how constructive starts (like NN Init) and self-adaptive mutation parameters (EP) scale under tight 5.0s limits.
8.  **Clustered Huge (50 Cities)**: Generates 50 cities clustered in 7 highly separated groups (cluster radius of 7.0). Highlights how structural spatial groupings affect genetic crossover mechanics vs. self-adaptive EP continuous searches.

---

## ⚡ Command-Line Interface & Fast Iterations

The runner script supports command-line arguments to speed up code iteration.

### Run All Benchmarks:
To run the full suite (including all random and clustered scales):
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
*   **Clustered-Only (18, 30, and 50 Cities)**:
    ```bash
    python main.py --clustered-only
    ```
    or `python main.py -c`
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
