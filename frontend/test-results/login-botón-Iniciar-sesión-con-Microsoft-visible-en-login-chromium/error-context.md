# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> botón 'Iniciar sesión con Microsoft' visible en /login
- Location: e2e\login.spec.ts:26:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('link', { name: /iniciar sesión con microsoft/i })
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 8000ms
  - waiting for getByRole('link', { name: /iniciar sesión con microsoft/i })

```

```yaml
- alert
- banner:
  - img "Politécnico Grancolombiano"
  - paragraph: Buenos días, dev
  - heading "Panel de indicadores" [level=1]
  - button "Sección Operativa"
  - text: calidad
- link "Resumen General":
  - /url: /resumen-general
- link "CMI Estratégico":
  - /url: /cmi-estrategico
- link "CMI por Procesos":
  - /url: /cmi-procesos
- link "Informe por Procesos":
  - /url: /informe-procesos
- link "Indicadores POLISIGS":
  - /url: /polisigs
- link "Plan de Mejoramiento":
  - /url: /plan-mejoramiento
```

# Test source

```ts
  1  | /**
  2  |  * Tests E2E — Flujo de autenticación (Fase 7)
  3  |  *
  4  |  * Verifica:
  5  |  * - La página /login existe y carga correctamente
  6  |  * - El botón "Iniciar sesión con Microsoft" está presente
  7  |  * - El botón "Acceso de desarrollo" está visible en modo dev
  8  |  * - El AuthGuard redirige a /login cuando no hay sesión
  9  |  * - Tras el dev-login, el usuario queda autenticado
  10 |  */
  11 | 
  12 | import { test, expect } from "@playwright/test";
  13 | import { mockAPI, devLogin } from "./fixtures";
  14 | 
  15 | test.beforeEach(async ({ page }) => {
  16 |   await mockAPI(page);
  17 | });
  18 | 
  19 | test("página /login carga sin errores", async ({ page }) => {
  20 |   await page.goto("/login");
  21 |   await page.waitForLoadState("networkidle");
  22 |   await expect(page).not.toHaveTitle(/error/i);
  23 |   await expect(page.locator("body")).toBeVisible();
  24 | });
  25 | 
  26 | test("botón 'Iniciar sesión con Microsoft' visible en /login", async ({ page }) => {
  27 |   await page.goto("/login");
  28 |   await page.waitForLoadState("networkidle");
  29 |   const msBtn = page.getByRole("link", { name: /iniciar sesión con microsoft/i });
> 30 |   await expect(msBtn).toBeVisible({ timeout: 8_000 });
     |                       ^ Error: expect(locator).toBeVisible() failed
  31 | });
  32 | 
  33 | test("botón 'Acceso de desarrollo' visible en modo dev", async ({ page }) => {
  34 |   await page.goto("/login");
  35 |   await page.waitForLoadState("networkidle");
  36 |   const devBtn = page.getByRole("button", { name: /acceso de desarrollo/i });
  37 |   await expect(devBtn).toBeVisible({ timeout: 8_000 });
  38 | });
  39 | 
  40 | test("AuthGuard redirige a /login cuando no hay sesión", async ({ page }) => {
  41 |   // Ir directamente al dashboard sin autenticarse
  42 |   await page.goto("/resumen-general");
  43 |   await page.waitForLoadState("networkidle");
  44 |   await page.waitForTimeout(1_000);
  45 | 
  46 |   // Debe haber redirigido a /login
  47 |   expect(page.url()).toContain("/login");
  48 | });
  49 | 
  50 | test("después del dev-login el usuario queda autenticado", async ({ page }) => {
  51 |   await devLogin(page);
  52 | 
  53 |   // El header debe mostrar el email o el menú de usuario
  54 |   const header = page.locator("header");
  55 |   const headerText = await header.textContent();
  56 |   // Debe haber algo en el header que indique sesión activa (email o rol)
  57 |   expect(headerText).toBeTruthy();
  58 | });
  59 | 
  60 | test("página raíz redirige a /login si no autenticado", async ({ page }) => {
  61 |   await page.goto("/");
  62 |   await page.waitForLoadState("networkidle");
  63 |   await page.waitForTimeout(800);
  64 | 
  65 |   // Debe redirigir a /login o /resumen-general
  66 |   expect(page.url()).toMatch(/\/(login|resumen-general)/);
  67 | });
  68 | 
```