#!/usr/bin/env python3
"""
OBJ Face Removal Tool
Removes specified faces (polygons) from .obj files
"""

import sys
import argparse
import numpy as np


class OBJMesh:
    """Class to handle OBJ file operations"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.vertices = []
        self.faces = []
        self.other_lines = []  # Store comments, normals, textures, etc.
        self.load()

    def load(self):
        """Load OBJ file"""
        try:
            with open(self.filepath, 'r') as f:
                for line in f:
                    line = line.strip()

                    if not line or line.startswith('#'):
                        self.other_lines.append(line)
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    if parts[0] == 'v':
                        # Vertex
                        if len(parts) >= 4:
                            self.vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                            self.other_lines.append(None)  # Placeholder
                    elif parts[0] == 'f':
                        # Face - extract vertex indices
                        face_indices = []
                        for vertex_ref in parts[1:]:
                            # Handle v, v/vt, v/vt/vn, v//vn formats
                            idx = vertex_ref.split('/')[0]
                            face_indices.append(int(idx))
                        self.faces.append(face_indices)
                        self.other_lines.append(None)  # Placeholder
                    else:
                        self.other_lines.append(line)

            print(f"Loaded: {len(self.vertices)} vertices, {len(self.faces)} faces")

        except FileNotFoundError:
            print(f"Error: File '{self.filepath}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)

    def remove_faces(self, face_indices):
        """Remove faces by their indices"""
        face_indices = sorted(set(face_indices), reverse=True)
        removed_count = 0

        for idx in face_indices:
            if 0 <= idx < len(self.faces):
                del self.faces[idx]
                removed_count += 1
            else:
                print(f"Warning: Face index {idx} out of range (0-{len(self.faces)-1})")

        print(f"Removed {removed_count} faces")
        print(f"Remaining: {len(self.faces)} faces")
        return removed_count

    def remove_faces_by_criteria(self, criteria_func):
        """Remove faces based on a criteria function"""
        faces_to_remove = []

        for i, face in enumerate(self.faces):
            if criteria_func(i, face, self.vertices):
                faces_to_remove.append(i)

        if faces_to_remove:
            print(f"Found {len(faces_to_remove)} faces matching criteria")
            return self.remove_faces(faces_to_remove)
        else:
            print("No faces match the criteria")
            return 0

    def remove_unused_vertices(self):
        """Remove vertices that are not referenced by any face"""
        # Find which vertices are used
        used_vertices = set()
        for face in self.faces:
            for v_idx in face:
                used_vertices.add(v_idx - 1)  # OBJ indices start at 1

        # Create mapping from old to new indices
        old_to_new = {}
        new_vertices = []
        new_idx = 1  # OBJ indices start at 1

        for old_idx in range(len(self.vertices)):
            if old_idx in used_vertices:
                old_to_new[old_idx + 1] = new_idx
                new_vertices.append(self.vertices[old_idx])
                new_idx += 1

        # Update face indices
        new_faces = []
        for face in self.faces:
            new_face = [old_to_new[v_idx] for v_idx in face]
            new_faces.append(new_face)

        removed = len(self.vertices) - len(new_vertices)
        self.vertices = new_vertices
        self.faces = new_faces

        if removed > 0:
            print(f"Removed {removed} unused vertices")

        return removed

    def save(self, output_path):
        """Save the modified mesh to a new OBJ file"""
        try:
            with open(output_path, 'w') as f:
                # Write header
                f.write("# Modified OBJ file\n")
                f.write(f"# Original: {self.filepath}\n")
                f.write(f"# Vertices: {len(self.vertices)}\n")
                f.write(f"# Faces: {len(self.faces)}\n\n")

                # Write vertices
                for v in self.vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

                f.write("\n")

                # Write faces
                for face in self.faces:
                    f.write("f " + " ".join(str(idx) for idx in face) + "\n")

            print(f"\nSaved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def print_info(self):
        """Print mesh information"""
        print("\n" + "="*60)
        print("MESH INFORMATION")
        print("="*60)
        print(f"File: {self.filepath}")
        print(f"Vertices: {len(self.vertices)}")
        print(f"Faces: {len(self.faces)}")

        if self.faces:
            face_sizes = [len(face) for face in self.faces]
            print(f"\nFace statistics:")
            print(f"  Min vertices per face: {min(face_sizes)}")
            print(f"  Max vertices per face: {max(face_sizes)}")
            print(f"  Average vertices per face: {np.mean(face_sizes):.2f}")

            # Count triangles, quads, etc.
            from collections import Counter
            size_counts = Counter(face_sizes)
            print(f"\nFace types:")
            for size in sorted(size_counts.keys()):
                name = {3: "triangles", 4: "quads", 5: "pentagons", 6: "hexagons"}.get(size, f"{size}-gons")
                print(f"  {name}: {size_counts[size]}")

        print("="*60 + "\n")

    def list_faces(self, limit=20):
        """List faces with their vertex indices"""
        print("\nFace list:")
        print("-"*60)
        for i, face in enumerate(self.faces[:limit]):
            vertex_str = ", ".join(str(idx) for idx in face)
            print(f"  Face {i}: [{vertex_str}]")

        if len(self.faces) > limit:
            print(f"  ... and {len(self.faces) - limit} more faces")
        print()


def parse_index_list(index_str):
    """Parse index string like '0,1,2' or '0-5,7,9-11' into list of indices"""
    indices = []
    parts = index_str.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            # Range
            start, end = part.split('-')
            indices.extend(range(int(start), int(end) + 1))
        else:
            # Single index
            indices.append(int(part))

    return indices


def main():
    parser = argparse.ArgumentParser(
        description='Remove faces (polygons) from OBJ mesh files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove faces by index
  python remove_faces.py model.obj -r 0,1,2 -o output.obj

  # Remove face range
  python remove_faces.py model.obj -r 0-10,15,20-25 -o output.obj

  # Remove triangles (3-sided faces)
  python remove_faces.py model.obj --triangles -o output.obj

  # Remove quads (4-sided faces)
  python remove_faces.py model.obj --quads -o output.obj

  # Remove faces with more than N vertices
  python remove_faces.py model.obj --max-vertices 4 -o output.obj

  # Just inspect the mesh
  python remove_faces.py model.obj --info

  # List all faces
  python remove_faces.py model.obj --list-faces
        """
    )

    parser.add_argument('input', help='Input OBJ file')
    parser.add_argument('-o', '--output', help='Output OBJ file')
    parser.add_argument('-r', '--remove', help='Face indices to remove (e.g., "0,1,2" or "0-5,7")')
    parser.add_argument('--triangles', action='store_true', help='Remove all triangular faces')
    parser.add_argument('--quads', action='store_true', help='Remove all quad faces')
    parser.add_argument('--min-vertices', type=int, help='Remove faces with fewer than N vertices')
    parser.add_argument('--max-vertices', type=int, help='Remove faces with more than N vertices')
    parser.add_argument('--clean-vertices', action='store_true', help='Remove unused vertices')
    parser.add_argument('--info', action='store_true', help='Show mesh information only')
    parser.add_argument('--list-faces', action='store_true', help='List all faces')

    args = parser.parse_args()

    # Load mesh
    mesh = OBJMesh(args.input)
    mesh.print_info()

    if args.list_faces:
        mesh.list_faces(limit=100)

    if args.info:
        return

    # Track if any modifications were made
    modified = False

    # Remove specific faces
    if args.remove:
        indices = parse_index_list(args.remove)
        print(f"\nRemoving {len(indices)} specified faces...")
        mesh.remove_faces(indices)
        modified = True

    # Remove by criteria
    if args.triangles:
        print("\nRemoving triangular faces...")
        mesh.remove_faces_by_criteria(lambda i, f, v: len(f) == 3)
        modified = True

    if args.quads:
        print("\nRemoving quad faces...")
        mesh.remove_faces_by_criteria(lambda i, f, v: len(f) == 4)
        modified = True

    if args.min_vertices:
        print(f"\nRemoving faces with fewer than {args.min_vertices} vertices...")
        mesh.remove_faces_by_criteria(lambda i, f, v: len(f) < args.min_vertices)
        modified = True

    if args.max_vertices:
        print(f"\nRemoving faces with more than {args.max_vertices} vertices...")
        mesh.remove_faces_by_criteria(lambda i, f, v: len(f) > args.max_vertices)
        modified = True

    # Clean up unused vertices
    if args.clean_vertices:
        print("\nCleaning unused vertices...")
        mesh.remove_unused_vertices()
        modified = True

    # Save if modified and output specified
    if modified:
        if args.output:
            mesh.save(args.output)
            print(f"\nSuccess! Modified mesh saved to: {args.output}")
        else:
            print("\nWarning: Faces were removed but no output file specified (use -o)")
            print("Use --info to see the changes without saving")
    elif not args.info and not args.list_faces:
        print("\nNo modifications specified. Use --help to see available options.")


if __name__ == "__main__":
    main()
