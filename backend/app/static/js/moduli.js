// static/js/moduli.js

let currentModules = [];
let currentPage = 1;
let totalModules = 0;
const pageSize = 20;

// Carica moduli del catalogo
async function loadModules() {
    try {
        const filters = getFilters();
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...filters
        });
        
        const data = await apiCall(`${API_BASE}/modules/catalogs?${params}`);
        
        currentModules = data.items;
        totalModules = data.total;
        
        renderModulesTable();
        renderPagination(data);
        
    } catch (error) {
        console.error('Errore caricamento moduli:', error);
        showMessage('Errore nel caricamento dei moduli: ' + error.message, 'error');
    }
}

// Ottieni filtri
function getFilters() {
    const filters = {};
    
    const search = document.getElementById('searchQuery').value;
    const activeOnly = document.getElementById('filterActiveOnly').checked;
    
    if (search) filters.q = search;
    if (activeOnly) filters.active_only = true;
    
    return filters;
}

// Renderizza tabella
function renderModulesTable() {
    const tbody = document.getElementById('modulesTableBody');
    
    if (currentModules.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">📄</div>
                        <p>Nessun modulo trovato</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = currentModules.map(module => {
        const statusBadge = module.active 
            ? '<span class="status-badge status-active">✅ Attivo</span>'
            : '<span class="status-badge status-discharged">❌ Disattivo</span>';
        
        return `
            <tr>
                <td>
                    <span style="font-weight: 600; font-family: monospace; color: var(--primary);">
                        ${module.code}
                    </span>
                </td>
                <td>${module.name || '-'}</td>
                <td style="text-align: center;">
                    <span class="status-badge" style="background: #e0e7ff; color: #4338ca;">
                        v${module.current_schema_version}
                    </span>
                </td>
                <td>${statusBadge}</td>
                <td style="font-size: 12px; color: #6b7280;">
                    ${module.updated_at ? formatDate(module.updated_at) : '-'}
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="viewModule(${module.module_id})" title="Visualizza">
                            👁️
                        </button>
                        <button class="btn-icon" onclick="showEditModal(${module.module_id})" title="Modifica">
                            ✏️
                        </button>
                        <button class="btn-icon" onclick="toggleModuleStatus(${module.module_id}, ${!module.active})" 
                                title="${module.active ? 'Disattiva' : 'Attiva'}">
                            ${module.active ? '⏸️' : '▶️'}
                        </button>
                        <button class="btn-icon danger" onclick="confirmDeleteModule(${module.module_id})" title="Elimina">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Paginazione
function renderPagination(data) {
    const info = document.getElementById('paginationInfo');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalModules);
    
    info.textContent = `Mostrando ${start}-${end} di ${totalModules}`;
    
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = !data.has_next;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        loadModules();
    }
}

function nextPage() {
    currentPage++;
    loadModules();
}

// Applica filtri
function applyFilters() {
    currentPage = 1;
    loadModules();
}

// Reset filtri
function resetFilters() {
    document.getElementById('searchQuery').value = '';
    document.getElementById('filterActiveOnly').checked = false;
    currentPage = 1;
    loadModules();
}

// === MODALS ===

// Mostra modal creazione
function showCreateModal() {
    document.getElementById('createModal').classList.add('show');
}

function closeCreateModal() {
    document.getElementById('createModal').classList.remove('show');
    document.getElementById('createForm').reset();
}

// Crea modulo
async function createModule(event) {
    event.preventDefault();
    
    const code = document.getElementById('moduleCode').value.trim().toUpperCase();
    const name = document.getElementById('moduleName').value.trim();
    const version = parseInt(document.getElementById('moduleVersion').value);
    const active = document.getElementById('moduleActive').checked;
    
    // Validazione code
    if (code.length > 10) {
        showMessage('Il codice deve essere massimo 10 caratteri', 'error');
        return;
    }
    
    if (version <= 0) {
        showMessage('La versione deve essere maggiore di 0', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('createSubmitBtn');
    const btnText = submitBtn.querySelector('span:not(.spinner)');
    const btnSpinner = submitBtn.querySelector('.spinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        const moduleData = {
            code: code,
            name: name || null,
            current_schema_version: version,
            active: active
        };
        
        await apiCall(`${API_BASE}/modules/catalogs`, {
            method: 'POST',
            body: JSON.stringify(moduleData)
        });
        
        showMessage('Modulo creato con successo!', 'success');
        closeCreateModal();
        loadModules();
        
    } catch (error) {
        showMessage('Errore nella creazione: ' + error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Visualizza dettaglio modulo
async function viewModule(moduleId) {
    try {
        const module = await apiCall(`${API_BASE}/modules/catalogs/${moduleId}`);
        
        document.getElementById('detailCode').textContent = module.code;
        document.getElementById('detailName').textContent = module.name || '-';
        document.getElementById('detailVersion').textContent = `v${module.current_schema_version}`;
        document.getElementById('detailActive').innerHTML = module.active 
            ? '<span class="status-badge status-active">✅ Attivo</span>'
            : '<span class="status-badge status-discharged">❌ Disattivo</span>';
        document.getElementById('detailUpdated').textContent = module.updated_at ? formatDate(module.updated_at) : '-';
        
        // Link per registrare modulo (da implementare)
        const registerBtn = document.getElementById('registerModuleBtn');
        registerBtn.onclick = () => {
            alert(`Registrazione modulo ${module.code} - Da implementare nella prossima fase`);
            // Qui andrà il link alla pagina di compilazione del modulo
            // window.location.href = `/moduli/compila?code=${module.code}`;
        };
        
        document.getElementById('detailModal').classList.add('show');
        
    } catch (error) {
        showMessage('Errore nel caricamento dettagli: ' + error.message, 'error');
    }
}

function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('show');
}

// Mostra modal modifica
async function showEditModal(moduleId) {
    try {
        const module = await apiCall(`${API_BASE}/modules/catalogs/${moduleId}`);
        
        document.getElementById('editModuleId').value = moduleId;
        document.getElementById('editModuleCode').value = module.code;
        document.getElementById('editModuleName').value = module.name || '';
        document.getElementById('editModuleVersion').value = module.current_schema_version;
        document.getElementById('editModuleActive').checked = module.active;
        
        document.getElementById('editModal').classList.add('show');
        
    } catch (error) {
        showMessage('Errore nel caricamento modulo: ' + error.message, 'error');
    }
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('show');
    document.getElementById('editForm').reset();
}

// Modifica modulo
async function editModule(event) {
    event.preventDefault();
    
    const moduleId = document.getElementById('editModuleId').value;
    const name = document.getElementById('editModuleName').value.trim();
    const version = parseInt(document.getElementById('editModuleVersion').value);
    const active = document.getElementById('editModuleActive').checked;
    
    if (version <= 0) {
        showMessage('La versione deve essere maggiore di 0', 'error');
        return;
    }
    
    try {
        const moduleData = {
            name: name || null,
            current_schema_version: version,
            active: active
        };
        
        // NOTA: typo nell'endpoint: "catalogs"
        await apiCall(`${API_BASE}/modules/catalogs/${moduleId}`, {
            method: 'PATCH',
            body: JSON.stringify(moduleData)
        });
        
        showMessage('Modulo aggiornato con successo!', 'success');
        closeEditModal();
        loadModules();
        
    } catch (error) {
        showMessage('Errore nell\'aggiornamento: ' + error.message, 'error');
    }
}

// Toggle status (attiva/disattiva)
async function toggleModuleStatus(moduleId, newStatus) {
    try {
        await apiCall(`${API_BASE}/modules/catalogs/${moduleId}`, {
            method: 'PATCH',
            body: JSON.stringify({ active: newStatus })
        });
        
        showMessage(`Modulo ${newStatus ? 'attivato' : 'disattivato'} con successo!`, 'success');
        loadModules();
        
    } catch (error) {
        showMessage('Errore nell\'aggiornamento: ' + error.message, 'error');
    }
}

// Conferma eliminazione
function confirmDeleteModule(moduleId) {
    if (confirm('Sei sicuro di voler eliminare questo modulo dal catalogo?\n\nQuesta operazione è IRREVERSIBILE e rimuoverà il modulo dalla lista dei moduli disponibili.')) {
        deleteModule(moduleId);
    }
}

// Elimina modulo
async function deleteModule(moduleId) {
    try {
        await apiCall(`${API_BASE}/modules/catalogs/${moduleId}`, {
            method: 'DELETE'
        });
        
        showMessage('Modulo eliminato con successo', 'success');
        loadModules();
        
    } catch (error) {
        showMessage('Errore nell\'eliminazione: ' + error.message, 'error');
    }
}

// Utility
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
}

// Init
document.addEventListener('DOMContentLoaded', function() {
    requireAuth();
    loadModules();
});