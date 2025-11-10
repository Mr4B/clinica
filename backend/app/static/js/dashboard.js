// static/js/dashboard.js

let currentUser = null;

// Carica i dati dell'utente
async function loadUserData() {
    try {
        const data = await apiCall(`${API_BASE}/users/me`);
        currentUser = data;
        displayUserInfo();
    } catch (error) {
        console.error('Errore nel caricamento utente:', error);
        // Se il token non è valido, redirect al login
        if (error.message.includes('401') || error.message.includes('403')) {
            TokenManager.remove();
            window.location.href = '/login';
        }
    }
}

// Mostra le info utente nell'header
function displayUserInfo() {
    if (!currentUser) return;
    
    // Avatar con iniziali
    const initials = (currentUser.first_name?.[0] || '') + (currentUser.last_name?.[0] || '');
    document.getElementById('userAvatar').textContent = initials.toUpperCase();
    
    // Nome completo
    const fullName = `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.username;
    document.getElementById('userName').textContent = fullName;
    
    // Ruolo
    const roleText = currentUser.is_superuser ? 'Amministratore' : 'Operatore';
    document.getElementById('userRole').textContent = roleText;
    
    // Welcome message
    const welcomeName = currentUser.first_name || currentUser.username;
    document.getElementById('welcomeName').textContent = welcomeName;
}

// Toggle dropdown menu utente
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

// Chiudi dropdown se clicco fuori
document.addEventListener('click', function(event) {
    const userMenu = document.querySelector('.user-menu');
    if (userMenu && !userMenu.contains(event.target)) {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    }
});

// Init quando la pagina è caricata
document.addEventListener('DOMContentLoaded', function() {
    requireAuth();
    loadUserData();
});