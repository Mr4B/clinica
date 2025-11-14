// static/js/dossiers.js

let currentDossiers = [];
let currentPage = 1;
let totalDossiers = 0;
const pageSize = 20;

// Carica dossiers
async function loadDossiers() {
    try {
        const filters = getFilters();
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...filters
        });
        
        const data = await apiCall(`${API_BASE}/dossiers?${params}`);
        
        currentDossiers = data.items;
        totalDossiers = data.total;
        
        renderDossiersTable();
        renderPagination(data);
        
    } catch (error) {
        console.error('Errore caricamento dossiers:', error);
        showMessage('Errore nel caricamento dei dossiers: ' + error.message, 'error');
    }
}

// Ottieni filtri dal form
function getFilters() {
    const filters = {};
    
    const patientId = document.getElementById('filterPatient').value;
    const status = document.getElementById('filterStatus').value;
    const fromDate = document.getElementById('filterFromDate').value;
    const toDate = document.getElementById('filterToDate').value;
    
    if (patientId) filters.patient_id = patientId;
    if (status) filters.status = status;
    if (fromDate) filters.from_admission = fromDate;
    if (toDate) filters.to_admission = toDate;
    
    return filters;
}

// Renderizza tabella
function renderDossiersTable() {
    const tbody = document.getElementById('dossiersTableBody');
    
    if (currentDossiers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7">
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <p>Nessun dossier trovato</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = currentDossiers.map(dossier => {
        // console.log(dossier);
        const careLevelBadge = dossier.care_level === 'R3'
            ? '<span class="status-badge status-active">R3</span>'
            : '<span class="status-badge" style="background: #fef3c7; color: #92400e;">R3D</span>';
        
        return `
            <tr>
                <td>
                    <div class="patient-info">
                        <span class="patient-name">Paziente ID: ${dossier.patient_id}</span>
                        <span class="patient-cf">Caricamento dati...</span>
                    </div>
                </td>
                <td>${formatDate(dossier.admission_date)}</td>
                <td>${dossier.discharge_date ? formatDate(dossier.discharge_date) : '-'}</td>
                <td>${careLevelBadge}</td>
                <td>
                    <span class="status-badge status-active">Attivo</span>
                </td>
                <td>Struttura ${dossier.structure_id}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="viewDossier('${dossier.id}')" title="Visualizza">
                            👁️
                        </button>
                        <button class="btn-icon danger" onclick="confirmDeleteDossier('${dossier.id}')" title="Elimina">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Carica dati pazienti per ogni dossier
    currentDossiers.forEach(dossier => {
        loadPatientInfo(dossier.patient_id);
    });
}

// Carica info paziente
async function loadPatientInfo(patientId) {
    try {
        const patient = await apiCall(`${API_BASE}/patients/${patientId}`);
        
        // Aggiorna celle della tabella con i dati del paziente
        const cells = document.querySelectorAll(`[data-patient-id="${patientId}"]`);
        cells.forEach(cell => {
            const nameSpan = cell.querySelector('.patient-name');
            const cfSpan = cell.querySelector('.patient-cf');
            
            if (nameSpan) {
                nameSpan.textContent = `${patient.first_name} ${patient.last_name}`;
            }
            if (cfSpan) {
                cfSpan.textContent = patient.fiscal_code;
            }
        });
        
        // Aggiorna anche nella riga della tabella se esiste
        const rows = document.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const patientInfo = row.querySelector('.patient-info');
            if (patientInfo) {
                const nameSpan = patientInfo.querySelector('.patient-name');
                if (nameSpan && nameSpan.textContent.includes(patientId)) {
                    nameSpan.textContent = `${patient.first_name} ${patient.last_name}`;
                    const cfSpan = patientInfo.querySelector('.patient-cf');
                    if (cfSpan) {
                        cfSpan.textContent = patient.fiscal_code;
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Errore caricamento paziente:', error);
    }
}

// Paginazione
function renderPagination(data) {
    const info = document.getElementById('paginationInfo');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalDossiers);
    
    info.textContent = `Mostrando ${start}-${end} di ${totalDossiers}`;
    
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = !data.has_next;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        loadDossiers();
    }
}

function nextPage() {
    currentPage++;
    loadDossiers();
}

// Applica filtri
function applyFilters() {
    currentPage = 1;
    loadDossiers();
}

// Reset filtri
function resetFilters() {
    document.getElementById('filterPatient').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterFromDate').value = '';
    document.getElementById('filterToDate').value = '';
    currentPage = 1;
    loadDossiers();
}

// === MODALS ===

// Mostra modal creazione
let allPatients = [];

async function showCreateModal() {
    // Carica lista pazienti
    try {
        const data = await apiCall(`${API_BASE}/patients?page_size=100`);
        allPatients = data.items;
        renderPatientsList(allPatients);
    } catch (error) {
        showMessage('Errore nel caricamento pazienti: ' + error.message, 'error');
        return;
    }
    
    document.getElementById('createModal').classList.add('show');
}

function closeCreateModal() {
    document.getElementById('createModal').classList.remove('show');
    document.getElementById('createForm').reset();
    document.getElementById('selectedPatientId').value = '';
    document.getElementById('selectedPatientName').textContent = 'Nessun paziente selezionato';
}

// Renderizza lista pazienti
function renderPatientsList(patients) {
    const list = document.getElementById('patientsList');
    
    if (patients.length === 0) {
        list.innerHTML = '<div style="padding: 20px; text-align: center; color: #6b7280;">Nessun paziente trovato</div>';
        return;
    }
    
    list.innerHTML = patients.map(patient => `
        <div class="select-item" onclick="selectPatient('${patient.id}', '${patient.first_name} ${patient.last_name}')">
            <div class="patient-info">
                <span class="patient-name">${patient.first_name} ${patient.last_name}</span>
                <span class="patient-cf">${patient.fiscal_code}</span>
            </div>
        </div>
    `).join('');
}

// Cerca pazienti
function searchPatients() {
    const query = document.getElementById('patientSearch').value.toLowerCase();
    const filtered = allPatients.filter(p => 
        p.first_name.toLowerCase().includes(query) ||
        p.last_name.toLowerCase().includes(query) ||
        p.fiscal_code.toLowerCase().includes(query)
    );
    renderPatientsList(filtered);
}

// Seleziona paziente
function selectPatient(patientId, patientName) {
    document.getElementById('selectedPatientId').value = patientId;
    document.getElementById('selectedPatientName').textContent = patientName;
    
    // Evidenzia selezione
    document.querySelectorAll('.select-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.target.closest('.select-item').classList.add('selected');
}

// Crea dossier
async function createDossier(event) {
    event.preventDefault();
    
    const patientId = document.getElementById('selectedPatientId').value;
    if (!patientId) {
        showMessage('Seleziona un paziente', 'error');
        return;
    }
    
    const admissionDate = document.getElementById('admissionDate').value;
    const careLevel = document.getElementById('careLevel').value;  // ✅ NUOVO
    const admissionReason = document.getElementById('admissionReason').value;
    const primaryDiagnosis = document.getElementById('primaryDiagnosis').value;
    
    if (!admissionDate) {
        showMessage('Inserisci la data di ammissione', 'error');
        return;
    }
    
    if (!careLevel) {  // ✅ NUOVO
        showMessage('Seleziona il livello assistenziale', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('createSubmitBtn');
    const btnText = submitBtn.querySelector('span:not(.spinner)');
    const btnSpinner = submitBtn.querySelector('.spinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        // Ottieni structure_id dell'utente corrente
        // const currentUser = await apiCall(`${API_BASE}/users/me`);
        
        // if (!currentUser.structure_id) {
        //     throw new Error('Utente non assegnato a nessuna struttura');
        // }
        
        const dossierData = {
            patient_id: patientId,
            structure_id: "35f32105-8dc9-47fa-ab1e-a0cb50ace5ed",
            admission_date: new Date(admissionDate).toISOString(),
            care_level: careLevel,
            admission_reason: admissionReason || null,
            primary_diagnosis: primaryDiagnosis || null,
            status: "active"
        };
        
        await apiCall(`${API_BASE}/dossiers`, {
            method: 'POST',
            body: JSON.stringify(dossierData)
        });
        
        showMessage('Dossier creato con successo!', 'success');
        closeCreateModal();
        loadDossiers();
        
    } catch (error) {
        showMessage('Errore nella creazione: ' + error.message, 'error');
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

// Visualizza dettaglio dossier
async function viewDossier(dossierId) {
    try {
        // Carica dossier
        const dossier = await apiCall(`${API_BASE}/dossiers/${dossierId}?include_patient=true`);
        // console.log(dossier);
        
        // Carica entries (moduli)
        const entriesData = await apiCall(`${API_BASE}/dossiers/${dossierId}/entries?page_size=100`);
        
        // Popola modal
        document.getElementById('detailPatientName').textContent = 
            dossier.patient ? `${dossier.patient.first_name} ${dossier.patient.last_name}` : 'Caricamento...';
        document.getElementById('detailAdmissionDate').textContent = formatDate(dossier.admission_date);
        document.getElementById('detailDischargeDate').textContent = 
            dossier.discharge_date ? formatDate(dossier.discharge_date) : 'Non dimesso';
        
        // ✅ NUOVO: Mostra care level con badge colorato
        const careLevelText = dossier.care_level === 'R3' 
            ? '<span class="status-badge status-active">R3 - Riabilitazione Intensiva</span>'
            : '<span class="status-badge" style="background: #fef3c7; color: #92400e;">R3D - Riabilitazione Intensiva Demenze</span>';
        document.getElementById('detailCareLevel').innerHTML = careLevelText;
        
        document.getElementById('detailDiagnosis').textContent = dossier.primary_diagnosis || '-';
        document.getElementById('detailReason').textContent = dossier.admission_reason || '-';
        document.getElementById('detailEntriesCount').textContent = dossier.entries_count || 0;
        
        // Renderizza moduli
        renderModulesList(entriesData.items, dossierId);
        
        // Mostra modal
        document.getElementById('detailModal').classList.add('show');
        
    } catch (error) {
        showMessage('Errore nel caricamento dettagli: ' + error.message, 'error');
    }
}

function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('show');
}

// Renderizza lista moduli
function renderModulesList(entries, dossierId) {
    const container = document.getElementById('modulesList');
    
    if (entries.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; text-align: center; padding: 20px;">Nessun modulo presente</p>';
        return;
    }
    
    container.innerHTML = entries.map(entry => `
        <div class="module-item">
            <div class="module-info">
                <span class="module-code">${entry.module_code} </span>
                <span class="module-date">${formatDateTime(entry.occurred_at)}</span>
            </div>
            <button class="btn-icon" onclick="viewModule('${entry.id}')" title="Visualizza">
                👁️
            </button>
        </div>
    `).join('');
}

// Placeholder per visualizzazione modulo (implementeremo dopo)
function viewModule(moduleId) {
    window.location.href = `moduli/valutazione_infermieristica?view=${moduleId}`;
}

// Conferma eliminazione
function confirmDeleteDossier(dossierId) {
    if (confirm('Sei sicuro di voler eliminare questo dossier?\n\nQuesta operazione è reversibile (soft delete).')) {
        deleteDossier(dossierId);
    }
}

// Elimina dossier
async function deleteDossier(dossierId) {
    try {
        await apiCall(`${API_BASE}/dossiers/${dossierId}`, {
            method: 'DELETE'
        });
        
        showMessage('Dossier eliminato con successo', 'success');
        loadDossiers();
        
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

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT');
}

// Init
document.addEventListener('DOMContentLoaded', function() {
    requireAuth();
    loadDossiers();
});