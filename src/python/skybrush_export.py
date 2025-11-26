#!/usr/bin/env python3
"""
Skybrush Export Module
=====================
Export trajectories to Skybrush .skyc format with speed constraints.
"""

import numpy as np
import json
import zipfile
import io
from typing import List, Dict, Any, Tuple
import time


def compute_trajectory_timing(trajectory: np.ndarray, min_speed: float = 2.0,
                              max_speed: float = 6.0, target_speed: float = 4.0) -> Tuple[np.ndarray, float]:
    """
    Compute timestamps for trajectory points respecting speed constraints.

    Args:
        trajectory: Array of shape (n_points, 3) with XYZ coordinates
        min_speed: Minimum allowed speed (m/s)
        max_speed: Maximum allowed speed (m/s)
        target_speed: Preferred cruising speed (m/s)

    Returns:
        timestamps: Array of timestamps (seconds) for each point
        total_duration: Total trajectory duration (seconds)
    """
    n_points = len(trajectory)
    if n_points < 2:
        return np.array([0.0]), 0.0

    # Calculate distances between consecutive points
    distances = np.linalg.norm(np.diff(trajectory, axis=0), axis=1)
    total_distance = np.sum(distances)

    # Calculate time for each segment using target speed
    # But respect min/max speed constraints
    segment_times = []
    for dist in distances:
        if dist < 1e-6:  # Very short segment
            segment_times.append(0.0)
        else:
            # Use target speed, but clamp to valid range
            segment_speed = target_speed
            time_at_target = dist / target_speed

            # Check if this violates speed constraints
            max_time = dist / min_speed  # Slowest allowed
            min_time = dist / max_speed  # Fastest allowed

            segment_time = np.clip(time_at_target, min_time, max_time)
            segment_times.append(segment_time)

    # Build cumulative timestamps
    timestamps = np.zeros(n_points)
    timestamps[1:] = np.cumsum(segment_times)

    total_duration = timestamps[-1]

    return timestamps, total_duration


def resample_trajectory_at_fps(trajectory: np.ndarray, timestamps: np.ndarray,
                               fps: float = 25.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resample trajectory at specified FPS using linear interpolation.

    Args:
        trajectory: Original trajectory points (n_points, 3)
        timestamps: Original timestamps for each point
        fps: Target frames per second

    Returns:
        resampled_trajectory: Trajectory resampled at target FPS
        resampled_timestamps: New timestamps
    """
    if len(trajectory) < 2:
        return trajectory, timestamps

    total_duration = timestamps[-1]
    frame_time = 1.0 / fps

    # Generate new timestamps at FPS intervals
    n_frames = int(np.ceil(total_duration * fps)) + 1
    new_timestamps = np.arange(n_frames) * frame_time

    # Ensure we don't exceed original duration
    new_timestamps = new_timestamps[new_timestamps <= total_duration]

    # Interpolate positions at new timestamps
    resampled_trajectory = np.zeros((len(new_timestamps), 3))
    for dim in range(3):
        resampled_trajectory[:, dim] = np.interp(new_timestamps, timestamps, trajectory[:, dim])

    return resampled_trajectory, new_timestamps


def create_skybrush_trajectory(trajectory: np.ndarray, timestamps: np.ndarray,
                               agent_id: int) -> Dict[str, Any]:
    """
    Create Skybrush trajectory format for a single agent.

    Args:
        trajectory: Resampled trajectory (n_frames, 3)
        timestamps: Timestamps for each frame
        agent_id: Agent identifier (1-indexed)

    Returns:
        Skybrush trajectory dictionary
    """
    points = []
    for t, pos in zip(timestamps, trajectory):
        points.append({
            "t": float(t * 1000),  # Convert to milliseconds
            "x": float(pos[0]),
            "y": float(pos[1]),
            "z": float(pos[2])
        })

    return {
        "id": agent_id,
        "points": points,
        "version": 1
    }


def export_to_skybrush(result: Dict[str, Any], output_file: str = "show.skyc",
                       fps: float = 25.0, min_speed: float = 2.0,
                       max_speed: float = 6.0, target_speed: float = 4.0,
                       show_title: str = "Adaptive Arcs Show") -> bool:
    """
    Export trajectory result to Skybrush .skyc format.

    Args:
        result: Result dictionary from generate_adaptive_collision_free_arcs
        output_file: Output .skyc filename
        fps: Frames per second (default: 25)
        min_speed: Minimum speed constraint (m/s)
        max_speed: Maximum speed constraint (m/s)
        target_speed: Target cruising speed (m/s)
        show_title: Show title in Skybrush

    Returns:
        True if export successful, False otherwise
    """
    try:
        arcs = result['arcs']
        n_agents = len(arcs)
        n_placed = sum(1 for arc in arcs if arc is not None)

        if n_placed == 0:
            print("✗ No agents to export")
            return False

        print(f"\n[Skybrush Export] Processing {n_placed}/{n_agents} agents...")
        print(f"  FPS: {fps}")
        print(f"  Speed range: {min_speed}-{max_speed} m/s (target: {target_speed} m/s)")

        # Process each trajectory
        trajectories = []
        max_duration = 0.0

        for i in range(n_agents):
            if arcs[i] is None:
                continue

            arc = arcs[i]

            # Compute timing based on speed constraints
            timestamps, duration = compute_trajectory_timing(
                arc, min_speed, max_speed, target_speed
            )

            # Resample at target FPS
            resampled_arc, resampled_times = resample_trajectory_at_fps(
                arc, timestamps, fps
            )

            # Create Skybrush trajectory
            traj = create_skybrush_trajectory(resampled_arc, resampled_times, i + 1)
            trajectories.append(traj)

            max_duration = max(max_duration, duration)

            # Compute actual speeds for verification
            distances = np.linalg.norm(np.diff(arc, axis=0), axis=1)
            segment_times = np.diff(timestamps)
            segment_speeds = distances / (segment_times + 1e-10)
            avg_speed = np.mean(segment_speeds)
            min_seg_speed = np.min(segment_speeds)
            max_seg_speed = np.max(segment_speeds)

            print(f"  Agent {i+1}: duration={duration:.2f}s, "
                  f"avg_speed={avg_speed:.2f}m/s, "
                  f"range=[{min_seg_speed:.2f}, {max_seg_speed:.2f}]m/s")

        # Create Skybrush show format
        show_data = {
            "version": 1,
            "title": show_title,
            "description": "Generated by Adaptive Collision-Free Arc Trajectory Generator",
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fps": fps,
            "duration": float(max_duration * 1000),  # milliseconds
            "agents": n_placed,
            "environment": {
                "type": "outdoor",
                "origin": {"lat": 0.0, "lon": 0.0, "amsl": 0.0}
            },
            "swarm": {
                "agents": trajectories
            },
            "settings": {
                "min_speed": min_speed,
                "max_speed": max_speed,
                "target_speed": target_speed
            }
        }

        # Create .skyc file (ZIP archive with show.json)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            show_json = json.dumps(show_data, indent=2)
            zf.writestr('show.json', show_json)

        # Write to file
        with open(output_file, 'wb') as f:
            f.write(buffer.getvalue())

        print(f"\n✓ Skybrush export complete: {output_file}")
        print(f"  Total agents: {n_placed}")
        print(f"  Show duration: {max_duration:.2f}s")
        print(f"  Total frames: {int(max_duration * fps)}")
        print(f"  File size: {len(buffer.getvalue()) / 1024:.1f} KB")

        return True

    except Exception as e:
        print(f"\n✗ Skybrush export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_skybrush_speeds(result: Dict[str, Any], min_speed: float = 2.0,
                             max_speed: float = 6.0) -> Dict[str, Any]:
    """
    Validate that trajectories can respect speed constraints.

    Args:
        result: Result dictionary from generate_adaptive_collision_free_arcs
        min_speed: Minimum speed (m/s)
        max_speed: Maximum speed (m/s)

    Returns:
        Validation report dictionary
    """
    arcs = result['arcs']
    violations = []
    warnings = []

    for i in range(len(arcs)):
        if arcs[i] is None:
            continue

        arc = arcs[i]

        # Compute required speeds if traveling at minimum time (max_speed)
        distances = np.linalg.norm(np.diff(arc, axis=0), axis=1)
        total_distance = np.sum(distances)

        # Check if any segment is too long for max_speed constraint
        min_segment_dist = np.min(distances)
        max_segment_dist = np.max(distances)
        avg_segment_dist = np.mean(distances)

        # Theoretical minimum time (at max_speed)
        min_time = total_distance / max_speed

        # Theoretical maximum time (at min_speed)
        max_time = total_distance / min_speed

        # Check for potential issues
        if max_segment_dist / min_segment_dist > 10:
            warnings.append({
                'agent': i + 1,
                'type': 'uneven_segments',
                'message': f'Segment distances vary greatly ({min_segment_dist:.2f}m - {max_segment_dist:.2f}m)',
                'severity': 'warning'
            })

        # Calculate if trajectory can respect speed constraints
        timestamps, duration = compute_trajectory_timing(arc, min_speed, max_speed)
        segment_times = np.diff(timestamps)
        segment_speeds = distances / (segment_times + 1e-10)

        if np.any(segment_speeds < min_speed - 0.1):  # Small tolerance
            violations.append({
                'agent': i + 1,
                'type': 'speed_too_low',
                'message': f'Some segments below min_speed ({np.min(segment_speeds):.2f} < {min_speed})',
                'severity': 'error'
            })

        if np.any(segment_speeds > max_speed + 0.1):  # Small tolerance
            violations.append({
                'agent': i + 1,
                'type': 'speed_too_high',
                'message': f'Some segments above max_speed ({np.max(segment_speeds):.2f} > {max_speed})',
                'severity': 'error'
            })

    report = {
        'valid': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'summary': {
            'total_agents': len([a for a in arcs if a is not None]),
            'agents_with_violations': len(set(v['agent'] for v in violations)),
            'agents_with_warnings': len(set(w['agent'] for w in warnings))
        }
    }

    return report
