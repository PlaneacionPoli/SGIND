# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: kpis.spec.ts >> Resumen General — KPI cards visibles tras login
- Location: e2e\kpis.spec.ts:19:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('div').filter({ has: locator('p, span').filter({ hasText: /\d+/ }) }).first()
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 8000ms
  - waiting for locator('div').filter({ has: locator('p, span').filter({ hasText: /\d+/ }) }).first()

```

```yaml
- 'heading "Application error: a client-side exception has occurred (see the browser console for more information)." [level=2]'
```

# Test source

```ts
  1   | /**
  2   |  * Tests E2E — KPIs del Resumen General
  3   |  *
  4   |  * Verifica:
  5   |  * 1. Los KPI cards se renderizan con datos reales de la API
  6   |  * 2. El filtro de año actualiza la consulta
  7   |  * 3. Los valores de KPIs coinciden con los datos mockeados (paridad)
  8   |  * 4. El CMI Estratégico actualiza datos al cambiar el año
  9   |  */
  10  | 
  11  | import { test, expect } from "@playwright/test";
  12  | import { mockAPI, devLogin, MOCK_KPIS } from "./fixtures";
  13  | 
  14  | test.beforeEach(async ({ page }) => {
  15  |   await mockAPI(page);
  16  |   await devLogin(page);
  17  | });
  18  | 
  19  | test("Resumen General — KPI cards visibles tras login", async ({ page }) => {
  20  |   await page.goto("/resumen-general?pdi=PDI-2022-2026");
  21  |   await page.waitForLoadState("networkidle");
  22  |   await page.waitForTimeout(1_200);
  23  | 
  24  |   // Al menos un KPI card debe ser visible
  25  |   const kpiCards = page
  26  |     .locator("div")
  27  |     .filter({ has: page.locator("p, span").filter({ hasText: /\d+/ }) })
  28  |     .first();
> 29  |   await expect(kpiCards).toBeVisible({ timeout: 8_000 });
      |                          ^ Error: expect(locator).toBeVisible() failed
  30  | });
  31  | 
  32  | test("Resumen General — valor de KPI coincide con mock (paridad)", async ({ page }) => {
  33  |   // Override con datos precisos
  34  |   await page.route("**/api/v1/dashboard/kpis**", (r) =>
  35  |     r.fulfill({ json: MOCK_KPIS })
  36  |   );
  37  | 
  38  |   await page.goto("/resumen-general?pdi=PDI-2022-2026");
  39  |   await page.waitForLoadState("networkidle");
  40  |   await page.waitForTimeout(1_500);
  41  | 
  42  |   // Buscar el valor 120 (total indicadores del mock) en la página
  43  |   const pageContent = await page.content();
  44  |   // El valor 120 debe estar en el HTML como KPI
  45  |   // (puede estar como "120" o como parte de un componente)
  46  |   expect(pageContent).toMatch(/120/);
  47  | });
  48  | 
  49  | test("CMI Estratégico — carga el heading correcto", async ({ page }) => {
  50  |   await page.goto("/cmi-estrategico?pdi=PDI-2022-2026");
  51  |   await page.waitForLoadState("networkidle");
  52  | 
  53  |   const heading = page.getByRole("heading", { name: /cmi estratégico/i });
  54  |   await expect(heading).toBeVisible({ timeout: 8_000 });
  55  | });
  56  | 
  57  | test("CMI Estratégico — filtro de año visible", async ({ page }) => {
  58  |   await page.goto("/cmi-estrategico?pdi=PDI-2022-2026");
  59  |   await page.waitForLoadState("networkidle");
  60  |   await page.waitForTimeout(1_000);
  61  | 
  62  |   // El segmented control de años o un select de año debe aparecer
  63  |   const yearControl = page
  64  |     .getByRole("button", { name: /2025|2024|2023/ })
  65  |     .or(page.locator("select"))
  66  |     .first();
  67  | 
  68  |   // Solo verificar que existe algún control de filtrado
  69  |   const exists = await yearControl.isVisible().catch(() => false);
  70  |   // No fallamos si no está visible — puede ser que los datos no estén
  71  |   // Pero la página debe haber cargado
  72  |   const bodyText = await page.textContent("body");
  73  |   expect(bodyText?.length).toBeGreaterThan(100);
  74  | });
  75  | 
  76  | test("Plan de Mejoramiento — sección de filtros y KPIs visible", async ({ page }) => {
  77  |   await page.goto("/plan-mejoramiento");
  78  |   await page.waitForLoadState("networkidle");
  79  |   await page.waitForTimeout(1_000);
  80  | 
  81  |   const heading = page.getByRole("heading", { name: /plan de mejoramiento/i });
  82  |   await expect(heading).toBeVisible({ timeout: 8_000 });
  83  | });
  84  | 
  85  | test("Seguimiento Operativo — sección de filtros visible", async ({ page }) => {
  86  |   await page.goto("/seguimiento-operativo");
  87  |   await page.waitForLoadState("networkidle");
  88  |   await page.waitForTimeout(1_000);
  89  | 
  90  |   const heading = page.getByRole("heading", { name: /seguimiento operativo/i });
  91  |   await expect(heading).toBeVisible({ timeout: 8_000 });
  92  | });
  93  | 
  94  | test("Diagnóstico — checks del sistema visibles", async ({ page }) => {
  95  |   await page.goto("/diagnostico");
  96  |   await page.waitForLoadState("networkidle");
  97  |   await page.waitForTimeout(1_500);
  98  | 
  99  |   // La página de diagnóstico debe mostrar los checks
  100 |   const heading = page.getByRole("heading", { name: /diagnóstico/i });
  101 |   await expect(heading).toBeVisible({ timeout: 8_000 });
  102 | 
  103 |   // Debe mostrar al menos un check
  104 |   const checks = page.locator("div").filter({ hasText: /backend api|autenticación|datos cmi/i });
  105 |   await expect(checks.first()).toBeVisible({ timeout: 5_000 });
  106 | });
  107 | 
```