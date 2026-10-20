/**
 * NASA JPL Asteroid Prospector - Suite de Pruebas E2E & Integración con Playwright
 * 
 * Verificación completa del flujo:
 *   Input -> Validación -> API -> Inferencia -> Renderizado Dinámico
 * 
 * Cumplimiento con:
 *   - taste-skill: Tipografía técnica, números tabulares, paleta de laboratorio M3 sin neón.
 *   - playwright-cli: Inspección semántica de elementos, eventos de teclado/click, capturas visuales.
 */

const { chromium } = require('C:/Users/User/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright-core');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = path.resolve(__dirname, 'screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runTestSuite() {
  console.log('================================================================');
  console.log('INICIANDO PRUEBAS END-TO-END CON PLAYWRIGHT - NASA JPL PROSPECTOR');
  console.log('================================================================\n');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });

  const page = await context.newPage();

  // Escuchar errores de consola en la página
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  let testCount = 0;
  let passCount = 0;

  function assert(condition, message) {
    testCount++;
    if (condition) {
      passCount++;
      console.log(`  [PASS] ${message}`);
    } else {
      console.error(`  [FAIL] ${message}`);
      throw new Error(`Fallo de aserción: ${message}`);
    }
  }

  try {
    // -------------------------------------------------------------------------
    // TEST 1: Carga Inicial de la Aplicación y Auditoría Estética taste-skill
    // -------------------------------------------------------------------------
    console.log('--> PASO 1: Carga de Aplicación y Verificación de Estado Inicial');
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });

    const title = await page.title();
    assert(title.includes('NASA JPL Asteroid Prospector'), `Título de página correcto: "${title}"`);

    // Indicador de Salud del API
    const apiStatusText = await page.textContent('#api-status-text');
    assert(apiStatusText.includes('JPL Random Forest: Online'), `Status de API Online: "${apiStatusText}"`);

    // Estado vacío presente y tarjeta de resultados oculta
    const emptyStateVisible = await page.isVisible('#empty-state');
    const resultsCardHidden = await page.evaluate(() => {
      const el = document.getElementById('results-card');
      return el.classList.contains('hidden');
    });
    assert(emptyStateVisible, 'El estado vacío (#empty-state) se muestra al inicio');
    assert(resultsCardHidden, 'La tarjeta de resultados (#results-card) inicia oculta');

    // Taste-skill: Tipografía tabular en inputs numéricos
    const tabularNumericCheck = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input[type="number"]');
      const input = inputs[0];
      const style = window.getComputedStyle(input);
      return style.fontVariantNumeric.includes('tabular-nums') || input.classList.contains('font-mono');
    });
    assert(tabularNumericCheck, 'Inputs configurados con numeración tabular estricta (tabular-nums / font-mono)');

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_initial_state.png'), fullPage: true });
    console.log('    [SCREENSHOT] tests/screenshots/01_initial_state.png guardado.\n');

    // -------------------------------------------------------------------------
    // TEST 2: Validación de Entradas en el Cliente (Fronteras y Errores)
    // -------------------------------------------------------------------------
    console.log('--> PASO 2: Validación de Entradas y Límites Críticos (Input & Validation)');

    // Inyectar valores inválidos que violen las restricciones
    await page.fill('#albedo_geometrico', '1.85');   // Máximo es 1.0
    await page.fill('#magnitud_absoluta_H', '45');   // Máximo es 35.0
    await page.fill('#diametro_km', '-10');          // Debe ser > 0
    await page.fill('#semieje_mayor_au', '-2');      // Debe ser > 0
    await page.fill('#excentricidad', '3.5');        // Máximo es 1.5
    await page.fill('#inclinacion_grados', '220');   // Máximo es 180°
    await page.fill('#distancia_perihelio_au', '-1'); // Debe ser > 0

    // Click en botón de envío
    await page.click('#submit-btn');

    // Comprobar que los mensajes de error se muestran
    const errorClasses = await page.evaluate(() => {
      const albedoErr = !document.getElementById('albedo-error').classList.contains('hidden');
      const hErr = !document.getElementById('h-error').classList.contains('hidden');
      const diamErr = !document.getElementById('diameter-error').classList.contains('hidden');
      const semErr = !document.getElementById('semieje-error').classList.contains('hidden');
      const eccErr = !document.getElementById('excentricidad-error').classList.contains('hidden');
      const incErr = !document.getElementById('inclinacion-error').classList.contains('hidden');
      const periErr = !document.getElementById('perihelio-error').classList.contains('hidden');
      
      const albedoInputError = document.getElementById('albedo_geometrico').classList.contains('input-error');
      const resHidden = document.getElementById('results-card').classList.contains('hidden');

      return { albedoErr, hErr, diamErr, semErr, eccErr, incErr, periErr, albedoInputError, resHidden };
    });

    assert(errorClasses.albedoErr, 'Error visual activado para albedo fuera de rango (>1.0)');
    assert(errorClasses.diamErr, 'Error visual activado para diámetro negativo');
    assert(errorClasses.eccErr, 'Error visual activado para excentricidad hiperbólica no permitida (>1.5)');
    assert(errorClasses.albedoInputError, 'Clase "input-error" aplicada a campo erróneo');
    assert(errorClasses.resHidden, 'Formulario bloqueó el envío y los resultados siguen ocultos');

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_validation_errors.png'), fullPage: true });
    console.log('    [SCREENSHOT] tests/screenshots/02_validation_errors.png guardado.\n');

    // -------------------------------------------------------------------------
    // TEST 3: Helpers Reactivos Dinámicos
    // -------------------------------------------------------------------------
    console.log('--> PASO 3: Helpers Reactivos en Tiempo Real (Telemetría de Entrada)');
    
    // Probar helper de albedo oscuro (C-type)
    await page.fill('#albedo_geometrico', '0.04');
    await page.dispatchEvent('#albedo_geometrico', 'input');
    const albedoCat = await page.textContent('#albedo-category');
    assert(albedoCat.includes('Carbón Muy Oscuro'), `Albedo 0.04 categorizado como carbón oscuro: "${albedoCat}"`);

    // Probar helper de diámetro escala
    await page.fill('#diametro_km', '0.45');
    await page.dispatchEvent('#diametro_km', 'input');
    const diamHelp = await page.textContent('#diameter-helper');
    assert(diamHelp.includes('m (Escala Estructura)'), `Diámetro 0.45km formateado en metros: "${diamHelp}"`);

    // Probar clasificador orbital reactivo (NEO vs Main Belt)
    await page.fill('#semieje_mayor_au', '1.12');
    await page.fill('#distancia_perihelio_au', '0.85');
    await page.dispatchEvent('#distancia_perihelio_au', 'input');
    const orbitChip = await page.textContent('#orbit-zone-chip');
    assert(orbitChip.includes('NEO'), `Órbita perihélica q < 1.3 clasificada como NEO: "${orbitChip}"\n`);

    // -------------------------------------------------------------------------
    // TEST 4: Flujo Completo E2E: Preset 16-Psyche (Metálico Fe-Ni)
    // -------------------------------------------------------------------------
    console.log('--> PASO 4: Inferencia y Renderizado Dinámico: Caso 16-Psyche (Metálico)');

    // Esperar a la llamada del API cuando se cargue el preset
    const [responsePsyche] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/api/v1/predict') && res.status() === 200),
      page.click('button:has-text("16-Psyche")')
    ]);

    const psycheJson = await responsePsyche.json();
    assert(psycheJson.status === 'success', 'Respuesta HTTP 200 con status "success" desde /api/v1/predict');
    assert(psycheJson.prediccion.includes('Metálico'), `Inferencia multiclase predijo: "${psycheJson.prediccion}"`);
    assert(psycheJson.es_metalico === true, 'Detector binario clasificó asteroide como Metálico');

    // Esperar a que la tarjeta de resultados se despliegue en el DOM
    await page.waitForSelector('#results-card:not(.hidden)');
    const resultFamilyText = await page.textContent('#result-family');
    assert(resultFamilyText.includes('Metálico'), `Tarjeta renderizó título de familia: "${resultFamilyText}"`);

    // Nivel de confianza renderizado
    const confText = await page.textContent('#result-confidence');
    assert(confText.includes('%'), `Métrica de confianza renderizada: "${confText}"`);

    // Evaluación de viabilidad minera
    const miningBadge = await page.textContent('#mining-badge-tag');
    const miningMetals = await page.textContent('#mining-metals');
    assert(miningBadge.includes('Alta Ley Metálica') || miningBadge.includes('Prioridad'), `Badge minero ISRU: "${miningBadge}"`);
    assert(miningMetals.includes('Muy Alto'), `Metales preciosos: "${miningMetals}"`);

    // Distribución de probabilidades en barras
    const barCount = await page.$$eval('#probabilities-container .prob-bar-fill', bars => bars.length);
    assert(barCount === 4, `4 barras de probabilidad taxonómica renderizadas (conteo: ${barCount})`);

    // Justificación astrofísica
    const interpText = await page.textContent('#result-interpretation');
    assert(interpText.length > 50, `Justificación astrofísica inyectada correctamente (${interpText.length} caracteres)`);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_result_psyche_metallic.png'), fullPage: true });
    console.log('    [SCREENSHOT] tests/screenshots/03_result_psyche_metallic.png guardado.\n');

    // -------------------------------------------------------------------------
    // TEST 5: Flujo Completo E2E: Preset 101955-Bennu (Carbonáceo / Agua)
    // -------------------------------------------------------------------------
    console.log('--> PASO 5: Inferencia y Renderizado Dinámico: Caso 101955-Bennu (Carbonáceo)');

    const [responseBennu] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/api/v1/predict') && res.status() === 200),
      page.click('button:has-text("101955-Bennu")')
    ]);

    const bennuJson = await responseBennu.json();
    assert(bennuJson.prediccion.includes('Carbonáceo'), `Inferencia Bennu: "${bennuJson.prediccion}"`);

    // Esperar renderizado dinámico en UI
    await page.waitForFunction(() => {
      const family = document.getElementById('result-family').innerText;
      return family.includes('Carbonáceo');
    });

    const bennuFamily = await page.textContent('#result-family');
    const bennuWater = await page.textContent('#mining-water');
    const bennuBadge = await page.textContent('#mining-badge-tag');
    assert(bennuFamily.includes('Carbonáceo'), `UI actualizada a familia Carbonácea: "${bennuFamily}"`);
    assert(bennuWater.includes('Excepcional') || bennuWater.includes('H2O'), `Agua & propelente evaluado como prioritario: "${bennuWater}"`);
    assert(bennuBadge.includes('Recurso Hídrico'), `Badge dinámico ISRU adaptado a Agua: "${bennuBadge}"`);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_result_bennu_carbonaceous.png'), fullPage: true });
    console.log('    [SCREENSHOT] tests/screenshots/04_result_bennu_carbonaceous.png guardado.\n');

    // -------------------------------------------------------------------------
    // TEST 6: Flujo Completo E2E: Preset 4-Vesta (Basáltico)
    // -------------------------------------------------------------------------
    console.log('--> PASO 6: Inferencia y Renderizado Dinámico: Caso 4-Vesta (Basáltico)');

    const [responseVesta] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/api/v1/predict') && res.status() === 200),
      page.click('button:has-text("4-Vesta")')
    ]);

    const vestaJson = await responseVesta.json();
    assert(vestaJson.prediccion.includes('Basáltico'), `Inferencia Vesta: "${vestaJson.prediccion}"`);

    await page.waitForFunction(() => {
      const family = document.getElementById('result-family').innerText;
      return family.includes('Basáltico');
    });

    const vestaFamily = await page.textContent('#result-family');
    assert(vestaFamily.includes('Basáltico'), `UI actualizada a clase Basáltica: "${vestaFamily}"`);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_result_vesta_basaltic.png'), fullPage: true });
    console.log('    [SCREENSHOT] tests/screenshots/05_result_vesta_basaltic.png guardado.\n');

    // -------------------------------------------------------------------------
    // TEST 7: Reinicio del Formulario y Ciclo Completo de Estado
    // -------------------------------------------------------------------------
    console.log('--> PASO 7: Limpieza y Reinicio de Estado (Reset Form)');

    await page.click('button:has-text("Evaluar otro asteroide")');

    // Verificar que la tarjeta de resultados vuelve a estar oculta y el empty state visible
    const isReset = await page.evaluate(() => {
      const resultsHidden = document.getElementById('results-card').classList.contains('hidden');
      const emptyVisible = !document.getElementById('empty-state').classList.contains('hidden');
      const hVal = document.getElementById('magnitud_absoluta_H').value;
      const albVal = document.getElementById('albedo_geometrico').value;
      return resultsHidden && emptyVisible && hVal === '' && albVal === '';
    });

    assert(isReset, 'Formulario limpiado, tarjeta de resultados oculta y empty-state restaurado');

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_form_reset.png'), fullPage: true });
    console.log('    [SCREENSHOT] tests/screenshots/06_form_reset.png guardado.\n');

    // -------------------------------------------------------------------------
    // TEST 8: Auditoría de Errores en Consola
    // -------------------------------------------------------------------------
    console.log('--> PASO 8: Auditoría de Consola del Navegador');
    const filteredErrors = consoleErrors.filter(err => !err.includes('favicon.ico'));
    assert(filteredErrors.length === 0, `Cero errores de JavaScript en consola durante toda la sesión (Encontrados: ${filteredErrors.length})`);

    console.log('================================================================');
    console.log(`RESUMEN FINAL: ${passCount}/${testCount} ASERCIONES SUPERADAS CON ÉXITO (100%)`);
    console.log('================================================================');

  } catch (err) {
    console.error('\n[ERROR CRÍTICO EN E2E]:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

runTestSuite();
