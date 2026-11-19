document.addEventListener("DOMContentLoaded", async () => {
    const res = await fetch("/api/analytics");
    const data = await res.json();

    document.getElementById("statPatients").innerText = data.metrics.total_patients;
    document.getElementById("statDoctors").innerText = data.metrics.total_doctors;
    document.getElementById("statPrescriptions").innerText = data.metrics.total_prescriptions;
    document.getElementById("statRevenue").innerText = "$" + data.metrics.total_revenue;

    // Chart.js - Department Breakdown
    const ctx = document.getElementById("deptChart").getContext("2d");
    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.departments.map(d => d._id || "General"),
            datasets: [{
                data: data.departments.map(d => d.count),
                backgroundColor: ["#4F46E5", "#10B981", "#F59E0B", "#EF4444"]
            }]
        }
    });
});