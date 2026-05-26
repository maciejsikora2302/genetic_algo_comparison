import os
from tsp import (
    TestCase,
    Visualize,
    Comparator,
    BruteForceTSP,
    HeldKarpTSP,
    NearestNeighborTSP,
    TwoOptTSP,
    SimulatedAnnealingTSP,
    GeneticAlgorithmTSP,
    EvolutionaryProgrammingTSP
)

def run_test_case_benchmark(test_case: TestCase, comparator: Comparator, seed: int):
    # Sanitize and create folder structure
    folder_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in test_case.name).strip('_').lower()
    case_dir = os.path.join("outputs", folder_name)
    final_routes_dir = os.path.join(case_dir, "final_routes")
    progressions_base_dir = os.path.join(case_dir, "progressions")

    os.makedirs(case_dir, exist_ok=True)
    os.makedirs(final_routes_dir, exist_ok=True)
    os.makedirs(progressions_base_dir, exist_ok=True)

    print(f"\n====================================================")
    print(f"BENCHMARK: {test_case.name} ({len(test_case.cities)} Cities)")
    print(f"Saving outputs to: {case_dir}")
    print(f"====================================================")

    # 1. Visualize Initial State
    initial_path = os.path.join(case_dir, "initial_state.png")
    Visualize.plot_initial_state(test_case, save_path=initial_path)

    # 2. Run Benchmark Comparison (Automatically skips solvers exceeding their limit)
    comparator.run_comparison(test_case)

    # 3. Generate and Save Benchmarking Charts
    time_chart = os.path.join(case_dir, "execution_time.png")
    convergence_chart = os.path.join(case_dir, "convergence.png")
    ranking_chart = os.path.join(case_dir, "performance_ranking.png")
    
    comparator.plot_time_comparison(save_path=time_chart, use_log=True)
    comparator.plot_convergence(save_path=convergence_chart, use_log_x=True)
    comparator.plot_performance_ranking(save_path=ranking_chart)
    print(f"\nSaved charts for '{test_case.name}':\n - {time_chart}\n - {convergence_chart}\n - {ranking_chart}")

    # 4. Generate Routes and Animations for successfully run solvers
    for algo_name, data in comparator.results.items():
        best_route = data["best_route"]
        algo_filename = algo_name.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_').lower()
        
        # Save final route plot
        route_img_path = os.path.join(final_routes_dir, f"{algo_filename}.png")
        Visualize.plot_route(test_case, best_route, f"Final Route - {algo_name}", save_path=route_img_path)
        
        # Build frame PNG sequence and compile animated GIFs at 5 different speeds
        algo_prog_dir = os.path.join(progressions_base_dir, algo_filename)
        
        Visualize.create_progression(
            test_case=test_case,
            history=data["history"],
            progression_dir=algo_prog_dir,
            max_frames=100,
            fps_list=[1, 3, 5, 10, 20]
        )

    print(f"Done with benchmark: '{test_case.name}'.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TSP Solver Benchmarking Suite")
    parser.add_argument("-m", "--medium-only", action="store_true", help="Run only the Medium 15-City Benchmark for fast iterations")
    parser.add_argument("-l", "--large-only", action="store_true", help="Run only the Large 30-City Benchmark")
    parser.add_argument("-g", "--huge-only", action="store_true", help="Run only the Huge 50-City Benchmark")
    args = parser.parse_args()

    seed = 42
    
    # 1. Define multiple TestCases of various scales
    if args.medium_only:
        test_cases = [
            TestCase.generate_random("Medium 15-City Benchmark", num_cities=15, seed=seed)
        ]
        print("Fast Iteration Mode: Running ONLY the Medium 15-City Benchmark.")
    elif args.large_only:
        test_cases = [
            TestCase.generate_random("Large 30-City Benchmark", num_cities=30, seed=seed)
        ]
        print("Large Scale Mode: Running ONLY the Large 30-City Benchmark.")
    elif args.huge_only:
        test_cases = [
            TestCase.generate_random("Huge 50-City Benchmark", num_cities=50, seed=seed)
        ]
        print("Huge Scale Mode: Running ONLY the Huge 50-City Benchmark.")
    else:
        test_cases = [
            TestCase.generate_random("Small 8-City Benchmark", num_cities=8, seed=seed),
            TestCase.generate_random("Standard 10-City Benchmark", num_cities=10, seed=seed),
            TestCase.generate_random("Medium 15-City Benchmark", num_cities=15, seed=seed),
            TestCase.generate_random("Large 30-City Benchmark", num_cities=30, seed=seed),
            TestCase.generate_random("Huge 50-City Benchmark", num_cities=50, seed=seed)
        ]

    # 2. Instantiate and register the 9 Solver variations
    comparator = Comparator()
    comparator.register_algorithm(BruteForceTSP())
    comparator.register_algorithm(HeldKarpTSP())
    comparator.register_algorithm(NearestNeighborTSP())
    comparator.register_algorithm(TwoOptTSP(init_with_nn=False))
    comparator.register_algorithm(TwoOptTSP(init_with_nn=True))
    comparator.register_algorithm(SimulatedAnnealingTSP(seed=seed, init_with_nn=False))
    comparator.register_algorithm(SimulatedAnnealingTSP(seed=seed, init_with_nn=True))
    comparator.register_algorithm(GeneticAlgorithmTSP(seed=seed))
    comparator.register_algorithm(EvolutionaryProgrammingTSP(seed=seed))

    # 3. Loop and execute benchmark for each TestCase
    for tc in test_cases:
        run_test_case_benchmark(tc, comparator, seed)

    print("\n====================================================")
    print("ALL REQUESTED TSP BENCHMARKS COMPLETED!")
    print("View the results under the respective folders in 'outputs/'.")
    print("====================================================")

if __name__ == "__main__":
    main()
