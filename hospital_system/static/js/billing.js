// ==========================================
// CarePulse Hospital System - Billing JS
// ==========================================

document.addEventListener("DOMContentLoaded", loadBills);

// Fetch and render hospital billing invoices
async function loadBills() {
    const tbody = document.getElementById("billingTableBody");
    if (!tbody) return;

    try {
        const res = await fetch("/api/billing");
        if (!res.ok) throw new Error("Failed to load billing records.");

        const bills = await res.json();

        if (!bills || bills.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-500">No bills found in database.</td></tr>`;
            return;
        }

        tbody.innerHTML = bills.map(b => {
            const billId = b.id || b._id;
            const patientName = escapeHtml(b.patient_name || 'Patient');
            const issueDate = escapeHtml(b.date || 'N/A');
            const amount = Number(b.amount || 0).toFixed(2);
            const status = escapeHtml(b.status || 'Pending');
            const isPaid = status === 'Paid';

            return `
                <tr class="border-b hover:bg-slate-50 transition">
                    <td class="p-4 font-semibold text-slate-800">${patientName}</td>
                    <td class="p-4 text-xs text-slate-500">${issueDate}</td>
                    <td class="p-4 font-mono font-bold text-slate-700">$${amount}</td>
                    <td class="p-4">
                        <span class="px-2.5 py-1 rounded-full text-xs font-bold ${isPaid ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                            ${status}
                        </span>
                    </td>
                    <td class="p-4">
                        ${!isPaid ? 
                            `<button onclick="payBill('${billId}')" class="bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-emerald-700 transition shadow">Pay Now</button>` : 
                            '<span class="text-slate-400 text-xs italic">Completed</span>'
                        }
                    </td>
                </tr>
            `;
        }).join("");

    } catch (err) {
        console.error("Error loading bills:", err);
        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-rose-500">Failed to load invoices from server.</td></tr>`;
    }
}

// Process online payment simulation
async function payBill(id) {
    if (!id) return;
    if (!confirm("Proceed with online payment simulation?")) return;

    try {
        const res = await fetch(`/api/billing/pay/${id}`, { method: "POST" });
        if (res.ok) {
            alert("Payment processed successfully!");
            loadBills();
        } else {
            const data = await res.json().catch(() => ({}));
            alert(data.message || "Failed to process payment.");
        }
    } catch (err) {
        console.error("Payment error:", err);
        alert("Network error processing payment.");
    }
}

// Create a new billing invoice via API
async function createNewBill(patientName, amount) {
    if (!patientName || isNaN(amount) || amount <= 0) {
        alert("Please enter a valid patient name and numeric amount.");
        return false;
    }

    try {
        const res = await fetch("/api/billing", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ patient_name: patientName, amount: amount })
        });

        if (res.ok) {
            alert("Invoice created successfully!");
            loadBills();
            return true;
        } else {
            const data = await res.json().catch(() => ({}));
            alert(data.message || "Error creating invoice.");
            return false;
        }
    } catch (err) {
        console.error("Error creating bill:", err);
        alert("Network error creating invoice.");
        return false;
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