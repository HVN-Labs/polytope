#!/usr/bin/env python3
"""
Skybrush Export Module V2
=========================
Export vertices to Skybrush .skyc format with animated trajectories.
25 keyframes per second, respecting kinematic constraints.
"""

import numpy as np
import json
import zipfile
import os
import math
from typing import List, Dict, Any


def create_rotation_trajectory(
    start_pos: List[float],
    center: List[float],
    rotation_speed: float,
    duration: float,
    fps: float = 25.0
) -> Dict[str, Any]:
    """
    Create trajectory for a drone rotating around the Z axis.

    Args:
        start_pos: Starting position [x, y, z]
        center: Center of rotation [x, y] (rotation around Z axis)
        rotation_speed: Linear speed in m/s
        duration: Duration in seconds
        fps: Keyframes per second (default 25)

    Returns:
        Trajectory dictionary with keyframes
    """
    # Calculate total keyframes
    n_keyframes = int(duration * fps) + 1
    dt = 1.0 / fps

    # Calculate radius and initial angle
    dx = start_pos[0] - center[0]
    dy = start_pos[1] - center[1]
    radius = math.sqrt(dx * dx + dy * dy)
    initial_angle = math.atan2(dy, dx)
    z = start_pos[2]

    # Angular velocity: omega = v / r (rad/s)
    if radius < 0.001:
        omega = 0.0  # Point at center doesn't move
    else:
        omega = rotation_speed / radius

    # Generate keyframes
    points = []
    for i in range(n_keyframes):
        t = i * dt  # Time in seconds

        # Calculate angle at this time
        angle = initial_angle + omega * t

        # Calculate position
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)

        pos = [round(x, 6), round(y, 6), round(z, 6)]
        points.append([round(t, 4), pos, [pos]])

    return {"version": 1, "points": points}


def create_vertical_scale_trajectory(
    start_pos: List[float],
    scale_start: float,
    scale_end: float,
    shrink_speed: float,
    center_z: float = None,
    fps: float = 25.0
) -> Dict[str, Any]:
    """
    Create trajectory for vertical scaling (Z axis only) from both sides.

    Args:
        start_pos: Starting position [x, y, z]
        scale_start: Starting Z scale factor
        scale_end: Ending Z scale factor
        shrink_speed: Speed of Z change in m/s
        center_z: Center of Z scaling (vertices shrink towards this)
        fps: Keyframes per second (default 25)

    Returns:
        Trajectory dictionary with keyframes
    """
    x = start_pos[0]
    y = start_pos[1]
    original_z = start_pos[2]

    # If no center provided, use the vertex's own Z as reference
    if center_z is None:
        center_z = original_z

    # Calculate offset from center
    z_offset = original_z - center_z

    # Calculate duration based on total Z change and speed
    total_z_change = abs(z_offset) * abs(scale_start - scale_end)
    duration = total_z_change / shrink_speed if shrink_speed > 0 and total_z_change > 0 else 1.0
    duration = max(duration, 0.1)  # Minimum duration

    n_keyframes = int(duration * fps) + 1
    dt = 1.0 / fps

    points = []
    for i in range(n_keyframes):
        t = i * dt
        progress = i / max(n_keyframes - 1, 1)  # 0 to 1

        # Linear interpolation of scale
        scale = scale_start + (scale_end - scale_start) * progress
        # Scale from center - vertices above center move down, below move up
        z = center_z + z_offset * scale

        pos = [round(x, 6), round(y, 6), round(z, 6)]
        points.append([round(t, 4), pos, [pos]])

    return {"version": 1, "points": points}


def create_combined_trajectory(
    start_pos: List[float],
    center: List[float],
    rotation_speed: float,
    scale_start: float,
    scale_end: float,
    duration: float,
    shrink_speed: float = 2.0,
    center_z: float = None,
    fps: float = 25.0
) -> Dict[str, Any]:
    """
    Create trajectory combining rotation and vertical scaling from both sides.

    Args:
        start_pos: Starting position [x, y, z]
        center: Center of rotation [x, y]
        rotation_speed: Linear rotation speed in m/s
        scale_start: Starting Z scale factor
        scale_end: Ending Z scale factor
        duration: Duration in seconds (for rotation)
        shrink_speed: Speed of Z change in m/s
        center_z: Center of Z scaling (vertices shrink towards this)
        fps: Keyframes per second (default 25)

    Returns:
        Trajectory dictionary with keyframes
    """
    original_z = start_pos[2]

    # If no center provided, use the vertex's own Z as reference
    if center_z is None:
        center_z = original_z

    # Calculate offset from center
    z_offset = original_z - center_z

    # Calculate shrink duration based on speed
    total_z_change = abs(z_offset) * abs(scale_start - scale_end)
    shrink_duration = total_z_change / shrink_speed if shrink_speed > 0 and total_z_change > 0 else duration
    shrink_duration = max(shrink_duration, 0.1)

    # Use the longer of the two durations
    actual_duration = max(duration, shrink_duration)
    n_keyframes = int(actual_duration * fps) + 1
    dt = 1.0 / fps

    # Rotation parameters
    dx = start_pos[0] - center[0]
    dy = start_pos[1] - center[1]
    radius = math.sqrt(dx * dx + dy * dy)
    initial_angle = math.atan2(dy, dx)

    omega = rotation_speed / radius if radius > 0.001 else 0.0

    points = []
    for i in range(n_keyframes):
        t = i * dt

        # Rotation (continues for full duration)
        angle = initial_angle + omega * t
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)

        # Vertical scale from center (based on shrink duration)
        shrink_progress = min(t / shrink_duration, 1.0) if shrink_duration > 0 else 1.0
        scale = scale_start + (scale_end - scale_start) * shrink_progress
        z = center_z + z_offset * scale

        pos = [round(x, 6), round(y, 6), round(z, 6)]
        points.append([round(t, 4), pos, [pos]])

    return {"version": 1, "points": points}


def create_stationary_trajectory(
    position: List[float],
    duration: float,
    fps: float = 25.0
) -> Dict[str, Any]:
    """Create trajectory for a stationary drone."""
    n_keyframes = int(duration * fps) + 1
    dt = 1.0 / fps

    pos = [round(position[0], 6), round(position[1], 6), round(position[2], 6)]
    points = [[round(i * dt, 4), pos, [pos]] for i in range(n_keyframes)]

    return {"version": 1, "points": points}


def create_lights_data() -> Dict[str, Any]:
    """Create default lights configuration."""
    return {"version": 1, "data": "B4wlAAwK////"}


def create_show_metadata(n_drones: int, duration: float, title: str) -> Dict[str, Any]:
    """Create show.json metadata."""
    drones = []
    for i in range(1, n_drones + 1):
        drones.append({
            "type": "generic",
            "settings": {
                "trajectory": {"$ref": f"./drones/Drone {i}/trajectory.json#"},
                "lights": {"$ref": f"./drones/Drone {i}/lights.json#"},
                "home": [0.0, 0.0, 0.0],
                "landAt": [0.0, 0.0, 0.0],
                "name": f"Drone {i}"
            }
        })

    return {
        "version": 1,
        "settings": {
            "cues": {"$ref": "./cues.json"},
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
        "swarm": {"drones": drones},
        "environment": {"type": "outdoor"},
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


def create_cues_data(duration: float, title: str) -> Dict[str, Any]:
    """Create cues.json."""
    return {
        "version": 1,
        "items": [
            {"time": 0.0, "name": f"Start {title}"},
            {"time": duration, "name": f"End {title}"}
        ]
    }


def export_vertices_to_skybrush(
    vertices: np.ndarray,
    output_file: str = "vertices_show.skyc",
    n_frames: int = 100,
    fps: float = 25.0,
    show_title: str = "Polyhedron Vertices",
    animation: dict = None
) -> bool:
    """
    Export vertices to Skybrush .skyc format.

    Args:
        vertices: Array of vertex positions (n_vertices, 3)
        output_file: Output .skyc filename
        n_frames: Number of trajectory frames
        fps: Keyframes per second (default 25)
        show_title: Show title
        animation: Animation settings dict

    Returns:
        True if successful
    """
    try:
        n_vertices = len(vertices)

        # Parse animation settings
        enable_rotation = False
        rotation_speed = 4.0
        enable_scale = False
        scale_start = 1.0
        scale_end = 0.1
        shrink_speed = 2.0
        duration = 30.0

        if animation:
            enable_rotation = animation.get('enableRotation', False)
            rotation_speed = float(animation.get('rotationSpeed', 4.0))
            enable_scale = animation.get('enableScale', False)
            scale_start = float(animation.get('scaleStart', 1.0))
            scale_end = float(animation.get('scaleEnd', 0.1))
            shrink_speed = float(animation.get('shrinkSpeed', 2.0))
            duration = float(animation.get('duration', 30.0))
            fps = float(animation.get('fps', 25.0))

        n_keyframes = int(duration * fps) + 1

        print(f"\n{'='*60}")
        print(f"SKYBRUSH EXPORT - Animated Trajectories")
        print(f"{'='*60}")
        print(f"  Drones: {n_vertices}")
        print(f"  Duration: {duration}s")
        print(f"  FPS: {fps} (keyframes/sec)")
        print(f"  Total keyframes per drone: {n_keyframes}")
        print(f"  Rotation: {'YES - ' + str(rotation_speed) + ' m/s' if enable_rotation else 'NO'}")
        print(f"  Vertical Scale: {'YES - ' + str(scale_start) + ' → ' + str(scale_end) + ' at ' + str(shrink_speed) + ' m/s' if enable_scale else 'NO'}")

        # Calculate center for rotation (XY) and scaling (Z)
        center_x = float(np.mean(vertices[:, 0]))
        center_y = float(np.mean(vertices[:, 1]))
        center_z = float(np.mean(vertices[:, 2]))
        center = [center_x, center_y]
        print(f"  Rotation center: ({center_x:.2f}, {center_y:.2f})")
        print(f"  Z scale center: {center_z:.2f}")

        # Create ZIP archive
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Create show.json
            show_data = create_show_metadata(n_vertices, duration, show_title)
            for i, vertex in enumerate(vertices):
                pos = [float(vertex[0]), float(vertex[1]), float(vertex[2])]
                show_data["swarm"]["drones"][i]["settings"]["home"] = pos
                show_data["swarm"]["drones"][i]["settings"]["landAt"] = pos
            zf.writestr('show.json', json.dumps(show_data, indent=2))

            # Create cues.json
            zf.writestr('cues.json', json.dumps(create_cues_data(duration, show_title), indent=2))

            # Create trajectory for each drone
            print(f"\n  Writing trajectories...")
            for i, vertex in enumerate(vertices):
                start_pos = [float(vertex[0]), float(vertex[1]), float(vertex[2])]

                # Choose trajectory type
                if enable_rotation and enable_scale:
                    traj = create_combined_trajectory(
                        start_pos, center, rotation_speed,
                        scale_start, scale_end, duration, shrink_speed, center_z, fps
                    )
                elif enable_rotation:
                    traj = create_rotation_trajectory(
                        start_pos, center, rotation_speed, duration, fps
                    )
                elif enable_scale:
                    traj = create_vertical_scale_trajectory(
                        start_pos, scale_start, scale_end, shrink_speed, center_z, fps
                    )
                else:
                    traj = create_stationary_trajectory(start_pos, duration, fps)

                # Write trajectory
                drone_name = f"Drone {i + 1}"
                zf.writestr(f"drones/{drone_name}/trajectory.json", json.dumps(traj, indent=2))
                zf.writestr(f"drones/{drone_name}/lights.json", json.dumps(create_lights_data(), indent=2))

                # Log first 3 drones' trajectory samples
                if i < 3:
                    pts = traj["points"]
                    print(f"\n    {drone_name} trajectory ({len(pts)} keyframes):")
                    print(f"      t=0.00s: x={pts[0][1][0]:.2f}, y={pts[0][1][1]:.2f}, z={pts[0][1][2]:.2f}")
                    mid = len(pts) // 4
                    print(f"      t={pts[mid][0]:.2f}s: x={pts[mid][1][0]:.2f}, y={pts[mid][1][1]:.2f}, z={pts[mid][1][2]:.2f}")
                    mid2 = len(pts) // 2
                    print(f"      t={pts[mid2][0]:.2f}s: x={pts[mid2][1][0]:.2f}, y={pts[mid2][1][1]:.2f}, z={pts[mid2][1][2]:.2f}")
                    mid3 = 3 * len(pts) // 4
                    print(f"      t={pts[mid3][0]:.2f}s: x={pts[mid3][1][0]:.2f}, y={pts[mid3][1][1]:.2f}, z={pts[mid3][1][2]:.2f}")
                    print(f"      t={pts[-1][0]:.2f}s: x={pts[-1][1][0]:.2f}, y={pts[-1][1][1]:.2f}, z={pts[-1][1][2]:.2f}")

        file_size = os.path.getsize(output_file) / 1024
        print(f"\n{'='*60}")
        print(f"✓ EXPORT COMPLETE: {output_file}")
        print(f"  File size: {file_size:.1f} KB")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test rotation export
    test_vertices = np.array([
        [10, 0, 50],
        [0, 10, 50],
        [-10, 0, 50],
        [0, -10, 50]
    ])

    print("Testing rotation export...")
    export_vertices_to_skybrush(
        test_vertices,
        "test_rotation.skyc",
        animation={
            'enableRotation': True,
            'rotationSpeed': 4.0,
            'enableScale': False,
            'duration': 10,
            'fps': 25
        }
    )

    print("\nTesting shrink export with speed...")
    export_vertices_to_skybrush(
        test_vertices,
        "test_shrink.skyc",
        animation={
            'enableRotation': False,
            'enableScale': True,
            'scaleStart': 1.0,
            'scaleEnd': 0.1,
            'shrinkSpeed': 2.0,
            'fps': 25
        }
    )
