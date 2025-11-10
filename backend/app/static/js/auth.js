// static/js/auth.js

// Configurazione API
const API_BASE = '/api/v1';

// Gestione token
const TokenManager = {
    get: () => localStorage.getItem('access_token'),
    set: (token) => localStorage.setItem('access_token', token),
    remove: () => localStorage.removeItem('access_token'),
    isAuthenticated: () => !!localStorage.getItem('access_token')
};

// Utility per le chiamate API
async function apiCall(url, options = {}) {
    const token = TokenManager.get();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token && !options.skipAuth) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Errore nella richiesta');
        }
        
        return data;
    } catch (error) {
        throw error;
    }
}

// Mostra messaggi di errore/successo
function showMessage(message, type = 'error') {
    const alertDiv = document.getElementById('alert');
    if (!alertDiv) return;
    
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.display = 'block';
    
    if (type === 'success') {
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 3000);
    }
}

// Login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    
    // Disabilita il bottone e mostra spinner
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        // OAuth2 richiede form-data
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/login/access-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Credenziali non valide');
        }
        
        // Salva il token
        TokenManager.set(data.access_token);
        
        showMessage('Login effettuato con successo!', 'success');
        
        // Redirect alla dashboard
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1000);
        
    } catch (error) {
        showMessage(error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Registrazione
async function handleSignup(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validazione password
    if (password !== confirmPassword) {
        showMessage('Le password non coincidono', 'error');
        return;
    }
    
    if (password.length < 3) {
        showMessage('La password deve essere di almeno 3 caratteri', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        const userData = {
            first_name: firstName,
            last_name: lastName,
            username: username,
            password: password
        };
        
        const data = await apiCall(`${API_BASE}/users/signup`, {
            method: 'POST',
            body: JSON.stringify(userData),
            skipAuth: true
        });
        
        showMessage('Registrazione completata! Reindirizzamento al login...', 'success');
        
        // Redirect al login dopo 2 secondi
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
        
    } catch (error) {
        showMessage(error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Logout
function handleLogout() {
    TokenManager.remove();
    window.location.href = '/login';
}

// Verifica autenticazione
function requireAuth() {
    if (!TokenManager.isAuthenticated()) {
        window.location.href = '/login';
    }
}

// Check se già loggato (per pagine login/signup)
function redirectIfAuthenticated() {
    if (TokenManager.isAuthenticated()) {
        window.location.href = '/dashboard';
    }
}