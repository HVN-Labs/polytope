#!/usr/bin/env python3
"""
Skybrush Export Module V2
=========================
Export vertices to Skybrush .skyc format matching the qq.skyc structure.
"""

import numpy as np
import json
import zipfile
import os
from typing import List, Dict, Any


def create_stationary_trajectory_skybrush(position: np.ndarray, n_frames: int = 100,
                                          fps: float = 4.0) -> Dict[str, Any]:
    """
    Create a Skybrush trajectory for a stationary drone (hovering at one position).

    Args:
        position: 3D position [x, y, z]
        n_frames: Number of trajectory points
        fps: Frames per second

    Returns:
        Skybrush trajectory dictionary with Bezier control points
    """
    # Calculate time interval between frames
    dt = 1.0 / fps

    points = []
    for i in range(n_frames):
        time = i * dt
        pos = position.tolist()

        # For stationary trajectory, control point is the same as position
        # This creates a straight line (no curve) to the next point
        # Format: [[control_point_x, control_point_y, control_point_z]]
        points.append([time, pos, [pos]])

    return {
        "version": 1,
        "points": points
    }


def create_lights_data() -> Dict[str, Any]:
    """
    Create default lights configuration (white color, always on).

    Returns:
        Lights configuration dictionary
    """
    # Encode as base64-like data (the example uses "B4wlAAwK////" which represents white color)
    return {
        "version": 1,
        "data": "B4wlAAwK////"  # Default white lights
    }


def create_show_metadata(n_drones: int, duration: float, fps: float,
                         title: str = "Polyhedron Vertices") -> Dict[str, Any]:
    """
    Create show.json metadata with references to drone trajectory files.

    Args:
        n_drones: Number of drones
        duration: Show duration in seconds
        fps: Frames per second
        title: Show title

    Returns:
        Show metadata dictionary
    """
    # Create drone configurations
    drones = []
    for i in range(1, n_drones + 1):
        drone_config = {
            "type": "generic",
            "settings": {
                "trajectory": {
                    "$ref": f"./drones/Drone {i}/trajectory.json#"
                },
                "lights": {
                    "$ref": f"./drones/Drone {i}/lights.json#"
                },
                "home": [0.0, 0.0, 0.0],  # Will be set to actual vertex position
                "landAt": [0.0, 0.0, 0.0],
                "name": f"Drone {i}"
            }
        }
        drones.append(drone_config)

    show_data = {
        "version": 1,
        "settings": {
            "cues": {
                "$ref": "./cues.json"
            },
            "validation": {
                "maxAccelerationXY": 4.0,
                "maxAccelerationZ": 4.0,
                "maxAltitude": 150.0,
                "maxVelocityXY": 10.0,
                "maxVelocityZ": 2.0,
                "minDistance": 3.0,
                "minNavAltitude": 2.5
            }
        },
        "swarm": {
            "drones": drones
        },
        "environment": {
            "type": "outdoor"
        },
        "meta": {
            "title": title,
            "segments": {
                "takeoff": [0.0, 0.0],
                "show": [0.0, duration],
                "landing": [duration, duration]
            }
        },
        "media": {}
    }

    return show_data


def create_cues_data(duration: float, title: str = "Polyhedron Vertices") -> Dict[str, Any]:
    """
    Create cues.json with show timing markers.

    Args:
        duration: Show duration in seconds
        title: Show title

    Returns:
        Cues configuration dictionary
    """
    return {
        "version": 1,
        "items": [
            {"time": 0.0, "name": f"at {title}"},
            {"time": duration, "name": f"{title} ends"}
        ]
    }


def export_vertices_to_skybrush(vertices: np.ndarray, output_file: str = "vertices_show.skyc",
                                 n_frames: int = 100, fps: float = 4.0,
                                 show_title: str = "Polyhedron Vertices") -> bool:
    """
    Export vertices to Skybrush .skyc format with proper directory structure.

    Args:
        vertices: Array of vertex positions (n_vertices, 3)
        output_file: Output .skyc filename
        n_frames: Number of trajectory frames (default 100)
        fps: Frames per second (default 4)
        show_title: Show title

    Returns:
        True if successful, False otherwise
    """
    try:
        n_vertices = len(vertices)
        duration = (n_frames - 1) / fps

        print(f"\n[Skybrush Export V2] Creating .skyc file...")
        print(f"  Vertices: {n_vertices}")
        print(f"  Frames: {n_frames}")
        print(f"  FPS: {fps}")
        print(f"  Duration: {duration:.2f}s")

        # Create ZIP archive
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Create show.json
            show_data = create_show_metadata(n_vertices, duration, fps, show_title)

            # Update home/landAt positions for each drone
            for i, vertex in enumerate(vertices):
                drone_idx = i
                show_data["swarm"]["drones"][drone_idx]["settings"]["home"] = vertex.tolist()
                show_data["swarm"]["drones"][drone_idx]["settings"]["landAt"] = vertex.tolist()

            zf.writestr('show.json', json.dumps(show_data, indent=2))
            print(f"  ✓ Created show.json")

            # 2. Create cues.json
            cues_data = create_cues_data(duration, show_title)
            zf.writestr('cues.json', json.dumps(cues_data, indent=2))
            print(f"  ✓ Created cues.json")

            # 3. Create trajectory and lights for each drone
            for i, vertex in enumerate(vertices):
                drone_name = f"Drone {i + 1}"

                # Create trajectory
                trajectory_data = create_stationary_trajectory_skybrush(vertex, n_frames, fps)
                trajectory_path = f"drones/{drone_name}/trajectory.json"
                zf.writestr(trajectory_path, json.dumps(trajectory_data, indent=2))

                # Create lights
                lights_data = create_lights_data()
                lights_path = f"drones/{drone_name}/lights.json"
                zf.writestr(lights_path, json.dumps(lights_data, indent=2))

                if (i + 1) % 10 == 0 or (i + 1) == n_vertices:
                    print(f"  ✓ Created files for {i + 1}/{n_vertices} drones")

        file_size = os.path.getsize(output_file) / 1024
        print(f"\n✓ Successfully created {output_file}")
        print(f"  File size: {file_size:.1f} KB")
        print(f"  Total drones: {n_vertices}")
        print(f"  Trajectory duration: {duration:.2f}s")

        return True

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test with sample vertices
    test_vertices = np.array([
        [0, 0, 30],
        [10, 0, 30],
        [5, 8.66, 30]
    ])

    export_vertices_to_skybrush(test_vertices, "test_vertices.skyc")
