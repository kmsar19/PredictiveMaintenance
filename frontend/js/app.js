const API_URL = "https://predictive-maintenance-api-fxbb.onrender.com";
const THRESHOLD = 0.40;

let predictionCount = 0;
const history = [];

function updateClock() {
    const now = new Date();
    document.getElementById("dateTime").textContent =
        now.toLocaleDateString() + " " + now.toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

async function checkAPI() {
    const status = document.getElementById("cloudStatus");
    try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) throw new Error("Unavailable");
        status.textContent = "? API Connected";
        status.style.color = "#15966b";
    } catch {
        status.textContent = "? API Disconnected";
        status.style.color = "#dc4444";
    }
}
checkAPI();
setInterval(checkAPI, 10000);


// Sensor chart: illustrative simulated values, not actual dataset sensors.
const labels = Array.from({length: 12}, (_, i) => `${i * 2}:00`);

const sensorChart = new Chart(document.getElementById("sensorChart"), {
    type: "line",
    data: {
        labels,
        datasets: [
            {
                label: "Temperature (K)",
                data: [298, 298.3, 298.2, 298.6, 298.4, 298.8, 299, 298.7, 299.1, 299, 299.2, 299.3],
                borderColor: "#3287e8",
                tension: 0.35,
                pointRadius: 1
            },
            {
                label: "Vibration (simulated)",
                data: [30, 31, 30, 33, 32, 34, 32, 35, 34, 36, 35, 37],
                borderColor: "#f59e0b",
                tension: 0.35,
                pointRadius: 1
            },
            {
                label: "Current (simulated)",
                data: [20, 21, 20, 21, 22, 21, 23, 22, 23, 24, 23, 24],
                borderColor: "#159b70",
                tension: 0.35,
                pointRadius: 1
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { position: "bottom", labels: {boxWidth: 8, font: {size: 9}} } },
        scales: { x: { ticks: {font: {size: 8}} }, y: { ticks: {font: {size: 8}} } }
    }
});


// Model metrics: measured on the held-out test set.
new Chart(document.getElementById("performanceChart"), {
    type: "bar",
    data: {
        labels: ["Accuracy", "Precision", "Recall", "F1-score"],
        datasets: [{
            data: [96.6, 50.0, 88.2, 63.8],
            backgroundColor: ["#3985ec", "#159b70", "#f59e0b", "#7164db"],
            borderRadius: 5
        }]
    },
    options: {
        responsive: true,
        plugins: {legend: {display: false}},
        scales: {
            y: {beginAtZero: true, max: 100, ticks: {font: {size: 9}}},
            x: {ticks: {font: {size: 9}}}
        }
    }
});


function showResult(result) {
    const failure = result.failure_prediction === 1;
    const probability = result.failure_probability;
    const noFailureProbability = Math.max(0, 100 - probability);

    const heading = document.getElementById("conditionText");
    const conditionPanel = document.querySelector(".condition-heading");

    heading.textContent = failure ? "Failure Risk" : "Normal Operation";
    conditionPanel.classList.toggle("failure", failure);

    document.getElementById("conditionIcon").textContent = failure ? "!" : "?";
    document.getElementById("confidenceText").textContent =
        `Failure probability: ${probability.toFixed(2)}%`;

    document.getElementById("predictionValue").textContent =
        failure ? "Failure (1)" : "Normal (0)";

    document.getElementById("predictionTime").textContent =
        new Date().toLocaleString();

    document.getElementById("healthValue").textContent =
        `${noFailureProbability.toFixed(2)}%`;

    document.getElementById("gauge").style.background =
        `conic-gradient(#159b70 0% ${noFailureProbability}%, #dc4444 ${noFailureProbability}% 100%)`;
}


function addHistory(machine, result) {
    predictionCount++;

    const time = new Date().toLocaleTimeString();

    history.unshift({
        time,
        machine: machine.machine_type,
        condition: result.machine_status,
        probability: result.failure_probability
    });

    const body = document.getElementById("historyBody");
    body.innerHTML = "";

    history.slice(0, 8).forEach(item => {
        const row = document.createElement("tr");

        const values = [
            item.time,
            item.machine,
            item.condition,
            `${item.probability.toFixed(2)}%`
        ];

        values.forEach((value, index) => {
            const cell = document.createElement("td");

            if (index === 2) {
                const badge = document.createElement("span");
                badge.className = item.condition === "Failure Risk" ? "badge failure" : "badge";
                badge.textContent = value;
                cell.appendChild(badge);
            } else {
                cell.textContent = value;
            }

            row.appendChild(cell);
        });

        body.appendChild(row);
    });
}


document.getElementById("predictionForm").addEventListener("submit", async event => {
    event.preventDefault();

    const button = document.getElementById("predictButton");
    button.disabled = true;
    button.textContent = "Analyzing...";

    const machine = {
        machine_type: document.getElementById("machineType").value,
        air_temperature: Number(document.getElementById("airTemperature").value),
        process_temperature: Number(document.getElementById("processTemperature").value),
        rotational_speed: Number(document.getElementById("rotationalSpeed").value),
        torque: Number(document.getElementById("torque").value),
        tool_wear: Number(document.getElementById("toolWear").value)
    };

    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(machine)
        });

        if (!response.ok) {
            const detail = await response.text();
            throw new Error(detail);
        }

        const result = await response.json();

        showResult(result);
        addHistory(machine, result);

    } catch (error) {
        alert("Prediction error: " + error.message);
    } finally {
        button.disabled = false;
        button.textContent = "? Predict";
    }
});

document.getElementById("predictionForm").addEventListener("reset", () => {
    setTimeout(() => {
        document.getElementById("conditionText").textContent = "Awaiting Prediction";
        document.getElementById("confidenceText").textContent = "Enter machine parameters";
    }, 0);
});

document.querySelectorAll(".sidebar nav a").forEach(link => {
    link.addEventListener("click", () => {
        document.querySelectorAll(".sidebar nav a").forEach(item => item.classList.remove("active"));
        link.classList.add("active");
    });
});

// ==========================================
// SQLITE DATABASE HISTORY INTEGRATION
// ==========================================

async function loadDatabaseHistory() {
    try {
        const response = await fetch(`${API_URL}/predictions?limit=100`);

        if (!response.ok) {
            throw new Error("Unable to load prediction history");
        }

        const records = await response.json();

        const body = document.getElementById("historyBody");
        body.innerHTML = "";

        predictionCount = records.length;

        if (records.length === 0) {
            body.innerHTML =
                '<tr><td colspan="4">No predictions yet</td></tr>';
            return;
        }

        records.forEach(record => {
            const row = document.createElement("tr");

            const date = new Date(record.timestamp).toLocaleString();

            const values = [
                date,
                record.machine_type,
                record.machine_status,
                Number(record.failure_probability).toFixed(2) + "%"
            ];

            values.forEach((value, index) => {
                const cell = document.createElement("td");

                if (index === 2) {
                    const badge = document.createElement("span");

                    badge.className =
                        record.prediction === 1
                        ? "badge failure"
                        : "badge";

                    badge.textContent = value;
                    cell.appendChild(badge);
                } else {
                    cell.textContent = value;
                }

                row.appendChild(cell);
            });

            body.appendChild(row);
        });

    } catch (error) {
        console.error("Database history error:", error);
    }
}


// Replace temporary history handling with database history
async function addHistory(machine, result) {
    await loadDatabaseHistory();
}


// Load saved history whenever the dashboard opens
loadDatabaseHistory();


// ==========================================
// LOAD LIVE DATABASE STATISTICS
// ==========================================

async function loadDatabaseStatistics() {
    try {
        const response = await fetch(`${API_URL}/statistics`);

        if (!response.ok) {
            throw new Error("Statistics unavailable");
        }

        const stats = await response.json();

        const total = document.getElementById("totalPredictions");
        if (total) {
            total.textContent = stats.total_predictions;
        }

        const status = document.getElementById("cloudStatus");
        if (status) {
            status.textContent = "? Database Connected";
        }

    } catch (error) {
        console.error("Statistics error:", error);
    }
}


// Refresh statistics and history
async function refreshDatabaseDashboard() {
    await Promise.all([
        loadDatabaseStatistics(),
        loadDatabaseHistory()
    ]);
}

refreshDatabaseDashboard();
setInterval(refreshDatabaseDashboard, 15000);


// ==========================================
// SIMULATED REAL-TIME MACHINE MONITORING
// ==========================================

const simulatedMachine = {
    temperature: 298.1,
    vibration: 30,
    current: 20
};

let monitoringActive = true;

const monitoringPanel = document.createElement("section");
monitoringPanel.className = "panel";
monitoringPanel.id = "liveMonitoring";

monitoringPanel.innerHTML = `
    <h3>Real-time Machine Monitoring</h3>
    <p class="muted">Simulated sensor readings - no physical sensor connected.</p>

    <div class="metrics">
        <span>
            Air Temperature
            <b id="liveTemperature">298.1 K</b>
        </span>
        <span>
            Vibration
            <b id="liveVibration">30.0 units</b>
        </span>
        <span>
            Current
            <b id="liveCurrent">20.0 units</b>
        </span>
        <span>
            Monitoring Status
            <b id="liveStatus">Normal</b>
        </span>
    </div>

    <div id="liveAlert" style="
        margin-top:15px;
        padding:12px;
        border-radius:6px;
        background:#dcfce7;
        color:#166534;
    ">
        Monitoring active. No simulated warning conditions.
    </div>

    <p class="muted" style="margin-top:12px">
        Last update: <span id="liveUpdateTime">Waiting...</span>
    </p>
`;

const dashboardMain = document.querySelector("main");
const chartPanel = document.querySelector(".lower-grid");

if (dashboardMain && chartPanel && !document.getElementById("liveMonitoring")) {
    dashboardMain.insertBefore(monitoringPanel, chartPanel);
}


// Generate a small simulated sensor change
function simulateSensorReading(current, variation, minimum, maximum) {
    const next = current + (Math.random() - 0.5) * variation;

    return Math.min(maximum, Math.max(minimum, next));
}


// Update the dashboard
function updateLiveMonitoring() {

    if (!monitoringActive) return;

    simulatedMachine.temperature =
        simulateSensorReading(
            simulatedMachine.temperature, 0.8, 295, 305
        );

    simulatedMachine.vibration =
        simulateSensorReading(
            simulatedMachine.vibration, 3, 15, 65
        );

    simulatedMachine.current =
        simulateSensorReading(
            simulatedMachine.current, 2, 10, 40
        );

    document.getElementById("liveTemperature").textContent =
        simulatedMachine.temperature.toFixed(2) + " K";

    document.getElementById("liveVibration").textContent =
        simulatedMachine.vibration.toFixed(2) + " units";

    document.getElementById("liveCurrent").textContent =
        simulatedMachine.current.toFixed(2) + " units";

    document.getElementById("liveUpdateTime").textContent =
        new Date().toLocaleTimeString();


    // Example monitoring thresholds for this simulation only
    const warning =
        simulatedMachine.temperature > 303 ||
        simulatedMachine.vibration > 55 ||
        simulatedMachine.current > 35;

    const status = document.getElementById("liveStatus");
    const alert = document.getElementById("liveAlert");

    if (warning) {
        status.textContent = "Warning";

        alert.style.background = "#fee2e2";
        alert.style.color = "#991b1b";

        alert.textContent =
            "Simulated warning: One or more sensor readings exceeded the configured monitoring limits.";

    } else {
        status.textContent = "Normal";

        alert.style.background = "#dcfce7";
        alert.style.color = "#166534";

        alert.textContent =
            "Monitoring active. No simulated warning conditions.";
    }


    // Update the existing sensor chart
    if (typeof sensorChart !== "undefined") {

        const datasets = sensorChart.data.datasets;

        datasets[0].data.push(
            simulatedMachine.temperature
        );

        datasets[1].data.push(
            simulatedMachine.vibration
        );

        datasets[2].data.push(
            simulatedMachine.current
        );

        sensorChart.data.labels.push(
            new Date().toLocaleTimeString()
        );

        if (sensorChart.data.labels.length > 12) {
            sensorChart.data.labels.shift();

            datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }

        sensorChart.update("none");
    }
}


// Start simulated monitoring
updateLiveMonitoring();

setInterval(updateLiveMonitoring, 3000);


// ==========================================
// PREDICTION MANAGEMENT MODULE
// ==========================================

let predictionRecords = [];


// Add search, filter and export controls
function initializePredictionControls() {

    const panel = document.querySelector(".history-panel");
    if (!panel || document.getElementById("predictionSearch")) return;

    const controls = document.createElement("div");

    controls.style.cssText =
        "display:flex;gap:10px;flex-wrap:wrap;margin-bottom:15px;";

    controls.innerHTML = `
        <input
            id="predictionSearch"
            type="text"
            placeholder="Search machine type..."
            style="flex:1;min-width:140px;"
        >

        <select id="predictionFilter" style="flex:1;min-width:130px;">
            <option value="all">All Predictions</option>
            <option value="failure">Failure Risk</option>
            <option value="normal">Normal</option>
        </select>

        <button id="exportPredictions" type="button">
            Download CSV
        </button>
    `;

    const heading = panel.querySelector("h3");
    heading.insertAdjacentElement("afterend", controls);

    document.getElementById("predictionSearch")
        .addEventListener("input", renderPredictionRecords);

    document.getElementById("predictionFilter")
        .addEventListener("change", renderPredictionRecords);

    document.getElementById("exportPredictions")
        .addEventListener("click", exportPredictionCSV);
}


// Load saved predictions from SQLite
async function loadDatabaseHistory() {

    try {
        const response = await fetch(`${API_URL}/predictions?limit=500`);

        if (!response.ok) {
            throw new Error("Unable to load prediction records");
        }

        predictionRecords = await response.json();

        initializePredictionControls();
        renderPredictionRecords();

    } catch (error) {
        console.error("Prediction history error:", error);
    }
}


// Search and filter predictions
function renderPredictionRecords() {

    const body = document.getElementById("historyBody");
    if (!body) return;

    const search =
        (document.getElementById("predictionSearch")?.value || "")
        .trim().toLowerCase();

    const filter =
        document.getElementById("predictionFilter")?.value || "all";

    const filtered = predictionRecords.filter(record => {

        const machineMatches =
            String(record.machine_type).toLowerCase().includes(search);

        const failure = Number(record.prediction) === 1;

        const statusMatches =
            filter === "all" ||
            (filter === "failure" && failure) ||
            (filter === "normal" && !failure);

        return machineMatches && statusMatches;
    });

    body.innerHTML = "";

    if (filtered.length === 0) {
        body.innerHTML =
            '<tr><td colspan="4">No matching predictions found</td></tr>';
        return;
    }

    filtered.forEach(record => {

        const row = document.createElement("tr");

        const values = [
            new Date(record.timestamp).toLocaleString(),
            record.machine_type,
            record.machine_status,
            Number(record.failure_probability).toFixed(2) + "%"
        ];

        values.forEach((value, index) => {

            const cell = document.createElement("td");

            if (index === 2) {

                const badge = document.createElement("span");

                badge.className =
                    Number(record.prediction) === 1
                    ? "badge failure"
                    : "badge";

                badge.textContent = value;
                cell.appendChild(badge);

            } else {
                cell.textContent = value;
            }

            row.appendChild(cell);
        });

        body.appendChild(row);
    });
}


// Download all loaded database records as CSV
function exportPredictionCSV() {

    if (predictionRecords.length === 0) {
        alert("There are no prediction records to export.");
        return;
    }

    const columns = [
        "id",
        "timestamp",
        "machine_type",
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "prediction",
        "machine_status",
        "failure_probability"
    ];

    const escapeCSV = value =>
        '"' + String(value ?? "").replace(/"/g, '""') + '"';

    const rows = [
        columns.join(","),
        ...predictionRecords.map(record =>
            columns.map(column => escapeCSV(record[column])).join(",")
        )
    ];

    const csv = "\uFEFF" + rows.join("\r\n");

    const file = new Blob([csv], {
        type: "text/csv;charset=utf-8;"
    });

    const url = URL.createObjectURL(file);
    const link = document.createElement("a");

    link.href = url;
    link.download = "predictive_maintenance_predictions.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}


// Initialize prediction management
initializePredictionControls();
loadDatabaseHistory();


// ==========================================
// MODEL PERFORMANCE AND ANALYTICS
// ==========================================

function initializeModelAnalytics() {

    if (document.getElementById("modelAnalytics")) return;

    const section = document.createElement("section");

    section.id = "modelAnalytics";
    section.className = "panel";
    section.style.marginTop = "15px";

    section.innerHTML = `
        <h3>Model Performance and Analytics</h3>
        <p class="muted">
            Random Forest evaluation results on the independent test dataset.
        </p>

        <div class="metrics">
            <span>Accuracy <b>96.60%</b></span>
            <span>Failure Precision <b>50.00%</b></span>
            <span>Failure Recall <b>88.24%</b></span>
            <span>Failure F1-score <b>63.83%</b></span>
            <span>ROC-AUC <b>94.54%</b></span>
            <span>Decision Threshold <b>0.40</b></span>
        </div>

        <div class="analytics-grid">

            <div class="analytics-card">
                <h4>Confusion Matrix</h4>
                <img src="assets/confusion_matrix.png"
                     alt="Random Forest confusion matrix">
            </div>

            <div class="analytics-card">
                <h4>ROC Curve</h4>
                <img src="assets/roc_curve.png"
                     alt="Random Forest ROC curve">
            </div>

            <div class="analytics-card">
                <h4>Feature Importance</h4>
                <img src="assets/feature_importance.png"
                     alt="Random Forest feature importance">
            </div>

            <div class="analytics-card">
                <h4>Prediction Distribution</h4>
                <img src="assets/prediction_distribution.png"
                     alt="Prediction distribution">
            </div>

        </div>

        <p class="muted" style="margin-top:15px;line-height:1.7">
            Note: Metrics are from the saved test evaluation at threshold 0.40.
            Failure precision indicates the proportion of predicted failures
            that were actual failures. These results are not live measurements.
        </p>
    `;

    const style = document.createElement("style");

    style.textContent = `
        .analytics-grid {
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:15px;
            margin-top:18px;
        }

        .analytics-card {
            border:1px solid #e6ebf2;
            border-radius:8px;
            padding:12px;
            min-width:0;
        }

        .analytics-card h4 {
            font-size:12px;
            margin-bottom:12px;
            color:#25344c;
        }

        .analytics-card img {
            width:100%;
            height:auto;
            display:block;
            object-fit:contain;
        }

        @media(max-width:700px) {
            .analytics-grid {
                grid-template-columns:1fr;
            }
        }
    `;

    document.head.appendChild(style);

    const main = document.querySelector("main");

    if (main) {
        main.appendChild(section);
    }
}

initializeModelAnalytics();

