// ==========================================
// CarePulse Hospital System - Analytics JS
// ==========================================

let deptChartInstance = null;

document.addEventListener("DOMContentLoaded", fetchAnalytics);

async function fetchAnalytics() {
    try {
        const res = await fetch("/api/analytics");
        if (!res.ok) {
            throw new Error(`Analytics API returned status ${res.status}`);
        }

        const data = await res.json();
        const metrics = data.metrics || {};
        const departments = data.departments || [];

        // 1. Update Metric Cards Safely
        updateStatElement("statPatients", metrics.total_patients ?? 0);
        updateStatElement("statDoctors", metrics.total_doctors ?? 0);
        updateStatElement("statPrescriptions", metrics.total_prescriptions ?? 0);
        
        const revenue = Number(metrics.total_revenue || 0);
        updateStatElement("statRevenue", `$${revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);

        // 2. Render Departmental Distribution Chart
        renderDepartmentChart(departments);

    } catch (err) {
        console.error("Failed to load hospital analytics:", err);
        displayAnalyticsError();
    }
}

// Safely update DOM element text
function updateStatElement(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerText = value;
}

// Render or destroy/re-render Chart.js Doughnut Chart
function renderDepartmentChart(departments) {
    const canvas = document.getElementById("deptChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Extract labels matching both MySQL (department) and MongoDB (_id) schemas
    const labels = departments.map(d => escapeHtml(d.department || d._id || "General"));
    const chartData = departments.map(d => d.count || 0);

    // Extended color palette to prevent monochrome fallback
    const palette = [
        "#4F46E5", "#10B981", "#F59E0B", "#EF4444",
        "#8B5CF6", "#06B6D4", "#EC4899", "#64748B"
    ];
    const backgroundColors = labels.map((_, i) => palette[i % palette.length]);

    // Destroy existing instance to prevent canvas reuse errors
    if (deptChartInstance) {
        deptChartInstance.destroy();
    }

    deptChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: chartData,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 12,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} Patient(s)`;
                        }
                    }
                }
            }
        }
    });
}

// Fallback UI handler on API failure
function displayAnalyticsError() {
    updateStatElement("statPatients", "--");
    updateStatElement("statDoctors", "--");
    updateStatElement("statPrescriptions", "--");
    updateStatElement("statRevenue", "--");
}

// Security utility to sanitize dynamic labels
function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, m => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }[m]));
}