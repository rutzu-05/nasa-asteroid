/**
 * NASA JPL Asteroid Prospector - Frontend Client Logic
 * Prospección Minera & Targeting de Misiones Espaciales con Random Forest
 * Sistema de Diseño Material 3 - 100% Libre de Colores Neón
 */

// Presets de misiones reales de la NASA
const ASTEROID_PRESETS = {
  psyche: {
    nombre: '16 Psyche',
    H: 5.90,
    albedo: 0.120,
    diameter: 226.0,
    a: 2.924,
    e: 0.134,
    i: 3.09,
    q: 2.532,
    rot: 4.196
  },
  bennu: {
    nombre: '101955 Bennu (OSIRIS-REx)',
    H: 20.60,
    albedo: 0.046,
    diameter: 0.492,
    a: 1.126,
    e: 0.203,
    i: 6.03,
    q: 0.897,
    rot: 4.296
  },
  vesta: {
    nombre: '4 Vesta (Misión Dawn)',
    H: 3.20,
    albedo: 0.423,
    diameter: 525.4,
    a: 2.361,
    e: 0.089,
    i: 7.14,
    q: 2.151,
    rot: 5.342
  },
  eros: {
    nombre: '433 Eros (Misión NEAR)',
    H: 11.16,
    albedo: 0.250,
    diameter: 16.84,
    a: 1.458,
    e: 0.223,
    i: 10.83,
    q: 1.133,
    rot: 5.270
  }
};

document.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  setupDynamicHelpers();
  setupFormValidationAndSubmit();
  setupBatchProcessing();
});

// 1. Verificación de Salud del API
async function checkApiHealth() {
  const dot = document.getElementById('api-status-dot');
  const text = document.getElementById('api-status-text');

  try {
    const res = await fetch('/api/v1/health');
    if (res.ok) {
      dot.className = 'w-2 h-2 rounded-full bg-emerald-600';
      text.innerText = 'JPL Random Forest: Online';
      text.className = 'text-emerald-800 font-mono text-[11px] font-medium';
    } else {
      throw new Error('Health check error');
    }
  } catch (err) {
    dot.className = 'w-2 h-2 rounded-full bg-red-600';
    text.innerText = 'Servidor Desconectado';
    text.className = 'text-red-700 font-mono text-[11px] font-medium';
  }
}

// 2. Cargar Presets de Misiones
function loadAsteroidPreset(key) {
  const data = ASTEROID_PRESETS[key];
  if (!data) return;

  document.getElementById('magnitud_absoluta_H').value = data.H;
  document.getElementById('albedo_geometrico').value = data.albedo;
  document.getElementById('diametro_km').value = data.diameter;
  document.getElementById('semieje_mayor_au').value = data.a;
  document.getElementById('excentricidad').value = data.e;
  document.getElementById('inclinacion_grados').value = data.i;
  document.getElementById('distancia_perihelio_au').value = data.q;
  document.getElementById('periodo_rotacion_horas').value = data.rot;

  // Actualizar indicadores reactivos
  updateAlbedoHelper(data.albedo);
  updateDiameterHelper(data.diameter);
  updateHHelper(data.H);
  updateOrbitZoneHelper(data.a, data.q);

  // Limpiar marcas de error
  document.querySelectorAll('.error-msg').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('input').forEach(el => {
    el.classList.remove('input-error');
    el.classList.add('input-valid');
  });

  // Ejecutar envío automático para ver el resultado de inmediato
  document.getElementById('asteroid-form').dispatchEvent(new Event('submit'));
}

// 3. Helpers Reactivos en Tiempo Real
function setupDynamicHelpers() {
  const albedoInput = document.getElementById('albedo_geometrico');
  const diamInput = document.getElementById('diametro_km');
  const hInput = document.getElementById('magnitud_absoluta_H');
  const aInput = document.getElementById('semieje_mayor_au');
  const qInput = document.getElementById('distancia_perihelio_au');

  albedoInput.addEventListener('input', (e) => updateAlbedoHelper(e.target.value));
  diamInput.addEventListener('input', (e) => updateDiameterHelper(e.target.value));
  hInput.addEventListener('input', (e) => updateHHelper(e.target.value));
  
  const updateOrbit = () => updateOrbitZoneHelper(aInput.value, qInput.value);
  aInput.addEventListener('input', updateOrbit);
  qInput.addEventListener('input', updateOrbit);
}

function updateAlbedoHelper(val) {
  const alb = parseFloat(val);
  const cat = document.getElementById('albedo-category');
  const indicator = document.getElementById('albedo-indicator');

  if (isNaN(alb) || alb <= 0) {
    cat.innerText = '0.00 (Indeterminado)';
    cat.className = 'text-xs font-mono font-medium text-lab-600 px-2 py-0.5 rounded bg-lab-100 border border-lab-200';
    indicator.style.left = '0%';
    return;
  }

  // Posicionar indicador en barra (mapeado de 0 a 0.5+)
  const pct = Math.min(Math.max((alb / 0.5) * 100, 2), 98);
  indicator.style.left = `${pct}%`;

  if (alb < 0.08) {
    cat.innerText = `${alb.toFixed(3)} (Carbón Muy Oscuro / C-Type)`;
    cat.className = 'text-xs font-mono font-semibold text-emerald-800 px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200';
  } else if (alb >= 0.08 && alb <= 0.22) {
    cat.innerText = `${alb.toFixed(3)} (Reflectividad Media / Metálico o Silicato)`;
    cat.className = 'text-xs font-mono font-semibold text-amber-900 px-2 py-0.5 rounded bg-amber-50 border border-amber-200';
  } else if (alb > 0.22 && alb <= 0.35) {
    cat.innerText = `${alb.toFixed(3)} (Silicatos Brillantes / S-Type)`;
    cat.className = 'text-xs font-mono font-semibold text-blue-900 px-2 py-0.5 rounded bg-blue-50 border border-blue-200';
  } else {
    cat.innerText = `${alb.toFixed(3)} (Muy Brillante / Basalto V-Type)`;
    cat.className = 'text-xs font-mono font-semibold text-orange-900 px-2 py-0.5 rounded bg-orange-50 border border-orange-200';
  }
}

function updateDiameterHelper(val) {
  const d = parseFloat(val);
  const helper = document.getElementById('diameter-helper');
  if (isNaN(d) || d <= 0) {
    helper.innerText = '-- km';
    return;
  }
  if (d < 1.0) {
    helper.innerText = `${(d * 1000).toFixed(0)} m (Escala Estructura)`;
  } else if (d < 50.0) {
    helper.innerText = `${d.toFixed(1)} km (Monte Everest)`;
  } else if (d < 200.0) {
    helper.innerText = `${d.toFixed(1)} km (Metrópolis)`;
  } else {
    helper.innerText = `${d.toFixed(1)} km (Protoplaneta)`;
  }
}

function updateHHelper(val) {
  const h = parseFloat(val);
  const helper = document.getElementById('h-helper');
  if (isNaN(h)) {
    helper.innerText = '--';
    return;
  }
  if (h < 6.0) {
    helper.innerText = 'Luminosidad Gigante';
  } else if (h < 12.0) {
    helper.innerText = 'Luminosidad Media';
  } else {
    helper.innerText = 'Brillo Débil (Cuerpo Pequeño)';
  }
}

function updateOrbitZoneHelper(aVal, qVal) {
  const a = parseFloat(aVal);
  const q = parseFloat(qVal);
  const chip = document.getElementById('orbit-zone-chip');

  if (isNaN(a) || a <= 0) {
    chip.innerText = 'Órbita --';
    chip.className = 'text-[10px] text-lab-500 font-mono px-1.5 py-0.5 rounded bg-lab-100 border border-lab-200';
    return;
  }

  if (q && q < 1.3) {
    chip.innerText = 'Cercano a la Tierra (NEO)';
    chip.className = 'text-[10px] text-emerald-800 font-mono font-medium px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200';
  } else if (a >= 2.0 && a <= 3.3) {
    chip.innerText = 'Cinturón Principal';
    chip.className = 'text-[10px] text-lab-800 font-mono font-medium px-1.5 py-0.5 rounded bg-lab-100 border border-lab-200';
  } else if (a >= 5.0 && a <= 5.5) {
    chip.innerText = 'Troyano de Júpiter';
    chip.className = 'text-[10px] text-purple-800 font-mono font-medium px-1.5 py-0.5 rounded bg-purple-50 border border-purple-200';
  } else {
    chip.innerText = 'Órbita Externa';
    chip.className = 'text-[10px] text-lab-700 font-mono font-medium px-1.5 py-0.5 rounded bg-lab-100 border border-lab-200';
  }
}

// 4. Validación y Envío de Formulario
function setupFormValidationAndSubmit() {
  const form = document.getElementById('asteroid-form');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const hInput = document.getElementById('magnitud_absoluta_H');
    const albInput = document.getElementById('albedo_geometrico');
    const diamInput = document.getElementById('diametro_km');
    const aInput = document.getElementById('semieje_mayor_au');
    const eInput = document.getElementById('excentricidad');
    const iInput = document.getElementById('inclinacion_grados');
    const qInput = document.getElementById('distancia_perihelio_au');
    const rotInput = document.getElementById('periodo_rotacion_horas');

    // Validar según especificaciones
    const v1 = validateField(hInput, 'h-error', val => !isNaN(val) && parseFloat(val) >= -5.0 && parseFloat(val) <= 35.0);
    const v2 = validateField(albInput, 'albedo-error', val => !isNaN(val) && parseFloat(val) >= 0.001 && parseFloat(val) <= 1.0);
    const v3 = validateField(diamInput, 'diameter-error', val => !isNaN(val) && parseFloat(val) > 0.0);
    const v4 = validateField(aInput, 'semieje-error', val => !isNaN(val) && parseFloat(val) > 0.0);
    const v5 = validateField(eInput, 'excentricidad-error', val => !isNaN(val) && parseFloat(val) >= 0.0 && parseFloat(val) <= 1.5);
    const v6 = validateField(iInput, 'inclinacion-error', val => !isNaN(val) && parseFloat(val) >= 0.0 && parseFloat(val) <= 180.0);
    const v7 = validateField(qInput, 'perihelio-error', val => !isNaN(val) && parseFloat(val) > 0.0);

    if (!v1 || !v2 || !v3 || !v4 || !v5 || !v6 || !v7) {
      return;
    }

    const payload = {
      magnitud_absoluta_H: parseFloat(hInput.value),
      albedo_geometrico: parseFloat(albInput.value),
      diametro_km: parseFloat(diamInput.value),
      semieje_mayor_au: parseFloat(aInput.value),
      excentricidad: parseFloat(eInput.value),
      inclinacion_grados: parseFloat(iInput.value),
      distancia_perihelio_au: parseFloat(qInput.value),
      periodo_rotacion_horas: rotInput.value ? parseFloat(rotInput.value) : 6.8
    };

    setLoading(true);

    try {
      const res = await fetch('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error en el servidor al calcular inferencia.');
      }

      const result = await res.json();
      renderAsteroidResult(result);
    } catch (err) {
      alert(`Error en el cálculo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  });
}

function validateField(inputEl, errorId, validatorFn) {
  const errorEl = document.getElementById(errorId);
  const isValid = validatorFn(inputEl.value);

  if (isValid) {
    if (errorEl) errorEl.classList.add('hidden');
    inputEl.classList.remove('input-error');
    inputEl.classList.add('input-valid');
  } else {
    if (errorEl) errorEl.classList.remove('hidden');
    inputEl.classList.add('input-error');
    inputEl.classList.remove('input-valid');
  }
  return isValid;
}

function setLoading(isLoading) {
  const btn = document.getElementById('submit-btn');
  const spinner = document.getElementById('btn-spinner');
  const text = document.getElementById('btn-text');

  if (isLoading) {
    btn.disabled = true;
    btn.classList.add('opacity-75', 'cursor-not-allowed');
    spinner.classList.remove('hidden');
    text.innerText = 'Calculando Inferencia con Random Forest...';
  } else {
    btn.disabled = false;
    btn.classList.remove('opacity-75', 'cursor-not-allowed');
    spinner.classList.add('hidden');
    text.innerText = 'Ejecutar Diagnóstico de Prospección';
  }
}

// 5. Renderizado Dinámico de Resultados
function renderAsteroidResult(data) {
  document.getElementById('empty-state').classList.add('hidden');
  const resultsCard = document.getElementById('results-card');
  resultsCard.classList.remove('hidden');

  // Encabezado
  document.getElementById('result-icon').innerText = data.icono || '🪐';
  document.getElementById('result-family').innerText = data.prediccion;
  document.getElementById('result-confidence').innerText = `${data.confianza}%`;
  document.getElementById('result-orbit-badge').innerText = `🪐 ${data.zona_orbital}`;

  // Tarjeta de Viabilidad Minera
  const card = document.getElementById('mining-viability-card');
  const tag = document.getElementById('mining-badge-tag');

  document.getElementById('mining-metals').innerText = data.potencial_minero.metales_preciosos;
  document.getElementById('mining-water').innerText = data.potencial_minero.recursos_hidricos_combustible;
  document.getElementById('mining-verdict').innerText = data.potencial_minero.calificacion_general;

  if (data.es_metalico) {
    card.className = 'rounded-xl p-4 border border-amber-200 bg-amber-50/70 transition-all';
    tag.className = 'text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300';
    tag.innerText = `Alta Ley Metálica: ${data.probabilidad_metalica_detector}%`;
  } else if (data.prediccion.includes('Carbonáceo')) {
    card.className = 'rounded-xl p-4 border border-emerald-200 bg-emerald-50/70 transition-all';
    tag.className = 'text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-300';
    tag.innerText = 'Recurso Hídrico Clave';
  } else {
    card.className = 'rounded-xl p-4 border border-lab-200 bg-lab-50 transition-all';
    tag.className = 'text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-lab-100 text-lab-800 border border-lab-200';
    tag.innerText = 'Rocoso Estructural';
  }

  // Gráfico de Barras de Probabilidades (Pigmentos Material 3 - Sin Neones)
  const probContainer = document.getElementById('probabilities-container');
  probContainer.innerHTML = '';

  const colorMap = {
    'Metálico (Fe-Ni, Oro, Platino)': 'bg-amber-600',
    'Carbonáceo (Agua, Compuestos Orgánicos)': 'bg-emerald-700',
    'Silicatos / Rocoso (Mg-Fe, Piroxeno)': 'bg-blue-700',
    'Basáltico (Magmático, Rocas Ígneas)': 'bg-orange-700'
  };

  for (const [cls, pct] of Object.entries(data.probabilidades)) {
    const isWinner = cls === data.prediccion;
    const barBg = colorMap[cls] || 'bg-lab-800';

    const barHtml = `
      <div>
        <div class="flex justify-between text-xs mb-1.5 font-mono">
          <span class="${isWinner ? 'font-bold text-lab-900' : 'text-lab-600'}">${cls}</span>
          <span class="${isWinner ? 'font-bold text-lab-900' : 'text-lab-500'}">${pct}%</span>
        </div>
        <div class="w-full bg-lab-100 h-2 rounded-full overflow-hidden border border-lab-200">
          <div class="prob-bar-fill h-full rounded-full ${barBg}" style="width: 0%"></div>
        </div>
      </div>
    `;
    probContainer.insertAdjacentHTML('beforeend', barHtml);
  }

  // Animar las barras de progreso suavemente
  setTimeout(() => {
    const bars = probContainer.querySelectorAll('.prob-bar-fill');
    let idx = 0;
    for (const [, pct] of Object.entries(data.probabilidades)) {
      if (bars[idx]) {
        bars[idx].style.width = `${pct}%`;
      }
      idx++;
    }
  }, 40);

  // Ficha técnica y Justificación
  document.getElementById('meta-minerals').innerText = data.minerales_clave;
  document.getElementById('meta-albedo').innerText = data.albedo_tipico;
  document.getElementById('meta-objective').innerText = data.objetivo_mision;
  document.getElementById('result-interpretation').innerText = data.interpretacion_astrofisica;

  // Desplazamiento suave en pantallas móviles
  if (window.innerWidth < 1024) {
    resultsCard.scrollIntoView({ behavior: 'smooth' });
  }
}

// 6. Reiniciar Formulario
function resetAsteroidForm() {
  document.getElementById('asteroid-form').reset();
  document.getElementById('results-card').classList.add('hidden');
  document.getElementById('empty-state').classList.remove('hidden');
  document.querySelectorAll('input').forEach(el => {
    el.classList.remove('input-valid', 'input-error');
  });
  document.querySelectorAll('.error-msg').forEach(el => el.classList.add('hidden'));
  updateAlbedoHelper(0.12);
  updateDiameterHelper(0);
  updateHHelper(0);
}

window.loadAsteroidPreset = loadAsteroidPreset;
window.resetAsteroidForm = resetAsteroidForm;

// =============================================================================
// SECCIÓN: PROCESAMIENTO MASIVO Y REPORTES (EXCEL / CSV)
// =============================================================================

let currentBatchReport = null;
let currentBatchFile = null;
let currentFilteredRecords = [];

// 7. Selector de Modos (Individual vs Masivo)
function switchMode(mode) {
  const singleView = document.getElementById('single-mode-view');
  const batchView = document.getElementById('batch-mode-view');
  const singleBtn = document.getElementById('tab-single-btn');
  const batchBtn = document.getElementById('tab-batch-btn');

  if (mode === 'single') {
    singleView.classList.remove('hidden');
    batchView.classList.add('hidden');
    
    singleBtn.className = 'px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-2 bg-white text-lab-900 shadow-2xs cursor-pointer';
    batchBtn.className = 'px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-2 text-lab-600 hover:text-lab-900 cursor-pointer';
  } else {
    singleView.classList.add('hidden');
    batchView.classList.remove('hidden');

    singleBtn.className = 'px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-2 text-lab-600 hover:text-lab-900 cursor-pointer';
    batchBtn.className = 'px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-2 bg-white text-lab-900 shadow-2xs cursor-pointer';
  }
}

// 8. Inicialización de Eventos de Carga Drag & Drop
function setupBatchProcessing() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('batch-file-input');

  if (!dropzone || !fileInput) return;

  // Eventos de arrastre
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-over');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-over');
    }, false);
  });

  // Al soltar el archivo
  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      handleFileSelected(files[0]);
    }
  });

  // Al seleccionar mediante el explorador
  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

// 9. Manejo del Archivo Seleccionado
function handleFileSelected(file) {
  currentBatchFile = file;
  const badge = document.getElementById('selected-file-badge');
  const nameSpan = document.getElementById('selected-file-name');

  if (badge && nameSpan) {
    nameSpan.innerText = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    badge.classList.remove('hidden');
    badge.classList.add('inline-flex');
  }

  processBatchFile(file);
}

function clearSelectedFile(event) {
  if (event) event.stopPropagation();
  currentBatchFile = null;
  const fileInput = document.getElementById('batch-file-input');
  if (fileInput) fileInput.value = '';
  
  const badge = document.getElementById('selected-file-badge');
  if (badge) {
    badge.classList.add('hidden');
    badge.classList.remove('inline-flex');
  }
}

// 10. Cargar y Procesar Dataset de Prueba de la NASA Automáticamente
async function loadAndRunSampleDataset() {
  const progressBox = document.getElementById('batch-progress');
  const errorBox = document.getElementById('batch-error-box');
  
  if (errorBox) errorBox.classList.add('hidden');
  if (progressBox) progressBox.classList.remove('hidden');

  try {
    const res = await fetch('/api/v1/template/csv');
    if (!res.ok) throw new Error('No se pudo descargar la plantilla de prueba desde el servidor.');
    
    const blob = await res.blob();
    const testFile = new File([blob], 'prueba_asteroides_entrada.csv', { type: 'text/csv' });
    
    handleFileSelected(testFile);
  } catch (err) {
    if (progressBox) progressBox.classList.add('hidden');
    if (errorBox) {
      errorBox.classList.remove('hidden');
      document.getElementById('batch-error-message').innerText = err.message;
    }
  }
}

// 11. Envío al Servidor y Ejecución del Motor Masivo
async function processBatchFile(file) {
  const progressBox = document.getElementById('batch-progress');
  const progressBar = document.getElementById('batch-progress-bar');
  const progressStatus = document.getElementById('batch-progress-status');
  const errorBox = document.getElementById('batch-error-box');
  const reportContainer = document.getElementById('batch-report-container');

  if (errorBox) errorBox.classList.add('hidden');
  if (progressBox) progressBox.classList.remove('hidden');
  if (progressBar) progressBar.style.width = '20%';

  const formData = new FormData();
  formData.append('file', file);

  try {
    if (progressBar) progressBar.style.width = '60%';

    const response = await fetch('/api/v1/predict/batch', {
      method: 'POST',
      body: formData
    });

    if (progressBar) progressBar.style.width = '90%';

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Error del servidor HTTP ${response.status}`);
    }

    const data = await response.json();
    currentBatchReport = data;

    if (progressBar) progressBar.style.width = '100%';
    setTimeout(() => {
      if (progressBox) progressBox.classList.add('hidden');
    }, 400);

    renderBatchReport(data);

  } catch (err) {
    if (progressBox) progressBox.classList.add('hidden');
    if (errorBox) {
      errorBox.classList.remove('hidden');
      document.getElementById('batch-error-message').innerText = err.message;
    }
  }
}

// 12. Renderizado del Reporte Masivo
function renderBatchReport(data) {
  const summary = data.summary;
  const reportContainer = document.getElementById('batch-report-container');

  // Actualizar KPIs Ejecutivos
  document.getElementById('report-batch-badge').innerText = `${summary.total_registros} Cuerpos Analizados`;
  document.getElementById('kpi-total-count').innerText = summary.total_registros;
  document.getElementById('kpi-valid-rate').innerText = `${Math.round((summary.registros_validos / summary.total_registros) * 100)}% Válidos`;
  document.getElementById('kpi-avg-diam').innerText = `${summary.diametro_promedio_km} km`;

  document.getElementById('kpi-metal-count').innerText = summary.conteo_metalicos;
  document.getElementById('kpi-metal-pct').innerText = `${summary.porcentaje_metalicos}%`;

  document.getElementById('kpi-water-count').innerText = summary.conteo_recursos_hidricos;
  document.getElementById('kpi-water-pct').innerText = `${summary.porcentaje_recursos_hidricos}%`;

  document.getElementById('kpi-neo-count').innerText = summary.conteo_neos;
  document.getElementById('kpi-neo-pct').innerText = `${summary.porcentaje_neos}%`;

  document.getElementById('batch-avg-albedo').innerText = summary.albedo_promedio.toFixed(3);
  document.getElementById('batch-max-diam').innerText = `${summary.diametro_maximo_km.toLocaleString()} km`;

  // Renderizar Barras de Distribución Taxonómica
  const barsContainer = document.getElementById('batch-distribution-bars');
  barsContainer.innerHTML = '';

  const classColorMap = {
    'Metálico (Fe-Ni, Oro, Platino)': { bg: 'bg-amber-600', text: 'text-amber-900', label: 'Metálico (Fe-Ni, Pt, Au)' },
    'Carbonáceo (Agua, Compuestos Orgánicos)': { bg: 'bg-emerald-600', text: 'text-emerald-900', label: 'Carbonáceo (Agua H2O)' },
    'Silicatos / Rocoso (Mg-Fe, Piroxeno)': { bg: 'bg-blue-600', text: 'text-blue-900', label: 'Silicatos / Rocoso' },
    'Basáltico (Magmático, Rocas Ígneas)': { bg: 'bg-orange-600', text: 'text-orange-900', label: 'Basáltico Ígneo' }
  };

  for (const [clsName, count] of Object.entries(summary.distribucion_composicion)) {
    const pct = summary.porcentajes_composicion[clsName] || 0;
    const styleInfo = classColorMap[clsName] || { bg: 'bg-lab-700', text: 'text-lab-900', label: clsName };

    const barEl = document.createElement('div');
    barEl.className = 'space-y-1.5';
    barEl.innerHTML = `
      <div class="flex justify-between items-center text-xs">
        <span class="font-semibold ${styleInfo.text}">${styleInfo.label}</span>
        <span class="font-mono text-lab-600 font-medium">${count} (${pct}%)</span>
      </div>
      <div class="w-full bg-lab-100 h-2 rounded-full overflow-hidden border border-lab-200">
        <div class="h-full ${styleInfo.bg} rounded-full transition-all duration-700" style="width: ${pct}%;"></div>
      </div>
    `;
    barsContainer.appendChild(barEl);
  }

  // Renderizar Top 5 Objetivos Mineros Prioritarios
  const topTargetsContainer = document.getElementById('top-targets-container');
  topTargetsContainer.innerHTML = '';

  data.top_targets.forEach((target, index) => {
    const cardEl = document.createElement('div');
    const badgeClass = `badge-${target.badge_color || 'metal'}`;

    cardEl.className = 'p-3.5 rounded-xl border border-lab-200 bg-white hover:bg-lab-50/70 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs';
    cardEl.innerHTML = `
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-lg bg-lab-900 text-white font-mono font-bold text-xs flex items-center justify-center shrink-0">
          #${index + 1}
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-display font-bold text-sm text-lab-900">${target.nombre}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${badgeClass}">
              ${target.clase_corta}
            </span>
            ${target.es_metalico ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-900 border border-amber-300 font-mono font-bold">Metal: ${target.probabilidad_metalica}%</span>` : ''}
          </div>
          <p class="text-xs text-lab-500 mt-0.5">
            ${target.zona_orbital} &bull; Diámetro: <span class="font-mono font-medium text-lab-800">${target.diametro_km} km</span>
          </p>
        </div>
      </div>
      <div class="text-right sm:text-right">
        <span class="text-[11px] font-medium text-lab-700 block">${target.valor_estrategico}</span>
        <span class="text-[11px] font-mono text-emerald-700 font-semibold">${target.confianza}% confianza</span>
      </div>
    `;
    topTargetsContainer.appendChild(cardEl);
  });

  // Renderizar Tabla Completa
  currentFilteredRecords = data.records;
  renderBatchTable(data.records);

  // Mostrar contenedor y desplazar suavemente
  reportContainer.classList.remove('hidden');
  reportContainer.scrollIntoView({ behavior: 'smooth' });
}

// 13. Renderizado de Filas de la Tabla
function renderBatchTable(records) {
  const tbody = document.getElementById('batch-table-body');
  const countText = document.getElementById('table-showing-text');
  tbody.innerHTML = '';

  if (countText) {
    const total = currentBatchReport ? currentBatchReport.records.length : records.length;
    countText.innerText = `Mostrando ${records.length} de ${total} registros`;
  }

  if (records.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-8 text-lab-400">
          No se encontraron asteroides que coincidan con los filtros aplicados.
        </td>
      </tr>
    `;
    return;
  }

  records.forEach((row) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-lab-50 transition border-b border-lab-100';

    const badgeClass = `badge-${row.badge_color || 'metal'}`;
    const metalBadge = row.es_metalico 
      ? `<span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300">SÍ (${row.probabilidad_metalica}%)</span>`
      : `<span class="text-lab-400 font-mono text-[11px]">No (${row.probabilidad_metalica}%)</span>`;

    tr.innerHTML = `
      <td class="py-3 px-4 font-semibold text-lab-900 font-display whitespace-nowrap">${row.nombre_asteroide}</td>
      <td class="py-3 px-3 whitespace-nowrap">
        <span class="px-2 py-0.5 rounded text-[11px] font-medium ${badgeClass}">
          ${row.clase_corta}
        </span>
      </td>
      <td class="py-3 px-3 font-mono text-xs font-semibold text-lab-800">${row.confianza}%</td>
      <td class="py-3 px-3 whitespace-nowrap">${metalBadge}</td>
      <td class="py-3 px-3 font-mono text-xs text-lab-700">${row.albedo_geometrico.toFixed(3)}</td>
      <td class="py-3 px-3 font-mono text-xs text-lab-900">${row.diametro_km.toLocaleString()}</td>
      <td class="py-3 px-3 text-xs text-lab-600 max-w-xs truncate" title="${row.zona_orbital}">${row.zona_orbital}</td>
      <td class="py-3 px-4 text-xs text-lab-700 font-medium">${row.potencial_minero}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 14. Filtros Interactivos de la Tabla
function filterBatchTable() {
  if (!currentBatchReport || !currentBatchReport.records) return;

  const searchVal = document.getElementById('table-search-input').value.toLowerCase().trim();
  const classVal = document.getElementById('table-class-filter').value;
  const orbitVal = document.getElementById('table-orbit-filter').value;

  const filtered = currentBatchReport.records.filter(row => {
    // Filtro por texto
    if (searchVal && !row.nombre_asteroide.toLowerCase().includes(searchVal)) {
      return false;
    }
    // Filtro por clase
    if (classVal !== 'ALL') {
      if (row.clase_corta !== classVal) return false;
    }
    // Filtro por órbita
    if (orbitVal !== 'ALL') {
      if (!row.zona_orbital.toLowerCase().includes(orbitVal.toLowerCase())) return false;
    }
    return true;
  });

  currentFilteredRecords = filtered;
  renderBatchTable(filtered);
}

// 15. Exportar Reporte a CSV
async function downloadProcessedCSV() {
  if (!currentBatchReport) return;

  // Si tenemos el archivo cargado, solicitamos la exportación directa al endpoint de backend
  if (currentBatchFile) {
    try {
      const formData = new FormData();
      formData.append('file', currentBatchFile);

      const res = await fetch('/api/v1/predict/batch/export', {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const blob = await res.blob();
        triggerDownload(blob, 'reporte_asteroides_predicciones.csv');
        return;
      }
    } catch (e) {
      console.warn('Fallback a exportación local CSV:', e);
    }
  }

  // Fallback: Generación de CSV desde el objeto en memoria
  const records = currentBatchReport.records;
  const headers = [
    'Asteroide', 'Composicion_Predicha', 'Confianza_Pct', 'Es_Metalico',
    'Probabilidad_Metalica_Pct', 'Potencial_Minero_ISRU', 'Zona_Orbital',
    'Albedo_Visual_pv', 'Diametro_km', 'Magnitud_H', 'Semieje_Mayor_AU',
    'Excentricidad', 'Inclinacion_deg', 'Perihelio_AU', 'Rotacion_horas'
  ];

  const rows = records.map(r => [
    `"${r.nombre_asteroide}"`,
    `"${r.prediccion}"`,
    r.confianza,
    r.es_metalico,
    r.probabilidad_metalica,
    `"${r.potencial_minero}"`,
    `"${r.zona_orbital}"`,
    r.albedo_geometrico,
    r.diametro_km,
    r.magnitud_absoluta_H,
    r.semieje_mayor_au,
    r.excentricidad,
    r.inclinacion_grados,
    r.distancia_perihelio_au,
    r.periodo_rotacion_horas
  ].join(','));

  const csvContent = '\uFEFF' + [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  triggerDownload(blob, 'reporte_asteroides_predicciones.csv');
}

// 16. Exportar Reporte a JSON
function downloadProcessedJSON() {
  if (!currentBatchReport) return;
  const jsonContent = JSON.stringify(currentBatchReport, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  triggerDownload(blob, 'reporte_asteroides_predicciones.json');
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Exponer funciones globales para interacción HTML
window.switchMode = switchMode;
window.handleFileSelected = handleFileSelected;
window.clearSelectedFile = clearSelectedFile;
window.loadAndRunSampleDataset = loadAndRunSampleDataset;
window.filterBatchTable = filterBatchTable;
window.downloadProcessedCSV = downloadProcessedCSV;
window.downloadProcessedJSON = downloadProcessedJSON;
