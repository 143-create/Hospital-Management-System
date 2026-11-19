// ==========================================
// CarePulse Hospital System - Authentication JS
// ==========================================

// Restore pending OTP verification state if user already requested an OTP
document.addEventListener("DOMContentLoaded", () => {
    const pendingEmail = sessionStorage.getItem("pending_email");
    const otpBox = document.getElementById("otpBox");
    if (pendingEmail && otpBox) {
        const emailInput = document.getElementById("regEmail");
        if (emailInput && !emailInput.value) {
            emailInput.value = pendingEmail;
        }
        showOtpBox(pendingEmail);
    }
});

function showOtpBox(email) {
    const otpBox = document.getElementById("otpBox");
    if (!otpBox) return;

    otpBox.classList.remove("hidden");
    otpBox.style.display = "block";

    const otpSentTo = document.getElementById("otpSentTo");
    if (otpSentTo && email) {
        otpSentTo.innerText = `Sent to ${email}`;
    }

    const otpCode = document.getElementById("otpCode");
    if (otpCode) {
        otpCode.focus();
    }
}

async function sendOTP(event) {
    if (event) event.preventDefault();

    const name = document.getElementById("regName")?.value.trim();
    const user_id = document.getElementById("regUserId")?.value.trim();
    const phone = document.getElementById("regPhone")?.value.trim();
    const email = document.getElementById("regEmail")?.value.trim();
    const password = document.getElementById("regPassword")?.value;
    const role = document.getElementById("regRole")?.value || "Patient";

    if (!name || !email || !password) {
        alert("Please fill in all required fields (Name, Email, Password) before requesting OTP.");
        return;
    }

    const sendBtn = document.getElementById("sendOtpBtn");
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerText = "Sending OTP...";
    }

    try {
        const res = await fetch("/api/auth/send-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, user_id, phone, email, password, role })
        });

        const rawText = await res.text();
        let data = {};
        try {
            data = JSON.parse(rawText);
        } catch {
            throw new Error(`Server error (HTTP ${res.status}): ${rawText.slice(0, 120)}`);
        }

        if (res.ok) {
            sessionStorage.setItem("pending_email", email);
            showOtpBox(email);
            alert(data.message || "Verification code sent to your email!");
        } else {
            alert(data.message || `Error ${res.status}: Failed to send OTP.`);
        }
    } catch (err) {
        console.error("Error sending OTP:", err);
        if (window.location.protocol === "file:" || window.location.port !== "5000") {
            alert("Wrong URL! Open http://127.0.0.1:5000/register in your browser instead of Live Server or file://.");
        } else {
            alert(err.message.includes("Failed to fetch")
                ? "Cannot connect to Flask. Make sure 'python app.py' is running on port 5000."
                : err.message);
        }
    } finally {
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerText = "Resend OTP";
        }
    }
}

async function verifyOTP(event) {
    if (event) event.preventDefault();

    const email = sessionStorage.getItem("pending_email") || document.getElementById("regEmail")?.value.trim();
    const otp = document.getElementById("otpCode")?.value.trim();

    if (!email) {
        alert("Session expired. Please re-enter your email address and request a new OTP.");
        return;
    }

    if (!otp || otp.length < 6) {
        alert("Please enter the 6-digit OTP verification code.");
        return;
    }

    const verifyBtn = document.getElementById("verifyOtpBtn");
    if (verifyBtn) {
        verifyBtn.disabled = true;
        verifyBtn.innerText = "Verifying...";
    }

    try {
        const res = await fetch("/api/auth/verify-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, otp })
        });

        const data = await res.json();

        if (res.ok) {
            sessionStorage.removeItem("pending_email");
            if (data.user) {
                sessionStorage.setItem("userName", data.user.name);
                sessionStorage.setItem("userRole", data.user.role);
            }
            alert("Registration and Email Verification Successful! Redirecting to Dashboard...");
            window.location.href = "/dashboard";
        } else {
            alert(data.message || "Invalid OTP code. Please check and try again.");
        }
    } catch (err) {
        console.error("Error verifying OTP:", err);
        alert("Server connection error during verification.");
    } finally {
        if (verifyBtn) {
            verifyBtn.disabled = false;
            verifyBtn.innerText = "Verify & Complete";
        }
    }
}

async function loginUser(event) {
    if (event) event.preventDefault();

    const identifier = (document.getElementById("loginIdentifier") || document.getElementById("loginPhone") || document.getElementById("loginEmail"))?.value.trim();
    const password = document.getElementById("loginPassword")?.value;
    const loginBtn = document.getElementById("loginBtn");

    if (!identifier || !password) {
        alert("Please enter both your email/phone number and password.");
        return;
    }

    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerText = "Logging in...";
    }

    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: identifier, password: password })
        });

        const data = await res.json();

        if (res.ok) {
            if (data.user) {
                sessionStorage.setItem("userName", data.user.name);
                sessionStorage.setItem("userRole", data.user.role);
            }
            window.location.href = "/dashboard";
        } else {
            alert(data.message || "Invalid credentials. Please try again.");
        }
    } catch (err) {
        console.error("Error during login:", err);
        alert("Server connection error during login.");
    } finally {
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerText = "Login";
        }
    }
}