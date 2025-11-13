// static/js/utenti.js

let currentTab = 'users'; // 'users' o 'roles'
let allUsers = [];
let allRoles = [];
let allModules = [];

// === TAB MANAGEMENT ===

function switchTab(tab) {
    currentTab = tab;
    
    // Aggiorna UI tabs
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    // Mostra/nascondi sezioni
    document.getElementById('usersSection').style.display = tab === 'users' ? 'block' : 'none';
    document.getElementById('rolesSection').style.display = tab === 'roles' ? 'block' : 'none';
    
    // Carica dati
    if (tab === 'users') {
        loadUsers();
    } else {
        loadRoles();
    }
}

// === USERS ===

async function loadUsers() {
    try {
        const data = await apiCall(`${API_BASE}/users/`);
        allUsers = data.data;
        renderUsersTable();
    } catch (error) {
        console.error('Errore caricamento utenti:', error);
        showMessage('Errore nel caricamento degli utenti: ' + error.message, 'error');
    }
}

function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    
    if (allUsers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">👤</div>
                        <p>Nessun utente trovato</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = allUsers.map(user => {
        const roleText = user.is_superuser ? '👑 Superuser' : (user.role_id ? 'Ruolo assegnato' : 'Nessun ruolo');
        const roleBadge = user.is_superuser 
            ? '<span class="status-badge" style="background: #fef3c7; color: #92400e;">👑 Admin</span>'
            : '<span class="status-badge status-active">👤 Operatore</span>';
        
        return `
            <tr>
                <td>
                    <div class="patient-info">
                        <span class="patient-name">${user.first_name} ${user.last_name}</span>
                        <span class="patient-cf">@${user.username}</span>
                    </div>
                </td>
                <td>${roleBadge}</td>
                <td>${user.structure_id ? `Struttura ${user.structure_id.substring(0, 8)}...` : '-'}</td>
                <td>${user.role_id ? user.role_id.substring(0, 8) + '...' : '-'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="showAssignRoleModal('${user.id}')" title="Assegna Ruolo">
                            🔑
                        </button>
                        <button class="btn-icon danger" onclick="confirmDeleteUser('${user.id}')" title="Elimina">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Mostra modal creazione utente
async function showCreateUserModal() {
    // Carica ruoli disponibili
    try {
        const rolesData = await apiCall(`${API_BASE}/roles/`);
        const rolesSelect = document.getElementById('userRoleId');
        rolesSelect.innerHTML = '<option value="">Nessun ruolo</option>' + 
            rolesData.data.map(role => `<option value="${role.id}">${role.name}</option>`).join('');
    } catch (error) {
        console.error('Errore caricamento ruoli:', error);
    }
    
    document.getElementById('createUserModal').classList.add('show');
}

function closeCreateUserModal() {
    document.getElementById('createUserModal').classList.remove('show');
    document.getElementById('createUserForm').reset();
}

// Crea utente
async function createUser(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('userFirstName').value.trim();
    const lastName = document.getElementById('userLastName').value.trim();
    const username = document.getElementById('userUsername').value.trim();
    const password = document.getElementById('userPassword').value;
    const roleId = document.getElementById('userRoleId').value;
    const isSuperuser = document.getElementById('userIsSuperuser').checked;
    
    if (password.length < 8) {
        showMessage('La password deve essere di almeno 8 caratteri', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('createUserSubmitBtn');
    const btnText = submitBtn.querySelector('span:not(.spinner)');
    const btnSpinner = submitBtn.querySelector('.spinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        const userData = {
            first_name: firstName,
            last_name: lastName,
            username: username,
            password: password,
            structure_id: "00000000-0000-0000-0000-000000000001", // Default structure ID
            role_id: roleId || null,
            is_superuser: isSuperuser
        };
        
        await apiCall(`${API_BASE}/users/`, {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        showMessage('Utente creato con successo!', 'success');
        closeCreateUserModal();
        loadUsers();
        
    } catch (error) {
        showMessage('Errore nella creazione: ' + error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Assegna ruolo a utente
async function showAssignRoleModal(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('assignRoleUserId').value = userId;
    document.getElementById('assignRoleUserName').textContent = `${user.first_name} ${user.last_name}`;
    
    // Carica ruoli
    try {
        const rolesData = await apiCall(`${API_BASE}/roles/`);
        const rolesSelect = document.getElementById('assignRoleSelect');
        rolesSelect.innerHTML = rolesData.data.map(role => 
            `<option value="${role.id}" ${role.id === user.role_id ? 'selected' : ''}>${role.name}</option>`
        ).join('');
    } catch (error) {
        showMessage('Errore nel caricamento ruoli: ' + error.message, 'error');
        return;
    }
    
    document.getElementById('assignRoleModal').classList.add('show');
}

function closeAssignRoleModal() {
    document.getElementById('assignRoleModal').classList.remove('show');
}

async function assignRole(event) {
    event.preventDefault();
    
    const userId = document.getElementById('assignRoleUserId').value;
    const roleId = document.getElementById('assignRoleSelect').value;
    
    if (!roleId) {
        showMessage('Seleziona un ruolo', 'error');
        return;
    }
    
    try {
        await apiCall(`${API_BASE}/users/${userId}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role_id: roleId })
        });
        
        showMessage('Ruolo assegnato con successo!', 'success');
        closeAssignRoleModal();
        loadUsers();
        
    } catch (error) {
        showMessage('Errore nell\'assegnazione: ' + error.message, 'error');
    }
}

// Elimina utente
function confirmDeleteUser(userId) {
    if (confirm('Sei sicuro di voler eliminare questo utente?')) {
        deleteUser(userId);
    }
}

async function deleteUser(userId) {
    try {
        await apiCall(`${API_BASE}/users/${userId}`, {
            method: 'DELETE'
        });
        
        showMessage('Utente eliminato con successo', 'success');
        loadUsers();
        
    } catch (error) {
        showMessage('Errore nell\'eliminazione: ' + error.message, 'error');
    }
}

// === ROLES ===

async function loadRoles() {
    try {
        const data = await apiCall(`${API_BASE}/roles/`);
        allRoles = data.data;
        renderRolesTable();
    } catch (error) {
        console.error('Errore caricamento ruoli:', error);
        showMessage('Errore nel caricamento dei ruoli: ' + error.message, 'error');
    }
}

function renderRolesTable() {
    const tbody = document.getElementById('rolesTableBody');
    
    if (allRoles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    <div class="empty-state">
                        <div class="empty-state-icon">🔑</div>
                        <p>Nessun ruolo trovato</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = allRoles.map(role => {
        const modulesCount = role.modules ? role.modules.length : 0;
        const modulesList = role.modules && role.modules.length > 0 
            ? role.modules.slice(0, 3).join(', ') + (role.modules.length > 3 ? '...' : '')
            : 'Nessun modulo';
        
        return `
            <tr>
                <td>
                    <span style="font-weight: 600;">${role.name}</span>
                </td>
                <td>
                    <span class="status-badge status-active">${modulesCount} moduli</span>
                </td>
                <td style="font-size: 12px; color: #6b7280;">${modulesList}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="viewRole('${role.id}')" title="Visualizza">
                            👁️
                        </button>
                        <button class="btn-icon" onclick="showEditRoleModal('${role.id}')" title="Modifica">
                            ✏️
                        </button>
                        <button class="btn-icon danger" onclick="confirmDeleteRole('${role.id}')" title="Elimina">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Carica moduli dal catalogo
async function loadModulesCatalog() {
    try {
        const data = await apiCall(`${API_BASE}/modules/catalogs?active_only=true&page_size=100`);
        console.log(data)
        console.log("pippo")
        allModules = data.items;
        return allModules;
    } catch (error) {
        console.error('Errore caricamento moduli:', error);
        showMessage('Errore nel caricamento del catalogo moduli: ' + error.message, 'error');
        return [];
    }
}

// Mostra modal creazione ruolo
async function showCreateRoleModal() {
    await loadModulesCatalog();
    renderModulesCheckboxes([]);
    document.getElementById('createRoleModal').classList.add('show');
}

function closeCreateRoleModal() {
    document.getElementById('createRoleModal').classList.remove('show');
    document.getElementById('createRoleForm').reset();
}

// Renderizza checkbox moduli
function renderModulesCheckboxes(selectedModules) {
    const container = document.getElementById('modulesCheckboxes');
    
    if (allModules.length === 0) {
        container.innerHTML = '<p style="color: #6b7280;">Nessun modulo disponibile</p>';
        return;
    }
    
    container.innerHTML = allModules.map(module => {
        const isChecked = selectedModules.includes(module.code);
        return `
            <label class="checkbox-item">
                <input 
                    type="checkbox" 
                    name="modules" 
                    value="${module.code}" 
                    ${isChecked ? 'checked' : ''}
                >
                <div>
                    <div style="font-weight: 600;">${module.code}</div>
                    <div style="font-size: 12px; color: #6b7280;">${module.name || 'Senza descrizione'}</div>
                </div>
            </label>
        `;
    }).join('');
}

// Crea ruolo
async function createRole(event) {
    event.preventDefault();
    
    const name = document.getElementById('roleName').value.trim();
    const moduleCheckboxes = document.querySelectorAll('input[name="modules"]:checked');
    const modules = Array.from(moduleCheckboxes).map(cb => cb.value);
    
    if (!name) {
        showMessage('Inserisci il nome del ruolo', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('createRoleSubmitBtn');
    const btnText = submitBtn.querySelector('span:not(.spinner)');
    const btnSpinner = submitBtn.querySelector('.spinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        const roleData = {
            name: name,
            modules: modules
        };
        
        await apiCall(`${API_BASE}/roles/`, {
            method: 'POST',
            body: JSON.stringify(roleData)
        });
        
        showMessage('Ruolo creato con successo!', 'success');
        closeCreateRoleModal();
        loadRoles();
        
    } catch (error) {
        showMessage('Errore nella creazione: ' + error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Visualizza dettaglio ruolo
async function viewRole(roleId) {
    const role = allRoles.find(r => r.id === roleId);
    if (!role) return;
    
    document.getElementById('viewRoleName').textContent = role.name;
    
    const modulesList = document.getElementById('viewRoleModules');
    if (role.modules && role.modules.length > 0) {
        modulesList.innerHTML = role.modules.map(code => 
            `<span class="status-badge status-active">${code}</span>`
        ).join(' ');
    } else {
        modulesList.innerHTML = '<p style="color: #6b7280;">Nessun modulo assegnato</p>';
    }
    
    document.getElementById('viewRoleModal').classList.add('show');
}

function closeViewRoleModal() {
    document.getElementById('viewRoleModal').classList.remove('show');
}

// Mostra modal modifica ruolo
async function showEditRoleModal(roleId) {
    const role = allRoles.find(r => r.id === roleId);
    if (!role) return;
    
    await loadModulesCatalog();
    
    document.getElementById('editRoleId').value = roleId;
    document.getElementById('editRoleName').value = role.name;
    
    renderEditModulesCheckboxes(role.modules || []);
    
    document.getElementById('editRoleModal').classList.add('show');
}

function closeEditRoleModal() {
    document.getElementById('editRoleModal').classList.remove('show');
    document.getElementById('editRoleForm').reset();
}

function renderEditModulesCheckboxes(selectedModules) {
    const container = document.getElementById('editModulesCheckboxes');
    
    if (allModules.length === 0) {
        container.innerHTML = '<p style="color: #6b7280;">Nessun modulo disponibile</p>';
        return;
    }
    
    container.innerHTML = allModules.map(module => {
        const isChecked = selectedModules.includes(module.code);
        return `
            <label class="checkbox-item">
                <input 
                    type="checkbox" 
                    name="editModules" 
                    value="${module.code}" 
                    ${isChecked ? 'checked' : ''}
                >
                <div>
                    <div style="font-weight: 600;">${module.code}</div>
                    <div style="font-size: 12px; color: #6b7280;">${module.name || 'Senza descrizione'}</div>
                </div>
            </label>
        `;
    }).join('');
}

// Modifica ruolo
async function editRole(event) {
    event.preventDefault();
    
    const roleId = document.getElementById('editRoleId').value;
    const name = document.getElementById('editRoleName').value.trim();
    const moduleCheckboxes = document.querySelectorAll('input[name="editModules"]:checked');
    const modules = Array.from(moduleCheckboxes).map(cb => cb.value);
    
    if (!name) {
        showMessage('Inserisci il nome del ruolo', 'error');
        return;
    }
    
    try {
        const roleData = {
            name: name,
            modules: modules
        };
        
        await apiCall(`${API_BASE}/roles/${roleId}`, {
            method: 'PUT',
            body: JSON.stringify(roleData)
        });
        
        showMessage('Ruolo aggiornato con successo!', 'success');
        closeEditRoleModal();
        loadRoles();
        
    } catch (error) {
        showMessage('Errore nell\'aggiornamento: ' + error.message, 'error');
    }
}

// Elimina ruolo
function confirmDeleteRole(roleId) {
    if (confirm('Sei sicuro di voler eliminare questo ruolo?\n\nGli utenti con questo ruolo perderanno i permessi associati.')) {
        deleteRole(roleId);
    }
}

async function deleteRole(roleId) {
    try {
        await apiCall(`${API_BASE}/roles/${roleId}`, {
            method: 'DELETE'
        });
        
        showMessage('Ruolo eliminato con successo', 'success');
        loadRoles();
        
    } catch (error) {
        showMessage('Errore nell\'eliminazione: ' + error.message, 'error');
    }
}

// Init
document.addEventListener('DOMContentLoaded', function() {
    requireAuth();
    switchTab('users');
});