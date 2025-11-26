const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const conway = require('conway-hart');

const PORT = 3000;

const server = http.createServer((req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'GET' && req.url === '/') {
        // Serve the HTML file
        fs.readFile(path.join(__dirname, '../public/index.html'), (err, data) => {
            if (err) {
                res.writeHead(500);
                res.end('Error loading index.html');
                return;
            }
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(data);
        });
    } else if (req.method === 'POST' && req.url === '/generate') {
        // Handle polyhedron generation
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            try {
                const { notation } = JSON.parse(body);
                const result = conway(notation);

                // Format the response
                const polyhedron = {
                    name: result.name,
                    vertices: result.positions,
                    faces: result.cells
                };

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(polyhedron));
            } catch (error) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: error.message }));
            }
        });
    } else if (req.method === 'POST' && req.url === '/export') {
        // Handle Skybrush export
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            try {
                const { vertices, filename } = JSON.parse(body);
                const outputFile = filename || 'vertices_show.skyc';
                const outputPath = path.join(__dirname, '../output', outputFile);

                // Convert vertices to JSON string for command line
                const verticesJson = JSON.stringify(vertices);

                // Call Python export script
                const pythonScript = path.join(__dirname, 'python/export_vertices.py');
                const pythonCmd = `python3 "${pythonScript}" '${verticesJson}' '${outputPath}'`;

                exec(pythonCmd, { cwd: path.join(__dirname, '..') }, (error, stdout, stderr) => {
                    if (error) {
                        console.error('Export error:', stderr);
                        res.writeHead(500, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: `Export failed: ${stderr}` }));
                        return;
                    }

                    console.log('Export output:', stdout);

                    // Return success with filename
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        filename: outputPath,
                        message: `Exported ${vertices.length} vertices to output/${outputFile}`
                    }));
                });
            } catch (error) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: error.message }));
            }
        });
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
    console.log('Open your browser and navigate to the URL above');
});
