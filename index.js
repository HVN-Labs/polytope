/**
 * Polytope - Conway-Hart polyhedron generator with Skybrush export
 *
 * @module polytope
 */

const conway = require('conway-hart');

/**
 * Generate a polyhedron from Conway notation
 * @param {string} notation - Conway notation string (e.g., 'C', 'jC', 'kD')
 * @returns {Object} Polyhedron with name, vertices (positions), and faces (cells)
 */
function generatePolyhedron(notation) {
    const result = conway(notation);
    return {
        name: result.name,
        vertices: result.positions,
        faces: result.cells
    };
}

module.exports = {
    generatePolyhedron,
    conway
};
