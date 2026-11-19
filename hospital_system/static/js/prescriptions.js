// ==========================================
// CarePulse Hospital System - Prescriptions JS
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    loadPrescriptions();
    
    const form = document.getElementById("prescriptionForm");
    if (form) {
        form.addEventListener("submit", savePrescription);
    }
});

// Fetch and display all prescriptions from backend
async function loadPrescriptions() {
    const container = document.getElementById("prescriptionsList");
    const countBadge = document.getElementById("rxCount");
    if (!container) return;

    try {
        const res = await fetch("/api/prescriptions");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const prescriptions = await res.json();

        if (countBadge) {
            countBadge.innerText = `${prescriptions.length} Records`;
        }

        if (!prescriptions || prescriptions.length === 0) {
            container.innerHTML = `<p class="text-slate-500 py-6 text-center col-span-2">No prescriptions issued yet.</p>`;
            return;
        }

        container.innerHTML = prescriptions.map(p => {
            const patientName = escapeHtml(p.patient_name || 'Patient');
            const date = escapeHtml(p.date || 'Recent');
            const details = escapeHtml(p.details || 'No instructions specified');

            return `
                <div class="bg-white p-5 rounded-xl shadow border border-slate-200 space-y-3 hover:shadow-md transition">
                    <div class="flex justify-between items-center border-b border-slate-100 pb-2">
                        <h4 class="font-bold text-lg text-indigo-900">Patient: ${patientName}</h4>
                        <span class="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">${date}</span>
                    </div>
                    <div class="text-sm text-slate-700 bg-slate-50 p-3.5 rounded-lg border border-slate-100 font-mono whitespace-pre-line leading-relaxed">
                        ${details}
                    </div>
                </div>
            `;
        }).join("");

    } catch (err) {
        console.error("Failed to load prescriptions:", err);
        container.innerHTML = `<p class="text-rose-500 py-6 text-center col-span-2">Failed to load prescription records.</p>`;
    }
}

// Handle form submission to create a new prescription
async function savePrescription(e) {
    e.preventDefault();

    const patientInput = document.getElementById("rxPatient");
    const doctorInput = document.getElementById("rxDoctor");
    const diagnosisInput = document.getElementById("rxDiagnosis");
    const medicinesInput = document.getElementById("rxMedicines");
    const durationInput = document.getElementById("rxDuration");
    const adviceInput = document.getElementById("rxAdvice");
    const submitBtn = e.target.querySelector('button[type="submit"]');

    const patient_name = patientInput?.value.trim();
    const doctor_name = doctorInput?.value.trim();
    const diagnosis = diagnosisInput?.value.trim();
    const medicines = medicinesInput?.value.trim();
    const duration = durationInput?.value.trim();
    const advice = adviceInput?.value.trim();

    if (!patient_name || !medicines) {
        alert("Please provide both Patient Name and Medicines/Instructions.");
        return;
    }

    // Format all captured prescription fields into structured text
    const detailsParts = [];
    if (doctor_name) detailsParts.push(`Prescribing Doctor: ${doctor_name}`);
    if (diagnosis) detailsParts.push(`Diagnosis: ${diagnosis}`);
    if (medicines) detailsParts.push(`Medicines & Dosage:\n${medicines}`);
    if (duration) detailsParts.push(`Treatment Duration: ${duration}`);
    if (advice) detailsParts.push(`Special Advice & Diet:\n${advice}`);
    const formattedDetails = detailsParts.join("\n\n");

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Saving Prescription...";
    }

    try {
        const res = await fetch("/api/prescriptions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                patient_name: patient_name,
                details: formattedDetails
            })
        });

        if (res.ok) {
            alert("Prescription created and saved successfully!");
            document.getElementById("prescriptionForm").reset();
            loadPrescriptions();
        } else {
            const errorData = await res.json().catch(() => ({}));
            alert(errorData.message || "Failed to save prescription.");
        }
    } catch (err) {
        console.error("Error saving prescription:", err);
        alert("Network error while saving prescription.");
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = "+ Generate & Issue Digital Prescription";
        }
    }
}

// XSS Prevention Security Utility
function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, m => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }[m]));
}
