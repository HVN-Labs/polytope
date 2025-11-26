# Conway-Hart Polyhedron Viewer

An interactive 3D viewer for polyhedrons generated using Conway-Hart notation. This application allows you to create complex polyhedrons by entering Conway notation strings and displays their vertices in an interactive 3D visualization.

## Features

- Interactive 3D visualization using Three.js
- Real-time polyhedron generation from Conway notation
- Mouse controls for rotation (drag to rotate, auto-rotation when idle)
- Detailed vertex coordinate display
- Pre-loaded examples for quick exploration
- Modern, responsive UI

## Installation

Dependencies are already installed. If you need to reinstall them:

```bash
npm install
```

## Usage

1. Start the server:

```bash
npm start
```

2. Open your browser and navigate to:

```
http://localhost:3000
```

3. Enter a Conway notation string in the input field and click "Generate" (or press Enter)

## Conway Notation Guide

### Seed Polyhedrons

- `T` - Tetrahedron (4 faces)
- `C` - Cube (6 faces)
- `O` - Octahedron (8 faces)
- `I` - Icosahedron (20 faces)
- `D` - Dodecahedron (12 faces)
- `P[n]` - Prism (e.g., `P5` for pentagonal prism)
- `A[n]` - Antiprism (e.g., `A5` for pentagonal antiprism)
- `Y[n]` - Pyramid (e.g., `Y5` for pentagonal pyramid)

### Operators

- `d` - Dual (swaps vertices and faces)
- `k` - Kis (raises pyramids on each face)
- `a` - Ambo (truncates edges to create new faces)
- `g` - Gyro (rotates faces and adds new faces)
- `p` - Propellor (like gyro but with different proportions)
- `t` - Truncate (cuts off vertices)
- `e` - Explode (separates faces)
- `j` - Join (dual-ambo-dual)
- `s` - Snub (dual-gyro-dual)
- `c` - Canonicalize (adjusts vertices for uniformity)

### Examples

- `T` - Tetrahedron
- `C` - Cube
- `dC` - Dual of cube (Octahedron)
- `kC` - Kis cube (cube with pyramids on each face)
- `aD` - Ambo dodecahedron
- `gtC` - Gyro-truncate cube
- `aaD` - Double ambo dodecahedron
- `dkT` - Dual of kis tetrahedron
- `kkkC` - Triple kis cube

You can chain multiple operators together. The operations are applied from right to left.

## Controls

- **Mouse Drag**: Rotate the polyhedron
- **View Modes**: Toggle between "Vertices Only" and "Full Polyhedron"
- **Remove Polygon**: Click to activate removal mode, then click faces to remove them
- **Export to Skybrush**: Export current vertices to .skyc format
- **Examples**: Click on any example button to load that polyhedron
- **Enter Key**: Press Enter in the input field to generate

## Technical Details

- **Frontend**: HTML5, CSS3, Three.js for 3D rendering
- **Backend**: Node.js HTTP server
- **Polyhedron Generation**: conway-hart library
- **API Endpoint**: POST `/generate` with JSON body `{ "notation": "string" }`

## Project Structure

```
polytope/
├── index.html          # Main HTML interface
├── server.js           # Node.js server
├── package.json        # Dependencies
├── README.md          # This file
└── node_modules/      # Dependencies (including conway-hart)
```

## API

### POST /generate

Generate a polyhedron from Conway notation.

**Request:**
```json
{
  "notation": "kC"
}
```

**Response:**
```json
{
  "name": "kC",
  "vertices": [[x, y, z], ...],
  "faces": [[v1, v2, v3, ...], ...]
}
```

**Error Response:**
```json
{
  "error": "Error message"
}
```

## Skybrush Export

The application can export polyhedron vertices to Skybrush `.skyc` format for drone shows.

### Features

- Exports only vertices that are used by faces (after polygon removal)
- Automatically rescales vertices to fit within bounds while maintaining aspect ratio
- X, Y bounds: (-20, 20) meters
- Z bounds (altitude): (0, 50) meters
- Creates stationary trajectories (drones hover at vertex positions)
- Generates `.skyc` files compatible with Skybrush Studio

### Usage

1. Generate or modify a polyhedron
2. (Optional) Remove unwanted polygons to reduce vertex count
3. Click "Export to Skybrush" button
4. The `.skyc` file will be saved in the project directory

### Export Parameters

- **FPS**: 4 frames per second
- **Frames**: 100 timeframes
- **Duration**: 24.75 seconds (hovering)
- **X, Y Bounds**: (-20, 20) meters
- **Z Bounds (Altitude)**: (0, 50) meters

### File Format

The exported `.skyc` file is a ZIP archive containing:
- `show.json` - Skybrush show definition with agent trajectories
- Metadata including FPS, duration, and agent count

### Example

```bash
# Generate a dodecahedron and export its vertices
1. Navigate to http://localhost:3000
2. Enter "D" in the notation field
3. Click "Generate"
4. Click "Export to Skybrush"
5. File saved as: D_vertices.skyc
```

## License

ISC
