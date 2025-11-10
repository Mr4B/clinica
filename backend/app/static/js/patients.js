// static/js/patients.js

let currentPatients = [];
let currentPage = 1;
let totalPatients = 0;
const pageSize = 20;

// Carica pazienti
async function loadPatients() {
    try {
        const filters = getFilters();
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...filters
        });
        
        const data = await apiCall(`${API_BASE}/patients?${params}`);
        
        currentPatients = data.items;
        totalPatients = data.total;
        
        renderPatientsTable();
        renderPagination(data);
        
    } catch (error) {
        console.error('Errore caricamento pazienti:', error);
        showMessage('Errore nel caricamento dei pazienti: ' + error.message, 'error');
    }
}

// Ottieni filtri
function getFilters() {
    const filters = {};
    
    const search = document.getElementById('searchQuery').value;
    if (search) filters.q = search;
    
    return filters;
}

// Renderizza tabella
function renderPatientsTable() {
    const tbody = document.getElementById('patientsTableBody');
    
    if (currentPatients.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">👥</div>
                        <p>Nessun paziente trovato</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = currentPatients.map(patient => {
        const age = calculateAge(patient.date_of_birth);
        const hasDossier = patient.has_active_dossier ? '✅' : '❌';
        
        return `
            <tr>
                <td>
                    <div class="patient-info">
                        <span class="patient-name">${patient.first_name} ${patient.last_name}</span>
                        <span class="patient-cf">${patient.fiscal_code}</span>
                    </div>
                </td>
                <td>${formatDate(patient.date_of_birth)}</td>
                <td>${age} anni</td>
                <td>${patient.gender || '-'}</td>
                <td style="text-align: center;">${hasDossier}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="viewPatient('${patient.id}')" title="Visualizza">
                            👁️
                        </button>
                        <button class="btn-icon danger" onclick="confirmDeletePatient('${patient.id}')" title="Elimina">
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
    const end = Math.min(currentPage * pageSize, totalPatients);
    
    info.textContent = `Mostrando ${start}-${end} di ${totalPatients}`;
    
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = !data.has_next;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        loadPatients();
    }
}

function nextPage() {
    currentPage++;
    loadPatients();
}

// Applica ricerca
function applySearch() {
    currentPage = 1;
    loadPatients();
}

// Reset ricerca
function resetSearch() {
    document.getElementById('searchQuery').value = '';
    currentPage = 1;
    loadPatients();
}

// === MODALS ===

// Mostra modal creazione
function showCreateModal() {
    document.getElementById('createModal').classList.add('show');
    // Imposta data odierna come massimo
    document.getElementById('dateOfBirth').max = new Date().toISOString().split('T')[0];
}

function closeCreateModal() {
    document.getElementById('createModal').classList.remove('show');
    document.getElementById('createForm').reset();
}

// Crea paziente
async function createPatient(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const fiscalCode = document.getElementById('fiscalCode').value.trim().toUpperCase();
    const dateOfBirth = document.getElementById('dateOfBirth').value;
    const gender = document.getElementById('gender').value;
    const placeOfBirth = document.getElementById('placeOfBirth').value.trim();
    const address = document.getElementById('address').value.trim();
    
    // Validazione CF
    if (fiscalCode.length !== 16) {
        showMessage('Il codice fiscale deve essere di 16 caratteri', 'error');
        return;
    }
    
    // Validazione età
    const age = calculateAge(dateOfBirth);
    if (age < 18) {
        showMessage('Il paziente deve avere almeno 18 anni', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('createSubmitBtn');
    const btnText = submitBtn.querySelector('span:not(.spinner)');
    const btnSpinner = submitBtn.querySelector('.spinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        const patientData = {
            first_name: firstName,
            last_name: lastName,
            fiscal_code: fiscalCode,
            date_of_birth: dateOfBirth,
            gender: gender || null,
            place_of_birth: placeOfBirth || null,
            address: address || null
        };
        
        await apiCall(`${API_BASE}/patients`, {
            method: 'POST',
            body: JSON.stringify(patientData)
        });
        
        showMessage('Paziente creato con successo!', 'success');
        closeCreateModal();
        loadPatients();
        
    } catch (error) {
        showMessage('Errore nella creazione: ' + error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Visualizza dettaglio paziente
async function viewPatient(patientId) {
    try {
        const patient = await apiCall(`${API_BASE}/patients/${patientId}`);
        
        // Popola modal
        document.getElementById('detailName').textContent = `${patient.first_name} ${patient.last_name}`;
        document.getElementById('detailFiscalCode').textContent = patient.fiscal_code;
        document.getElementById('detailDateOfBirth').textContent = formatDate(patient.date_of_birth);
        document.getElementById('detailAge').textContent = `${calculateAge(patient.date_of_birth)} anni`;
        document.getElementById('detailGender').textContent = patient.gender || '-';
        document.getElementById('detailPlaceOfBirth').textContent = patient.place_of_birth || '-';
        document.getElementById('detailAddress').textContent = patient.address || '-';
        document.getElementById('detailCreatedAt').textContent = formatDateTime(patient.created_at);
        
        // Carica dossiers del paziente
        loadPatientDossiers(patientId);
        
        // Mostra modal
        document.getElementById('detailModal').classList.add('show');
        
    } catch (error) {
        showMessage('Errore nel caricamento dettagli: ' + error.message, 'error');
    }
}

function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('show');
}

// Carica dossiers del paziente
async function loadPatientDossiers(patientId) {
    const container = document.getElementById('patientDossiersList');
    
    try {
        const data = await apiCall(`${API_BASE}/dossiers?patient_id=${patientId}&page_size=100`);
        
        if (data.items.length === 0) {
            container.innerHTML = '<p style="color: #6b7280; text-align: center; padding: 20px;">Nessun dossier presente</p>';
            return;
        }
        
        container.innerHTML = data.items.map(dossier => {
            const statusClass = dossier.status === 'active' ? 'status-active' : 'status-discharged';
            const statusText = dossier.status === 'active' ? 'Attivo' : 'Dimesso';
            
            return `
                <div class="module-item">
                    <div class="module-info">
                        <span class="module-code">
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </span>
                        <span class="module-date">
                            Ammissione: ${formatDate(dossier.admission_date)}
                            ${dossier.discharge_date ? ` - Dimissione: ${formatDate(dossier.discharge_date)}` : ''}
                        </span>
                    </div>
                    <button class="btn-icon" onclick="goToDossier('${dossier.id}')" title="Visualizza Dossier">
                        📋
                    </button>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        container.innerHTML = '<p style="color: #ef4444; text-align: center; padding: 20px;">Errore nel caricamento dossiers</p>';
    }
}

// Vai al dossier
function goToDossier(dossierId) {
    window.location.href = `/dossiers?dossier_id=${dossierId}`;
}

// Conferma eliminazione
function confirmDeletePatient(patientId) {
    if (confirm('Sei sicuro di voler eliminare questo paziente?\n\nQuesta operazione è reversibile (soft delete).')) {
        deletePatient(patientId);
    }
}

// Elimina paziente
async function deletePatient(patientId) {
    try {
        await apiCall(`${API_BASE}/patients/${patientId}`, {
            method: 'DELETE'
        });
        
        showMessage('Paziente eliminato con successo', 'success');
        loadPatients();
        
    } catch (error) {
        showMessage('Errore nell\'eliminazione: ' + error.message, 'error');
    }
}

// Utility
function calculateAge(dateOfBirth) {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    return age;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT');
}

// Init
document.addEventListener('DOMContentLoaded', function() {
    requireAuth();
    loadPatients();
});