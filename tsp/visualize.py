import os
from typing import List, Tuple
import matplotlib.pyplot as plt
from .test_case import TestCase

class Visualize:
    """
    Handles plotting and animation generation for Traveling Salesman Problem (TSP) runs.
    
    Utilizes matplotlib to produce static figures of problem states and build
    animations illustrating route optimization progression.
    """

    @staticmethod
    def plot_initial_state(test_case: TestCase, save_path: str = None, show: bool = False):
        """
        Generates and saves/displays a plot showing only the cities (nodes) with no connections.
        
        Args:
            test_case (TestCase): The TSP instance containing coordinates.
            save_path (str, optional): Target image filepath. Defaults to None.
            show (bool, optional): Whether to display the plot interactively. Defaults to False.
        """
        plt.figure(figsize=(8, 6))
        xs = [city[0] for city in test_case.cities]
        ys = [city[1] for city in test_case.cities]
        
        plt.scatter(xs, ys, color='red', zorder=5, s=60, edgecolors='black')
        
        # Annotate city indices
        for i, (x, y) in enumerate(test_case.cities):
            plt.annotate(f" {i}", (x, y), fontsize=9, fontweight='bold', alpha=0.8)

        plt.title(f"Initial State - Cities for '{test_case.name}'")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.grid(True, linestyle='--', alpha=0.5)

        if save_path:
            # Create directories if they do not exist
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        plt.close()

    @staticmethod
    def plot_route(test_case: TestCase, route: List[int], title: str, save_path: str = None, show: bool = False):
        """
        Plots a specific route/tour through the cities.

        Args:
            test_case (TestCase): The TSP instance containing coordinates.
            route (List[int]): The ordering sequence of city indices.
            title (str): Title of the plot (e.g. 'Final Route - Genetic Algorithm').
            save_path (str, optional): Target image filepath. Defaults to None.
            show (bool, optional): Whether to display the plot interactively. Defaults to False.
        """
        plt.figure(figsize=(8, 6))
        xs = [city[0] for city in test_case.cities]
        ys = [city[1] for city in test_case.cities]
        
        # Plot cities
        plt.scatter(xs, ys, color='red', zorder=5, s=60, edgecolors='black')
        for i, (x, y) in enumerate(test_case.cities):
            plt.annotate(f" {i}", (x, y), fontsize=9, fontweight='bold', alpha=0.8)

        # Plot route paths
        if route and len(route) == len(test_case.cities):
            route_coords = [test_case.cities[i] for i in route]
            route_coords.append(test_case.cities[route[0]])  # Return to start
            
            rx, ry = zip(*route_coords)
            plt.plot(rx, ry, color='blue', linestyle='-', linewidth=2, zorder=2, label="Route")
            
            # Start/End indicator
            plt.scatter(rx[0], ry[0], color='green', marker='s', s=120, zorder=6, label="Start / End")
            plt.legend()

        total_distance = test_case.get_route_distance(route)
        plt.title(f"{title}\nTotal Distance: {total_distance:.2f}")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.grid(True, linestyle='--', alpha=0.5)

        if save_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        plt.close()

    @staticmethod
    def create_progression(test_case: TestCase, history: List[Tuple[int, float, List[int]]], progression_dir: str, max_frames: int = 100, fps_list: List[int] = None):
        """
        Builds a folder containing frame PNGs for the optimization progression and
        compiles them into several animated GIFs at different speed rates.
        
        Args:
            test_case (TestCase): The TSP instance containing coordinates.
            history (List[Tuple[int, float, List[int]]]): A list of tuples containing (iteration, distance, route).
            progression_dir (str): Folder where PNG frames will be saved and kept.
            max_frames (int, optional): Maximum number of frames to generate. Defaults to 100.
            fps_list (List[int], optional): List of target FPS rates to compile. Defaults to [1, 3, 5, 10, 20].
        """
        if not history:
            print("No history available to create a progression.")
            return

        if fps_list is None:
            fps_list = [1, 3, 5, 10, 20]

        from PIL import Image
        os.makedirs(progression_dir, exist_ok=True)

        # Select a representative set of frames up to max_frames
        if len(history) <= max_frames:
            selected_steps = history
        else:
            step_size = len(history) / max_frames
            selected_steps = [history[int(i * step_size)] for i in range(max_frames)]
            # Ensure the final solution is included
            if history[-1] not in selected_steps:
                selected_steps.append(history[-1])

        print(f"Generating and saving {len(selected_steps)} progression frames to: {progression_dir}")

        frame_paths = []
        # Generate and save frames
        for idx, (iteration, distance, route) in enumerate(selected_steps):
            plt.figure(figsize=(8, 6))
            xs = [city[0] for city in test_case.cities]
            ys = [city[1] for city in test_case.cities]
            
            plt.scatter(xs, ys, color='red', zorder=5, s=60, edgecolors='black')
            for i, (x, y) in enumerate(test_case.cities):
                plt.annotate(f" {i}", (x, y), fontsize=9, alpha=0.8)

            if route:
                route_coords = [test_case.cities[i] for i in route]
                route_coords.append(test_case.cities[route[0]])
                rx, ry = zip(*route_coords)
                plt.plot(rx, ry, color='purple', linestyle='-', linewidth=2, zorder=2)
                plt.scatter(rx[0], ry[0], color='green', marker='s', s=120, zorder=6)

            plt.title(f"Optimization Progress - Step {iteration}\nDistance: {distance:.2f}")
            plt.grid(True, linestyle='--', alpha=0.5)

            frame_path = os.path.join(progression_dir, f"frame_{idx:03d}.png")
            plt.savefig(frame_path, dpi=100)
            plt.close()
            frame_paths.append(frame_path)

        # Load images in Pillow
        images = [Image.open(f) for f in frame_paths]
        if images:
            # Compile multiple GIF versions for each FPS in the list
            for fps in fps_list:
                duration = int(1000 / fps)
                gif_path = os.path.join(progression_dir, f"animation_{fps}fps.gif")
                images[0].save(
                    gif_path,
                    save_all=True,
                    append_images=images[1:],
                    optimize=False,
                    duration=duration,
                    loop=0
                )
                print(f"Animated GIF ({fps} FPS) successfully saved to: {gif_path}")

    @staticmethod
    def create_gif(test_case: TestCase, history: List[Tuple[int, float, List[int]]], save_path: str, fps: int = 2):
        """
        Backwards-compatible wrapper for create_gif. Saves frames to a temporary folder
        and deletes them after compiling the GIF.
        """
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate the progression inside the temp directory
            Visualize.create_progression(
                test_case=test_case,
                history=history,
                progression_dir=tmpdir,
                max_frames=20,
                fps_list=[fps]
            )
            # Copy the single compiled GIF out to save_path
            compiled_gif = os.path.join(tmpdir, f"animation_{fps}fps.gif")
            if os.path.exists(compiled_gif):
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                shutil.copy(compiled_gif, save_path)

