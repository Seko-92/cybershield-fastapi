// --- Configuration ---
// CORRECTED: The base URL now includes the /api prefix to match the FastAPI routing.
const API_BASE_URL = "https://cybershield-fastapi-production.up.railway.app/api";

// --- View Management ---

function showView(viewId) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.style.display = 'none';
    });

    // Show the requested view
    const viewToShow = document.getElementById(viewId);
    if (viewToShow) {
        viewToShow.style.display = 'block';
    }

    // Special handling for the dashboard
    if (viewId === 'dashboard-view') {
        const userEmail = sessionStorage.getItem('currentUserEmail');
        if (userEmail) {
            document.getElementById('welcome-message').textContent = `Welcome, ${userEmail}`;
            // Optionally load recent reports here
        }
    }
}

// --- Navigation ---

function goToDashboard() {
    if (sessionStorage.getItem('currentUserId')) {
        showView('dashboard-view');
    } else {
        // Force user to log in if session is expired or invalid
        showView('login-view');
    }
}

function handleSignOut() {
    sessionStorage.removeItem('currentUserId');
    sessionStorage.removeItem('currentUserEmail');
    alert('You have been signed out.');
    showView('home-view');
}


// --- Registration Logic (/api/register) ---

async function handleRegistration(event) {
    event.preventDefault();

    // FIX 2: Correctly reference the form using event.target
    const form = event.target;

    const scope = form.querySelector('input[name="scope"]:checked').value;
    const email = form.querySelector('#reg-email').value;

    // Base user data
    let userData = {
        scope: scope,
        email: email,
    };

    // Collect fields based on scope
    if (scope === 'individual') {
        userData.first_name = form.querySelector('#reg-first-name').value;
        userData.last_name = form.querySelector('#reg-last-name').value;
        userData.mobile = form.querySelector('#reg-mobile').value;
    } else if (scope === 'enterprise') {
        userData.company_name = form.querySelector('#reg-company-name').value;
        userData.company_website = form.querySelector('#reg-company-website').value;
        userData.phone = form.querySelector('#reg-phone').value;
    }

    try {
        // Correct API call: API_BASE_URL already includes /api
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Registration successful! Please sign in with your email.');
            // Automatically switch to the login view after successful registration
            showView('login-view');
        } else {
            alert(`Registration failed: ${result.detail || 'An unknown error occurred.'}`);
        }
    } catch (error) {
        console.error('Network error during registration:', error);
        alert('Could not connect to the backend server. Check the API URL and network connection.');
    }
}


// --- Login Logic (/api/login) ---

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;

    try {
        // Correct API call: API_BASE_URL already includes /api
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });

        const result = await response.json();

        if (response.ok) {
            alert('Login successful!');
            // Save user session details
            sessionStorage.setItem('currentUserId', result.id);
            sessionStorage.setItem('currentUserEmail', result.email);
            // Show dashboard
            goToDashboard();
        } else {
            alert(`Login failed: ${result.detail || 'Invalid email or user not found.'}`);
        }
    } catch (error) {
        console.error('Network error during login:', error);
        alert('Could not connect to the backend server. Check network connection.');
    }
}


// --- Scan Logic (URL - /api/scan) ---

async function handleUrlScan(event) {
    event.preventDefault();
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value;
    const userId = sessionStorage.getItem('currentUserId');

    if (!userId) {
        alert('You must be logged in to perform a scan.');
        return;
    }

    if (!url) {
        alert('Please enter a URL to scan.');
        return;
    }

    // Set loading state
    const resultDiv = document.getElementById('url-scan-result');
    resultDiv.innerHTML = '<p class="text-warning">Scanning... This may take a moment.</p>';

    try {
        // Correct API call: API_BASE_URL already includes /api
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                user_id: parseInt(userId)
            })
        });

        const result = await response.json();

        if (response.ok) {
            displayScanResult(result, resultDiv);
            urlInput.value = ''; // Clear input
        } else {
            resultDiv.innerHTML = `<p class="text-danger">Scan failed: ${result.detail || 'Server error.'}</p>`;
        }
    } catch (error) {
        console.error('Network error during URL scan:', error);
        resultDiv.innerHTML = '<p class="text-danger">Failed to connect to API for scan.</p>';
    }
}

function displayScanResult(data, targetElement) {
    let statusClass = '';

    // Determine the class based on the overall summary status (CLEAN, DANGER, WARNING)
    if (data.overall_summary.includes("DANGER")) {
        statusClass = 'text-danger';
    } else if (data.overall_summary.includes("WARNING")) {
        statusClass = 'text-warning';
    } else {
        statusClass = 'text-success';
    }

    let detailsHtml = '';

    // Simple display for mock Virustotal results
    const vt = data.details.virustotal;
    if (vt) {
        detailsHtml += `
            <p><strong>VirusTotal Summary:</strong></p>
            <ul>
                <li>Status: ${vt.status}</li>
                <li>Malicious Flags: <span class="${vt.malicious_count > 0 ? 'text-danger' : 'text-success'}">${vt.malicious_count}</span></li>
                <li>Harmless Checks: ${vt.harmless_count}</li>
                <li><a href="${vt.results_url}" target="_blank">View Full VT Report</a></li>
            </ul>
        `;
    }

    // Google Safe Browsing
    const gsb = data.details.google_safe_browsing;
    if (gsb) {
         detailsHtml += `
            <p><strong>Google Safe Browsing:</strong></p>
            <ul>
                <li>Status: <span class="${gsb.status === 'SAFE' ? 'text-success' : 'text-danger'}">${gsb.status}</span></li>
                <li>Message: ${gsb.message}</li>
            </ul>
        `;
    }


    // Combine and update the result div
    targetElement.innerHTML = `
        <h4 class="${statusClass}">Scan Result for: ${data.url}</h4>
        <p class="h5 ${statusClass}">${data.overall_summary}</p>
        <hr>
        ${detailsHtml}
        <p class="text-muted small">Report generated: ${new Date().toLocaleTimeString()}</p>
    `;
}

// --- Initialization and Event Listeners ---

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial View Setup
    // If user is logged in, go to dashboard, otherwise, show home
    if (sessionStorage.getItem('currentUserId')) {
        showView('dashboard-view');
    } else {
        showView('home-view');
    }

    // 2. Add event listeners for navigation and forms
    document.getElementById('nav-sign-up').addEventListener('click', () => showView('registration-view'));
    document.getElementById('nav-sign-in').addEventListener('click', () => showView('login-view'));
    document.getElementById('nav-sign-out').addEventListener('click', handleSignOut);
    document.getElementById('nav-dashboard').addEventListener('click', goToDashboard);

    // Use the function on the form submit events
    document.getElementById('registration-form').addEventListener('submit', handleRegistration);
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('url-scan-form').addEventListener('submit', handleUrlScan);

    // 3. Logic to show/hide Individual/Enterprise fields
    const scopeRadios = document.querySelectorAll('input[name="scope"]');
    const individualFields = document.getElementById('individual-fields');
    const enterpriseFields = document.getElementById('enterprise-fields');

    scopeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'individual') {
                individualFields.style.display = 'block';
                enterpriseFields.style.display = 'none';
            } else {
                individualFields.style.display = 'none';
                enterpriseFields.style.display = 'block';
            }
        });
    });
    // Ensure correct initial state
    if (document.getElementById('scope-individual').checked) {
        individualFields.style.display = 'block';
        enterpriseFields.style.display = 'none';
    }
});