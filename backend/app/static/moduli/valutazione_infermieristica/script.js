// static/moduli/valutazione_infermieristica/script.js
console.log("Modulo Valutazione Infermieristica caricato");

let MODE = 'create'; // 'create' o 'view'
let entryId = null;
let entryData = null;
let currentUser = null;
let allDossiers = [];
let selectedDossier = null;
let selectedPatient = null;


// Init
document.addEventListener('DOMContentLoaded', async function() {
    // Verifica autenticazione
    if (!TokenManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    // Determina modalità da URL
    const urlParams = new URLSearchParams(window.location.search);
    entryId = urlParams.get('id') || urlParams.get('view');
    
    if (entryId) {
        // MODALITÀ VISUALIZZAZIONE
        MODE = 'view';
        await initViewMode();
    } else {
        // MODALITÀ CREAZIONE
        MODE = 'create';
        await initCreateMode();
    }
});

async function initViewMode() {
    console.log('🔍 Modalità VISUALIZZAZIONE - Entry ID:', entryId);
    
    try {
        // Carica utente corrente
        currentUser = await apiCall(`${API_BASE}/users/me`);
        
        // Applica stile read-only
        applyViewMode();
        
        // Carica entry
        await loadEntry(entryId);
        
    } catch (error) {
        console.error('Errore init view mode:', error);
        showError('Errore nell\'inizializzazione: ' + error.message);
    }
}

async function loadEntry(id) {
    try {
        showLoading('Caricamento dati modulo...');
        
        // Chiama API
        const entry = await apiCall(`${API_BASE}/modules/entries/${id}`);
        
        entryData = entry;
        
        // Popola form
        populateFormFromEntry(entry);
        
        // Aggiorna UI
        updateHeaderForView(entry);
        
        hideLoading();
        
    } catch (error) {
        console.error('Errore caricamento entry:', error);
        hideLoading();
        
        if (error.message.includes('404')) {
            showError('Modulo non trovato');
        } else if (error.message.includes('403')) {
            showError('Non hai i permessi per visualizzare questo modulo');
        } else {
            showError('Errore nel caricamento: ' + error.message);
        }
    }
}

function applyViewMode() {
    // Aggiungi classe view-mode al container
    document.getElementById('moduleContainer').classList.add('view-mode');
    
    // Aggiorna titolo
    document.getElementById('pageTitle').textContent = '👁️ VISUALIZZA VALUTAZIONE INFERMIERISTICA';
    
    // Aggiungi badge
    document.getElementById('modeBadge').innerHTML = '<span class="badge badge-info">Solo Lettura</span>';
    
    // Disabilita tutti gli input, select, textarea
    const form = document.getElementById('moduleForm');
    const inputs = form.querySelectorAll('input:not([type="radio"]):not([type="checkbox"]), select, textarea');
    inputs.forEach(input => {
        input.setAttribute('readonly', 'readonly');
        input.setAttribute('disabled', 'disabled');
    });
    
    // Disabilita radio e checkbox
    const radios = form.querySelectorAll('input[type="radio"], input[type="checkbox"]');
    radios.forEach(radio => {
        radio.setAttribute('disabled', 'disabled');
    });
    
    // Rimuovi onsubmit
    form.onsubmit = (e) => {
        e.preventDefault();
        return false;
    };
}

function updateHeaderForView(entry) {
    document.getElementById('selectedDossierInfo').innerHTML = `
        <span class="badge badge-success">Modulo Compilato</span>
        <span class="badge badge-info">${entry.module_code} v${entry.schema_version}</span>
    `;
    
    // Popola info audit
    document.getElementById('audit_id').textContent = entry.id;
    document.getElementById('audit_module_code').textContent = entry.module_code;
    document.getElementById('audit_version').textContent = `v${entry.schema_version}`;
    document.getElementById('audit_created_at').textContent = formatDateTime(entry.created_at);
    document.getElementById('audit_created_by').textContent = entry.created_by_user_id || 'Sistema';
    document.getElementById('audit_updated_at').textContent = entry.updated_at ? formatDateTime(entry.updated_at) : 'Mai aggiornato';
}

// ============================================================
// INIT MODALITÀ CREAZIONE
// ============================================================

async function initCreateMode() {
    console.log('✏️ Modalità CREAZIONE');
    
    try {
        // Carica utente corrente
        currentUser = await apiCall(`${API_BASE}/users/me`);
        
        // Applica stile creazione
        applyCreateMode();
        
        // Mostra modal selezione dossier
        showDossierSelectionModal();
        
        // Setup campi condizionali
        setupConditionalFields();
        
    } catch (error) {
        console.error('Errore init create mode:', error);
        showError('Errore nell\'inizializzazione: ' + error.message);
    }
}

function applyCreateMode() {
    // Rimuovi classe view-mode (se presente)
    document.getElementById('moduleContainer').classList.remove('view-mode');
    
    // Aggiorna titolo
    document.getElementById('pageTitle').textContent = '✏️ COMPILA VALUTAZIONE INFERMIERISTICA';
    
    // Aggiungi badge
    document.getElementById('modeBadge').innerHTML = '<span class="badge badge-warning">Compilazione</span>';
}

// ============================================================
// POPOLAMENTO FORM (per modalità VIEW)
// ============================================================

function populateFormFromEntry(entry) {
    const data = entry.data;
    
    if (!data) {
        showError('Dati modulo non disponibili');
        return;
    }
    
    console.log('Popolamento form con dati:', data);
    
    // UTENTE
    if (data.utente) {
        setValue('inizNome', data.utente.inizNome);
        setValue('inizCognome', data.utente.inizCognome);
        setValue('dossier', data.utente.dossier);
        setRadioValue('struttura', data.utente.struttura);
    }
    
    // PAZIENTE
    if (data.paziente) {
        setValue('paziente_nominativo', data.paziente.paziente_nominativo);
        setValue('anno', data.paziente.anno);
        setValue('numero_progressivo', data.paziente.numero_progressivo);
        setValue('peso_kg', data.paziente.peso_kg);
        setValue('altezza_mt', data.paziente.altezza_mt);
        setValue('imc_kg_m2', data.paziente.imc_kg_m2);
    }
    
    // PARAMETRI VITALI
    if (data.rilievo_parametri_vitali) {
        const vitals = data.rilievo_parametri_vitali;
        setValue('frequenza_cardiaca_b_min', vitals.frequenza_cardiaca_b_min);
        setValue('temperatura_corporea_c', vitals.temperatura_corporea_c);
        setValue('pressione_arteriosa_mmhg', vitals.pressione_arteriosa_mmhg);
        setRadioValue('ecg', vitals.ecg ? 'si' : 'no');
        setValue('frequenza_respiratoria_atti_min', vitals.frequenza_respiratoria_atti_min);
        setValue('sato2', vitals.sato2);
        setValue('altro_parametri_vitali', vitals.altro_parametri_vitali);
    }
    
    // MODELLO PERCEZIONE
    if (data.modello_di_percezione_e_di_gestione_della_salute) {
        const modello = data.modello_di_percezione_e_di_gestione_della_salute;
        setRadioValue('consumo_tabacco', modello.consumo_tabacco ? 'si' : 'no');
        setValue('quantita_tabacco_die_numero_sigarette', modello.quantita_tabacco_die_numero_sigarette);
        setRadioValue('interrotto_consumo_tabacco', modello.interrotto_consumo_tabacco ? 'si' : 'no');
        setValue('data_interruzione_tabacco', modello.data_interruzione_tabacco);
        setRadioValue('consumo_alcolici', modello.consumo_alcolici ? 'si' : 'no');
        setValue('quantita_alcolici_die_cl', modello.quantita_alcolici_die_cl);
        setRadioValue('interrotto_consumo_alcolici', modello.interrotto_consumo_alcolici ? 'si' : 'no');
        setValue('data_interruzione_alcolici', modello.data_interruzione_alcolici);
    }
    
    // ALLERGIE
    if (data.allergie_riferite) {
        setValue('allergie_farmaci', data.allergie_riferite.farmaci);
        setValue('allergie_alimenti', data.allergie_riferite.alimenti);
        setValue('altro_allergie', data.allergie_riferite.altro_allergie);
    }
    
    // ATTIVITÀ
    setRadioValue('attivita_fisiche_sportive', data.attivita_fisiche_sportive ? 'si' : 'no');
    setRadioValue('patologie_croniche', data.patologie_croniche ? 'si' : 'no');
    setValue('quali_patologie_croniche', data.quali_patologie_croniche);
    
    // ANAMNESI
    if (data.anamnesi_ed_esame_obiettivo) {
        populateAnamnesi(data.anamnesi_ed_esame_obiettivo);
    }
    
    // TERAPIE
    setRadioValue('tao', data.tao ? 'si' : 'no');
    setRadioValue('ossigenoterapia', data.ossigenoterapia ? 'si' : 'no');
    setRadioValue('farmaci_h', data.farmaci_h ? 'si' : 'no');
    
    // DIAGNOSI
    if (data.diagnosi_infermieristica) {
        setValue('patologia_prevalente', data.diagnosi_infermieristica.patologia_prevalente);
        setValue('patologia_secondaria_1', data.diagnosi_infermieristica.patologia_secondaria_1);
        setValue('patologia_secondaria_2', data.diagnosi_infermieristica.patologia_secondaria_2);
    }
    
    // VALUTAZIONE
    setValue('valutazione_bisogni_infermieristici', data.valutazione_bisogni_infermieristici);
    setValue('cadenza_monitoraggio_clinico_parametri_vitali', data.cadenza_monitoraggio_clinico_parametri_vitali);
    setValue('patologie_da_monitorare', data.patologie_da_monitorare);
    
    // RISCHIO
    if (data.valutazione_del_rischio) {
        setRadioValue('rischio_cadute_scala_di_conley', data.valutazione_del_rischio.rischio_cadute_scala_di_conley);
        setRadioValue('rischio_infezioni_ica', data.valutazione_del_rischio.rischio_infezioni_ica);
    }
    
    setValue('scale_utilizzate', data.scale_utilizzate);
    
    // FIRMA
    setValue('data', data.data);
    setValue('infermiere_compilatore', data.infermiere_compilatore);
    setValue('firma', data.firma);
}

function populateAnamnesi(anamnesi) {
    // COMUNICAZIONE
    if (anamnesi.comunicazione) {
        const com = anamnesi.comunicazione;
        setCheckboxValues('stato_coscienza', com.stato_di_coscienza);
        setCheckboxValues('comunicazione', com.comunicazione);
        setCheckboxValues('udito', com.udito);
        setRadioValue('sordita_lato', com.sordita_lato);
        setCheckbox('protesi_udito', com.protesi_udito);
        setRadioValue('protesi_udito_lato', com.protesi_udito_lato);
        setCheckboxValues('vista', com.vista);
        setCheckboxValues('protesi_vista', com.protesi_vista);
        setCheckboxValues('condizioni_psichiche', com.condizioni_psichiche);
    }
    
    // RESPIRAZIONE
    if (anamnesi.respirazione) {
        const resp = anamnesi.respirazione;
        setRadioValue('tipologia_respirazione', resp.tipologia);
        setCheckboxValues('dispnea_tipo', resp.dispnea_tipo);
        setRadioValue('presenza_di_tosse', resp.presenza_di_tosse ? 'si' : 'no');
        setRadioValue('trattamento_o2', resp.trattamento_o2 ? 'si' : 'no');
        setValue('ossigenoterapia_l_min', resp.ossigenoterapia_l_min);
        setRadioValue('aspirazioni_secrezioni', resp.aspirazioni_secrezioni ? 'si' : 'no');
        setCheckboxValues('allergie_respirazione', resp.allergie_respirazione);
        setCheckboxValues('presidi_respirazione', resp.presidi_respirazione);
    }
    
    // CIRCOLAZIONE
    if (anamnesi.circolazione_e_tessuti_cutanei) {
        const circ = anamnesi.circolazione_e_tessuti_cutanei;
        setCheckboxValues('presidi_protesi', circ.presidi_protesi);
        setValue('altro_presidi_protesi', circ.altro_presidi_protesi);
        setCheckboxValues('cute_mucose', circ.cute_mucose);
        setCheckboxValues('integrita_cutanea', circ.integrita_cutanea);
        setValue('presenza_lesioni_da_decubito_sede', circ.presenza_lesioni_da_decubito_sede);
        setRadioValue('stadio_lesioni_da_decubito', circ.stadio_lesioni_da_decubito);
        setRadioValue('rischio_lesioni_scala_braden', circ.rischio_lesioni_scala_braden);
    }
    
    // STATO
    if (anamnesi.stato) {
        const stato = anamnesi.stato;
        setRadioValue('escursione_articolare', stato.escursione_articolare);
        setValue('altro_escursione_articolare', stato.altro_escursione_articolare);
        setRadioValue('presa_mani', stato.presa_delle_mani);
        setRadioValue('debolezza_mani_lato', stato.debolezza_mani_lato);
        setRadioValue('paralisi_mani_lato', stato.paralisi_mani_lato);
        setRadioValue('presa_arti_inferiori', stato.presa_arti_inferiori);
        setRadioValue('debolezza_arti_inferiori_lato', stato.debolezza_arti_inferiori_lato);
        setRadioValue('paralisi_arti_inferiori_lato', stato.paralisi_arti_inferiori_lato);
        setCheckbox('depressione', stato.depressione);
        setRadioValue('ansia', stato.ansia);
        setCheckbox('agitazione', stato.agitazione);
        setCheckboxValues('riposo_sonno', stato.riposo_sonno);
        setCheckboxValues('tipo_dolore', stato.tipo_dolore);
        setValue('sede_dolore_acuto', stato.sede_dolore_acuto);
        setValue('sede_dolore_cronico', stato.sede_dolore_cronico);
        setCheckboxValues('caratteristiche_dolore', stato.caratteristiche_dolore);
        setCheckboxValues('terapia_antidolorifica', stato.terapia_antidolorifica);
    }
    
    // MOVIMENTO IGIENE
    if (anamnesi.movimento_igiene) {
        const mov = anamnesi.movimento_igiene;
        setRadioValue('autonomia_movimento', mov.autonomia_movimento);
        setRadioValue('rischio_cadute_conley', mov.rischio_cadute_conley);
        setCheckboxValues('ausili_presidi_movimento', mov.ausili_presidi_movimento);
        setRadioValue('autonomia_postura', mov.autonomia_postura);
        setCheckboxValues('postura_obbligata_causa', mov.postura_obbligata_causa);
        setCheckboxValues('ausili_presidi_postura', mov.ausili_presidi_postura);
        setValue('altro_ausili_presidi_postura', mov.altro_ausili_presidi_postura);
        setRadioValue('lavarsi', mov.lavarsi);
        setRadioValue('vestirsi', mov.vestirsi);
        setRadioValue('autonomia_wc', mov.autonomia_wc);
        setValue('altro_uso_wc', mov.altro_uso_wc);
        setRadioValue('autonomia_doccia', mov.autonomia_doccia);
    }
    
    // ELIMINAZIONE INTESTINALE
    if (anamnesi.eliminazione_intestinale) {
        const eli = anamnesi.eliminazione_intestinale;
        setRadioValue('grado_autonomia_intestinale', eli.grado_autonomia);
        setValue('frequenza_evacuazioni_n', eli.frequenza_evacuazioni_n);
        setValue('data_utlima_evacuazione', eli.data_utlima_evacuazione);
        setRadioValue('consistenza', eli.consistenza);
        setRadioValue('colore_intestinale', eli.colore);
        setRadioValue('presidi_intestinale', eli.presidi);
    }
    
    // ELIMINAZIONE VESCICALE
    if (anamnesi.eliminazione_vescicale_urinaria) {
        const ves = anamnesi.eliminazione_vescicale_urinaria;
        setRadioValue('grado_autonomia_urinaria', ves.grado_autonomia);
        setRadioValue('incontinente_tipo', ves.incontinente_tipo);
        setRadioValue('minzione', ves.minzione);
        setValue('frequenza_die', ves.frequenza_die);
        setValue('diuresi_ml_24ore', ves.diuresi_ml_24ore);
        setRadioValue('diuresi_regolarita', ves.diuresi_regolarita);
        setRadioValue('caratteristiche_urinarie', ves.caratteristiche);
        setRadioValue('presidi_urinaria', ves.presidi_urinaria);
        setValue('stomia_tipo', ves.stomia_tipo);
        setRadioValue('infezioni_urinarie', ves.infezioni_urinarie ? 'si' : 'no');
        setValue('se_si_specificare_segni_e_sintomi', ves.se_si_specificare_segni_e_sintomi);
    }
    
    // ALIMENTAZIONE
    if (anamnesi.alimentazione_e_idratazione) {
        const alim = anamnesi.alimentazione_e_idratazione;
        setRadioValue('autonomia_alimentazione', alim.autonomia);
        setRadioValue('deglutizione', alim.deglutizione);
        setCheckboxValues('protesi_alimentazione', alim.protesi);
        setCheckboxValues('presidi_alimentazione', alim.presidi);
        setValue('altro_presidi_alimentazione', alim.altro_presidi);
        setRadioValue('dieta', alim.dieta);
        setValue('dieta_speciale_specifica', alim.dieta_speciale_specifica);
        setValue('restrizioni_dietetiche', alim.restrizioni_dietetiche);
        setValue('intolleranze', alim.intolleranze);
        setValue('allergie_alimentazione', alim.allergie);
        setRadioValue('cavo_orale', alim.cavo_orale);
        setValue('altro_cavo_orale', alim.altro_cavo_orale);
        setRadioValue('stato_nutrizionale_scala_mna', alim.stato_nutrizionale_scala_mna);
        setValue('variazioni_peso_ultimi_mesi', alim.variazioni_peso_ultimi_mesi);
        setValue('variazione_peso_kg', alim.variazione_peso_kg);
        setRadioValue('tipo_variazione_peso', alim.tipo_variazione_peso);
        setValue('peso_kg_alimentazione', alim.peso_kg);
        setValue('altezza_mt_alimentazione', alim.altezza_mt);
        setValue('imc', alim.imc);
        setRadioValue('grado_obesita', alim.grado_obesita);
        setCheckboxValues('presenza_di', alim.presenza_di);
        setCheckboxValues('addome', alim.addome);
        setRadioValue('idratazione_stato', alim.idratazione_stato);
        setRadioValue('idratazione_autonomia', alim.idratazione_autonomia);
    }
}

// === SELEZIONE DOSSIER ===

async function showDossierSelectionModal() {
    document.getElementById('dossierSelectionModal').classList.add('show');
    await loadDossiers();
}

async function loadDossiers() {
    try {
        const data = await apiCall(`${API_BASE}/dossiers?page_size=100`);
        allDossiers = data.items;
        
        // Carica anche i pazienti per mostrare i nomi
        for (const dossier of allDossiers) {
            try {
                const patient = await apiCall(`${API_BASE}/patients/${dossier.patient_id}`);
                dossier.patient = patient;
            } catch (error) {
                console.error('Errore caricamento paziente:', error);
            }
        }
        
        renderDossiersList(allDossiers);
    } catch (error) {
        console.error('Errore caricamento dossiers:', error);
        alert('Errore nel caricamento dei dossiers');
    }
}

function renderDossiersList(dossiers) {
    const list = document.getElementById('dossiersList');
    
    if (dossiers.length === 0) {
        list.innerHTML = '<div style="padding: 20px; text-align: center; color: #6b7280;">Nessun dossier attivo trovato</div>';
        return;
    }
    
    list.innerHTML = dossiers.map(dossier => `
        <div class="select-item" onclick="selectDossier('${dossier.id}')">
            <div class="patient-info">
                <span class="patient-name">
                    ${dossier.patient ? `${dossier.patient.first_name} ${dossier.patient.last_name}` : 'Caricamento...'}
                </span>
                <span class="patient-cf">
                    Dossier: ${dossier.id.substring(0, 8)}... | 
                    Ammissione: ${formatDate(dossier.admission_date)} | 
                    Care Level: ${dossier.care_level}
                </span>
            </div>
        </div>
    `).join('');
}

function searchDossiers() {
    const query = document.getElementById('dossierSearch').value.toLowerCase();
    const filtered = allDossiers.filter(d => {
        if (!d.patient) return false;
        const patientName = `${d.patient.first_name} ${d.patient.last_name}`.toLowerCase();
        const cf = d.patient.fiscal_code.toLowerCase();
        return patientName.includes(query) || cf.includes(query);
    });
    renderDossiersList(filtered);
}

async function selectDossier(dossierId) {
    try {
        // Carica dossier completo
        selectedDossier = await apiCall(`${API_BASE}/dossiers/${dossierId}?include_patient=true`);
        selectedPatient = selectedDossier.patient;
        
        // Chiudi modal
        document.getElementById('dossierSelectionModal').classList.remove('show');
        
        // Precompila form
        prefillFormForCreate();
        
    } catch (error) {
        console.error('Errore selezione dossier:', error);
        alert('Errore nella selezione del dossier');
    }
}

// === PRECOMPILAZIONE FORM ===

function prefillFormForCreate() {
    if (!selectedPatient || !selectedDossier || !currentUser) return;
    
    document.getElementById('inizNome').value = currentUser.first_name.substring(0, 1).toUpperCase();
    document.getElementById('inizCognome').value = currentUser.last_name.substring(0, 1).toUpperCase();
    document.getElementById('dossier').value = selectedDossier.id;
    
    const strutturaRadios = document.getElementsByName('struttura');
    strutturaRadios.forEach(radio => {
        if (radio.value === selectedDossier.care_level) {
            radio.checked = true;
        }
    });
    
    const nominativo = `${selectedPatient.first_name} ${selectedPatient.last_name}`;
    document.getElementById('paziente_nominativo').value = nominativo;
    
    const today = new Date();
    document.getElementById('anno').value = today.getFullYear();
    document.getElementById('numero_progressivo').value = 1;
    document.getElementById('data').value = today.toISOString().split('T')[0];
    document.getElementById('infermiere_compilatore').value = `${currentUser.first_name} ${currentUser.last_name}`;
    
    document.getElementById('selectedDossierInfo').innerHTML = `
        <strong>Dossier selezionato:</strong> ${nominativo} - 
        Care Level: ${selectedDossier.care_level} - 
        Ammissione: ${formatDate(selectedDossier.admission_date)}
    `;
}

// === GESTIONE CAMPI CONDIZIONALI ===

function setupConditionalFields() {
    // Sordità
    const uditoSordita = document.getElementById('udito_sordita');
    if (uditoSordita) {
        uditoSordita.addEventListener('change', function(e) {
            const field = document.getElementById('sordita_lato_field');
            if (field) field.style.display = e.target.checked ? 'inline' : 'none';
        });
    }
    
    // Protesi udito
    const protesiUdito = document.getElementById('protesi_udito');
    if (protesiUdito) {
        protesiUdito.addEventListener('change', function(e) {
            const field = document.getElementById('protesi_udito_lato_field');
            if (field) field.style.display = e.target.checked ? 'inline' : 'none';
        });
    }
    
    // Dispnea
    const tipologiaEupnea = document.getElementById('tipologia_eupnea');
    const tipologiaDispnea = document.getElementById('tipologia_dispnea');
    const dispneaTipoField = document.getElementById('dispnea_tipo_field');
    
    if (tipologiaEupnea && dispneaTipoField) {
        tipologiaEupnea.addEventListener('change', function() {
            dispneaTipoField.style.display = 'none';
        });
    }
    
    if (tipologiaDispnea && dispneaTipoField) {
        tipologiaDispnea.addEventListener('change', function() {
            dispneaTipoField.style.display = 'block';
        });
    }
    
    // Escursione articolare
    const escursioneCompleta = document.getElementById('escursione_articolare_completa');
    const escursioneAltro = document.getElementById('escursione_articolare_altro');
    const altroEscursioneField = document.getElementById('altro_escursione_articolare');
    
    if (escursioneCompleta && altroEscursioneField) {
        escursioneCompleta.addEventListener('change', function() {
            altroEscursioneField.style.display = 'none';
        });
    }
    
    if (escursioneAltro && altroEscursioneField) {
        escursioneAltro.addEventListener('change', function() {
            altroEscursioneField.style.display = 'inline';
        });
    }
    
    // Presa mani
    const presaManiRadios = document.getElementsByName('presa_mani');
    presaManiRadios.forEach(radio => {
        radio.addEventListener('change', function(e) {
            const debolezzaField = document.getElementById('debolezza_mani_lato_field');
            const paralisiField = document.getElementById('paralisi_mani_lato_field');
            
            if (debolezzaField) debolezzaField.style.display = 'none';
            if (paralisiField) paralisiField.style.display = 'none';
            
            if (e.target.value === 'debolezza' && debolezzaField) {
                debolezzaField.style.display = 'inline';
            } else if (e.target.value === 'paralisi' && paralisiField) {
                paralisiField.style.display = 'inline';
            }
        });
    });
    
    // Presa arti inferiori
    const presaArtiRadios = document.getElementsByName('presa_arti_inferiori');
    presaArtiRadios.forEach(radio => {
        radio.addEventListener('change', function(e) {
            const debolezzaField = document.getElementById('debolezza_arti_inferiori_lato_field');
            const paralisiField = document.getElementById('paralisi_arti_inferiori_lato_field');
            
            if (debolezzaField) debolezzaField.style.display = 'none';
            if (paralisiField) paralisiField.style.display = 'none';
            
            if (e.target.value === 'debolezza' && debolezzaField) {
                debolezzaField.style.display = 'inline';
            } else if (e.target.value === 'paralisi' && paralisiField) {
                paralisiField.style.display = 'inline';
            }
        });
    });
    
    // Dolore acuto
    const tipoDoloreAcuto = document.getElementById('tipo_dolore_acuto');
    const sedeDoloreAcuto = document.getElementById('sede_dolore_acuto');
    if (tipoDoloreAcuto && sedeDoloreAcuto) {
        tipoDoloreAcuto.addEventListener('change', function(e) {
            sedeDoloreAcuto.style.display = e.target.checked ? 'inline' : 'none';
        });
    }
    
    // Dolore cronico
    const tipoDoloreCronico = document.getElementById('tipo_dolore_cronico');
    const sedeDoloreCronico = document.getElementById('sede_dolore_cronico');
    if (tipoDoloreCronico && sedeDoloreCronico) {
        tipoDoloreCronico.addEventListener('change', function(e) {
            sedeDoloreCronico.style.display = e.target.checked ? 'inline' : 'none';
        });
    }
    
    // Incontinente
    const gradoAutonomiaIncontinente = document.getElementById('grado_autonomia_urinaria_incontinente');
    const incontinenteTipoField = document.getElementById('incontinente_tipo_field');
    if (gradoAutonomiaIncontinente && incontinenteTipoField) {
        gradoAutonomiaIncontinente.addEventListener('change', function() {
            incontinenteTipoField.style.display = 'block';
        });
    }
    
    const autonomoRadios = document.getElementsByName('grado_autonomia_urinaria');
    autonomoRadios.forEach(radio => {
        if (radio.value !== 'incontinente') {
            radio.addEventListener('change', function() {
                if (incontinenteTipoField) incontinenteTipoField.style.display = 'none';
            });
        }
    });
    
    // Patologie croniche
    const patologieCronicheSi = document.getElementById('patologie_croniche_si');
    const qualiPatologieField = document.getElementById('quali_patologie_croniche');
    if (patologieCronicheSi && qualiPatologieField) {
        patologieCronicheSi.addEventListener('change', function() {
            qualiPatologieField.closest('.activity-field').style.display = 'flex';
        });
    }
    
    const patologieCronicheNo = document.getElementsByName('patologie_croniche')[0];
    if (patologieCronicheNo && qualiPatologieField) {
        patologieCronicheNo.addEventListener('change', function() {
            qualiPatologieField.closest('.activity-field').style.display = 'none';
        });
    }
}

// === SALVATAGGIO ===

async function saveModule(event) {
    event.preventDefault();
    
    if (MODE !== 'create') {
        return false;
    }
    
    if (!selectedDossier) {
        alert('Seleziona prima un dossier');
        return false;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('span:not(.spinner)');
    const btnSpinner = submitBtn.querySelector('.spinner');
    
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    try {
        const formData = collectFormData();
        
        // Validazione base
        if (!formData.data) {
            throw new Error('Inserisci la data di compilazione');
        }
        
        if (!formData.infermiere_compilatore) {
            throw new Error('Inserisci il nome del compilatore');
        }
        
        if (!formData.firma) {
            throw new Error('Inserisci la firma');
        }
        
        const entryPayload = {
            dossier_id: selectedDossier.id,
            module_code: "ROG26/1.4",
            schema_version: 1,
            occurred_at: formData.data ? new Date(formData.data).toISOString() : new Date().toISOString(),
            data: formData
        };
        
        const response = await apiCall(`${API_BASE}/modules/entries`, {
            method: 'POST',
            body: JSON.stringify(entryPayload)
        });
        
        showSuccessMessage('Valutazione infermieristica salvata con successo!');
        
        setTimeout(() => {
            if (confirm('Vuoi compilare un altro modulo?')) {
                document.getElementById('moduleForm').reset();
                showDossierSelectionModal();
            } else {
                goBack();
            }
        }, 1500);
        
    } catch (error) {
        console.error('Errore salvataggio:', error);
        
        let errorMessage = 'Errore nel salvataggio del modulo';
        
        if (error.message.includes('validation')) {
            errorMessage = 'Errore di validazione dei dati. Controlla i campi compilati.';
        } else if (error.message.includes('permission') || error.message.includes('403')) {
            errorMessage = 'Non hai i permessi per creare questo modulo.';
        } else if (error.message.includes('404')) {
            errorMessage = 'Dossier o modulo non trovato.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showErrorMessage(errorMessage);
        
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
    
    return false;
}

function showSuccessMessage(message) {
    const alertDiv = document.getElementById('alert');
    if (!alertDiv) return;
    
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = '✅ ' + message;
    alertDiv.style.display = 'block';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showErrorMessage(message) {
    const alertDiv = document.getElementById('alert');
    if (!alertDiv) return;
    
    alertDiv.className = 'alert alert-error';
    alertDiv.textContent = '❌ ' + message;
    alertDiv.style.display = 'block';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 10000);
}

function collectFormData() {
    const form = document.getElementById('moduleForm');
    const formData = new FormData(form);
    
    // Helper per raccogliere checkbox multipli
    const getCheckboxValues = (name) => {
        return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
            .map(cb => cb.value);
    };
    
    // Helper per valori radio
    const getRadioValue = (name) => {
        const radio = document.querySelector(`input[name="${name}"]:checked`);
        return radio ? radio.value : null;
    };
    
    // Helper per convertire valori numerici
    const parseNumber = (value) => {
        if (!value || value === '') return null;
        const num = parseFloat(value);
        return isNaN(num) ? null : num;
    };
    
    const parseIntSafe = (value) => {
        if (!value || value === '') return null;
        const num = Number.parseInt(value);
        return isNaN(num) ? null : num;
    };
    
    // Costruisci oggetto dati
    const data = {
        utente: {
            inizNome: formData.get('inizNome') || '',
            inizCognome: formData.get('inizCognome') || '',
            dossier: formData.get('dossier') || '',
            struttura: getRadioValue('struttura') || 'R3'
        },
        paziente: {
            paziente_nominativo: formData.get('paziente_nominativo') || '',
            anno: parseIntSafe(formData.get('anno')) || new Date().getFullYear(),
            numero_progressivo: parseIntSafe(formData.get('numero_progressivo')) || 1,
            peso_kg: parseNumber(formData.get('peso_kg')),
            altezza_mt: parseNumber(formData.get('altezza_mt')),
            imc_kg_m2: parseNumber(formData.get('imc_kg_m2'))
        },
        rilievo_parametri_vitali: {
            frequenza_cardiaca_b_min: parseIntSafe(formData.get('frequenza_cardiaca_b_min')),
            temperatura_corporea_c: parseNumber(formData.get('temperatura_corporea_c')),
            pressione_arteriosa_mmhg: formData.get('pressione_arteriosa_mmhg') || null,
            ecg: getRadioValue('ecg') === 'si',
            frequenza_respiratoria_atti_min: parseIntSafe(formData.get('frequenza_respiratoria_atti_min')),
            sato2: parseNumber(formData.get('sato2')),
            altro_parametri_vitali: formData.get('altro_parametri_vitali') || null
        },
        modello_di_percezione_e_di_gestione_della_salute: {
            consumo_tabacco: getRadioValue('consumo_tabacco') === 'si',
            quantita_tabacco_die_numero_sigarette: parseIntSafe(formData.get('quantita_tabacco_die_numero_sigarette')),
            interrotto_consumo_tabacco: getRadioValue('interrotto_consumo_tabacco') === 'si',
            data_interruzione_tabacco: formData.get('data_interruzione_tabacco') || null,
            consumo_alcolici: getRadioValue('consumo_alcolici') === 'si',
            quantita_alcolici_die_cl: parseIntSafe(formData.get('quantita_alcolici_die_cl')),
            interrotto_consumo_alcolici: getRadioValue('interrotto_consumo_alcolici') === 'si',
            data_interruzione_alcolici: formData.get('data_interruzione_alcolici') || null
        },
        allergie_riferite: {
            farmaci: formData.get('allergie_farmaci') || null,
            alimenti: formData.get('allergie_alimenti') || null,
            altro_allergie: formData.get('altro_allergie') || null
        },
        attivita_fisiche_sportive: getRadioValue('attivita_fisiche_sportive') === 'si',
        patologie_croniche: getRadioValue('patologie_croniche') === 'si',
        quali_patologie_croniche: formData.get('quali_patologie_croniche') || null,
        
        anamnesi_ed_esame_obiettivo: {
            comunicazione: {
                stato_di_coscienza: getCheckboxValues('stato_coscienza'),
                comunicazione: getCheckboxValues('comunicazione'),
                udito: getCheckboxValues('udito'),
                sordita_lato: getRadioValue('sordita_lato'),
                protesi_udito: document.getElementById('protesi_udito')?.checked || false,
                protesi_udito_lato: getRadioValue('protesi_udito_lato'),
                vista: getCheckboxValues('vista'),
                protesi_vista: getCheckboxValues('protesi_vista'),
                condizioni_psichiche: getCheckboxValues('condizioni_psichiche')
            },
            respirazione: {
                tipologia: getRadioValue('tipologia_respirazione'),
                dispnea_tipo: getCheckboxValues('dispnea_tipo'),
                presenza_di_tosse: getRadioValue('presenza_di_tosse') === 'si',
                trattamento_o2: getRadioValue('trattamento_o2') === 'si',
                ossigenoterapia_l_min: parseNumber(formData.get('ossigenoterapia_l_min')),
                aspirazioni_secrezioni: getRadioValue('aspirazioni_secrezioni') === 'si',
                allergie_respirazione: getCheckboxValues('allergie_respirazione'),
                presidi_respirazione: getCheckboxValues('presidi_respirazione')
            },
            circolazione_e_tessuti_cutanei: {
                presidi_protesi: getCheckboxValues('presidi_protesi'),
                altro_presidi_protesi: formData.get('altro_presidi_protesi') || null,
                cute_mucose: getCheckboxValues('cute_mucose'),
                integrita_cutanea: getCheckboxValues('integrita_cutanea'),
                presenza_lesioni_da_decubito_sede: formData.get('presenza_lesioni_da_decubito_sede') || null,
                stadio_lesioni_da_decubito: getRadioValue('stadio_lesioni_da_decubito'),
                rischio_lesioni_scala_braden: getRadioValue('rischio_lesioni_scala_braden')
            },
            stato: {
                escursione_articolare: getRadioValue('escursione_articolare'),
                altro_escursione_articolare: formData.get('altro_escursione_articolare') || null,
                presa_delle_mani: getRadioValue('presa_mani'),
                debolezza_mani_lato: getRadioValue('debolezza_mani_lato'),
                paralisi_mani_lato: getRadioValue('paralisi_mani_lato'),
                presa_arti_inferiori: getRadioValue('presa_arti_inferiori'),
                debolezza_arti_inferiori_lato: getRadioValue('debolezza_arti_inferiori_lato'),
                paralisi_arti_inferiori_lato: getRadioValue('paralisi_arti_inferiori_lato'),
                depressione: document.querySelector('input[name="depressione"]')?.checked || false,
                ansia: getRadioValue('ansia'),
                agitazione: document.querySelector('input[name="agitazione"]')?.checked || false,
                riposo_sonno: getCheckboxValues('riposo_sonno'),
                tipo_dolore: getCheckboxValues('tipo_dolore'),
                sede_dolore_acuto: formData.get('sede_dolore_acuto') || null,
                sede_dolore_cronico: formData.get('sede_dolore_cronico') || null,
                caratteristiche_dolore: getCheckboxValues('caratteristiche_dolore'),
                terapia_antidolorifica: getCheckboxValues('terapia_antidolorifica')
            },
            movimento_igiene: {
                autonomia_movimento: getRadioValue('autonomia_movimento'),
                rischio_cadute_conley: getRadioValue('rischio_cadute_conley'),
                ausili_presidi_movimento: getCheckboxValues('ausili_presidi_movimento'),
                autonomia_postura: getRadioValue('autonomia_postura'),
                postura_obbligata_causa: getCheckboxValues('postura_obbligata_causa'),
                ausili_presidi_postura: getCheckboxValues('ausili_presidi_postura'),
                altro_ausili_presidi_postura: formData.get('altro_ausili_presidi_postura') || null,
                lavarsi: getRadioValue('lavarsi'),
                vestirsi: getRadioValue('vestirsi'),
                autonomia_wc: getRadioValue('autonomia_wc'),
                altro_uso_wc: formData.get('altro_uso_wc') || null,
                autonomia_doccia: getRadioValue('autonomia_doccia')
            },
            eliminazione_intestinale: {
                grado_autonomia: getRadioValue('grado_autonomia_intestinale'),
                frequenza_evacuazioni_n: parseIntSafe(formData.get('frequenza_evacuazioni_n')),
                data_utlima_evacuazione: formData.get('data_utlima_evacuazione') || null,
                consistenza: getRadioValue('consistenza'),
                colore: getRadioValue('colore_intestinale'),
                presidi: getRadioValue('presidi_intestinale')
            },
            eliminazione_vescicale_urinaria: {
                grado_autonomia: getRadioValue('grado_autonomia_urinaria'),
                incontinente_tipo: getRadioValue('incontinente_tipo'),
                minzione: getRadioValue('minzione'),
                frequenza_die: parseIntSafe(formData.get('frequenza_die')),
                diuresi_ml_24ore: parseIntSafe(formData.get('diuresi_ml_24ore')),
                diuresi_regolarita: getRadioValue('diuresi_regolarita'),
                caratteristiche: getRadioValue('caratteristiche_urinarie'),
                presidi_urinaria: getRadioValue('presidi_urinaria'),
                stomia_tipo: formData.get('stomia_tipo') || null,
                infezioni_urinarie: getRadioValue('infezioni_urinarie') === 'si',
                se_si_specificare_segni_e_sintomi: formData.get('se_si_specificare_segni_e_sintomi') || null
            },
            alimentazione_e_idratazione: {
                autonomia: getRadioValue('autonomia_alimentazione'),
                deglutizione: getRadioValue('deglutizione'),
                protesi: getCheckboxValues('protesi_alimentazione'),
                presidi: getCheckboxValues('presidi_alimentazione'),
                altro_presidi: formData.get('altro_presidi_alimentazione') || null,
                dieta: getRadioValue('dieta'),
                dieta_speciale_specifica: formData.get('dieta_speciale_specifica') || null,
                restrizioni_dietetiche: formData.get('restrizioni_dietetiche') || null,
                intolleranze: formData.get('intolleranze') || null,
                allergie: formData.get('allergie_alimentazione') || null,
                cavo_orale: getRadioValue('cavo_orale'),
                altro_cavo_orale: formData.get('altro_cavo_orale') || null,
                stato_nutrizionale_scala_mna: getRadioValue('stato_nutrizionale_scala_mna'),
                variazioni_peso_ultimi_mesi: parseIntSafe(formData.get('variazioni_peso_ultimi_mesi')),
                variazione_peso_kg: parseNumber(formData.get('variazione_peso_kg')),
                tipo_variazione_peso: formData.get('tipo_variazione_peso') || null,
                peso_kg: parseNumber(formData.get('peso_kg_alimentazione')),
                altezza_mt: parseNumber(formData.get('altezza_mt_alimentazione')),
                imc: parseNumber(formData.get('imc')),
                grado_obesita: getRadioValue('grado_obesita'),
                presenza_di: getCheckboxValues('presenza_di'),
                addome: getCheckboxValues('addome'),
                idratazione_stato: getRadioValue('idratazione_stato'),
                idratazione_autonomia: getRadioValue('idratazione_autonomia')
            }
        },
        
        tao: getRadioValue('tao') === 'si',
        ossigenoterapia: getRadioValue('ossigenoterapia') === 'si',
        farmaci_h: getRadioValue('farmaci_h') === 'si',
        
        diagnosi_infermieristica: {
            patologia_prevalente: formData.get('patologia_prevalente') || null,
            patologia_secondaria_1: formData.get('patologia_secondaria_1') || null,
            patologia_secondaria_2: formData.get('patologia_secondaria_2') || null
        },
        
        valutazione_bisogni_infermieristici: formData.get('valutazione_bisogni_infermieristici') || null,
        cadenza_monitoraggio_clinico_parametri_vitali: formData.get('cadenza_monitoraggio_clinico_parametri_vitali') || null,
        patologie_da_monitorare: formData.get('patologie_da_monitorare') || null,
        
        valutazione_del_rischio: {
            rischio_cadute_scala_di_conley: getRadioValue('rischio_cadute_scala_di_conley'),
            rischio_infezioni_ica: getRadioValue('rischio_infezioni_ica')
        },
        
        scale_utilizzate: formData.get('scale_utilizzate') || null,
        
        data: formData.get('data') || null,
        infermiere_compilatore: formData.get('infermiere_compilatore') || null,
        firma: formData.get('firma') || null
    };
    
    return data;
}


// ============================================================
// HELPER FUNCTIONS
// ============================================================

function setValue(id, value) {
    const element = document.getElementById(id);
    if (element && value !== null && value !== undefined) {
        element.value = value;
    }
}

function setRadioValue(name, value) {
    if (!value) return;
    const radios = document.getElementsByName(name);
    for (const radio of radios) {
        if (radio.value === value || radio.value === String(value)) {
            radio.checked = true;
            break;
        }
    }
}

function setCheckboxValues(name, values) {
    if (!values || !Array.isArray(values)) return;
    
    const checkboxes = document.querySelectorAll(`input[name="${name}"]`);
    checkboxes.forEach(cb => {
        cb.checked = values.includes(cb.value);
    });
}

function setCheckbox(id, checked) {
    const element = document.getElementById(id);
    if (element) {
        element.checked = !!checked;
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
}

function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT');
}

function showLoading(text = 'Caricamento...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('show');
}

function showSuccessMessage(message) {
    const alertDiv = document.getElementById('alert');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = '✅ ' + message;
    alertDiv.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showErrorMessage(message) {
    const alertDiv = document.getElementById('alert');
    alertDiv.className = 'alert alert-error';
    alertDiv.textContent = '❌ ' + message;
    alertDiv.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 10000);
}

function showError(message) {
    showErrorMessage(message);
}

// ============================================================
// AZIONI UI
// ============================================================

function goBack() {
    if (MODE === 'view') {
        // Torna alla lista
        window.location.href = 'lista_moduli.html';
    } else {
        // Torna alla dashboard
        window.location.href = '/dashboard';
    }
}

function printModule() {
    window.print();
}

function downloadPDF() {
    alert('Funzionalità download PDF in sviluppo');
}



// Utility
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
}

// API helper
const API_BASE = '/api/v1';
const TokenManager = {
    get: () => localStorage.getItem('access_token'),
    set: (token) => localStorage.setItem('access_token', token),
    remove: () => localStorage.removeItem('access_token'),
    isAuthenticated: () => !!localStorage.getItem('access_token')
};

async function apiCall(url, options = {}) {
    const token = TokenManager.get();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token && !options.skipAuth) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.detail || 'Errore nella richiesta');
    }
    
    return data;
}