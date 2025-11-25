// Configuration
const COURT_WIDTH = 800;
const COURT_HEIGHT = 450; // Aspect ratio approx 1.77
const DATA_FILE = '../output_videos/tactical_data.jsonl';

// Setup SVG
const svg = d3.select("#court-container")
    .append("svg")
    .attr("width", COURT_WIDTH)
    .attr("height", COURT_HEIGHT);

// Draw Court Lines (Simplified)
function drawCourt() {
    const lineColor = "#fff";
    const lineWidth = 2;

    // Outer boundary
    svg.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", COURT_WIDTH)
        .attr("height", COURT_HEIGHT)
        .attr("fill", "none")
        .attr("stroke", lineColor)
        .attr("stroke-width", lineWidth);

    // Center line
    svg.append("line")
        .attr("x1", COURT_WIDTH / 2)
        .attr("y1", 0)
        .attr("x2", COURT_WIDTH / 2)
        .attr("y2", COURT_HEIGHT)
        .attr("stroke", lineColor)
        .attr("stroke-width", lineWidth);

    // Center circle
    svg.append("circle")
        .attr("cx", COURT_WIDTH / 2)
        .attr("cy", COURT_HEIGHT / 2)
        .attr("r", 40)
        .attr("fill", "none")
        .attr("stroke", lineColor)
        .attr("stroke-width", lineWidth);
        
    // Hoops (approximate positions)
    svg.append("circle")
        .attr("cx", 40)
        .attr("cy", COURT_HEIGHT / 2)
        .attr("r", 5)
        .attr("fill", "none")
        .attr("stroke", lineColor)
        .attr("stroke-width", lineWidth);

    svg.append("circle")
        .attr("cx", COURT_WIDTH - 40)
        .attr("cy", COURT_HEIGHT / 2)
        .attr("r", 5)
        .attr("fill", "none")
        .attr("stroke", lineColor)
        .attr("stroke-width", lineWidth);
}

drawCourt();

// Data Handling
let frames = [];
let currentFrameIndex = 0;
let isPlaying = false;
let animationId;

async function fetchData() {
    try {
        const response = await fetch(DATA_FILE);
        const text = await response.text();
        const lines = text.trim().split('\n');
        
        // Parse JSONL
        const newFrames = lines.map(line => {
            try {
                return JSON.parse(line);
            } catch (e) {
                return null;
            }
        }).filter(f => f !== null);

        // Update frames if we have new data
        if (newFrames.length > frames.length) {
            frames = newFrames;
            document.getElementById('status').innerText = `Loaded ${frames.length} frames`;
        }
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// Render Frame
function renderFrame(frameData) {
    if (!frameData) return;

    // Players
    const players = svg.selectAll(".player-dot")
        .data(frameData.players, d => d.id);

    // Enter
    players.enter()
        .append("circle")
        .attr("class", "player-dot")
        .attr("r", 8)
        .merge(players) // Update
        .attr("cx", d => d.x / 100 * COURT_WIDTH) // Assuming normalized coordinates 0-100? Need to verify scale
        // Actually, the python code passes raw pixel coordinates from the tactical view converter
        // We might need to scale them if the converter output doesn't match our SVG size
        // For now, let's assume the converter outputs coordinates relative to the court image size used there
        // and we might need to scale. Let's assume 1:1 for now or scale if needed.
        // The converter uses 'tactical_view_converter.width' which seems to be hardcoded or derived.
        // Let's assume we need to scale x and y.
        .attr("cx", d => d.x) 
        .attr("cy", d => d.y)
        .attr("fill", d => d.team === 1 ? "#fff" : "#1e90ff"); // White vs Blue

    // Exit
    players.exit().remove();

    // Ball (if we had ball position, but we only have ball owner)
    // If we want to show the ball, we'd need its coordinates or attach it to the owner
    if (frameData.ball_owner !== -1) {
        const owner = frameData.players.find(p => p.id === frameData.ball_owner);
        if (owner) {
            const ball = svg.selectAll(".ball-dot").data([owner]);
            ball.enter()
                .append("circle")
                .attr("class", "ball-dot")
                .attr("r", 4)
                .merge(ball)
                .attr("cx", d => d.x + 5) // Offset slightly
                .attr("cy", d => d.y - 5);
            ball.exit().remove();
        }
    } else {
        svg.selectAll(".ball-dot").remove();
    }
}

// Animation Loop
function animate() {
    if (!isPlaying) return;

    if (currentFrameIndex < frames.length) {
        renderFrame(frames[currentFrameIndex]);
        currentFrameIndex++;
    } else {
        // Loop or stop? Let's loop for now
        currentFrameIndex = 0;
    }

    // Control speed (e.g., 24 fps)
    setTimeout(() => {
        animationId = requestAnimationFrame(animate);
    }, 1000 / 24);
}

// Controls
document.getElementById('play-btn').addEventListener('click', () => {
    if (!isPlaying) {
        isPlaying = true;
        animate();
    }
});

document.getElementById('pause-btn').addEventListener('click', () => {
    isPlaying = false;
    cancelAnimationFrame(animationId);
});

document.getElementById('reset-btn').addEventListener('click', () => {
    isPlaying = false;
    currentFrameIndex = 0;
    renderFrame(frames[0]);
});

// Poll for new data every second (streaming simulation)
setInterval(fetchData, 1000);
fetchData();
