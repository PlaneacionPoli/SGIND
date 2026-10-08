# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> página raíz redirige a /login si no autenticado
- Location: e2e\login.spec.ts:60:5

# Error details

```
Error: expect(received).toMatch(expected)

Expected pattern: /\/(login|resumen-general)/
Received string:  "http://localhost:3000/menu"
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e4]:
    - banner [ref=e5]:
      - img "Politécnico Grancolombiano" [ref=e7]
      - generic [ref=e8]:
        - paragraph [ref=e9]: Buenos días, dev
        - heading "Panel de indicadores" [level=1] [ref=e10]
      - button "Sección Operativa" [ref=e11] [cursor=pointer]:
        - img [ref=e12]
        - text: Sección Operativa
      - generic [ref=e14]: calidad
    - generic [ref=e15]:
      - generic [ref=e16]:
        - img [ref=e17]
        - generic [ref=e29]:
          - link "Resumen General" [ref=e30] [cursor=pointer]:
            - /url: /resumen-general
            - img [ref=e32]
            - generic [ref=e33]: Resumen General
          - link "CMI Estratégico" [ref=e34] [cursor=pointer]:
            - /url: /cmi-estrategico
            - img [ref=e36]
            - generic [ref=e37]: CMI Estratégico
          - link "CMI por Procesos" [ref=e38] [cursor=pointer]:
            - /url: /cmi-procesos
            - img [ref=e40]
            - generic [ref=e41]: CMI por Procesos
      - generic [ref=e42]:
        - img [ref=e43]
        - generic [ref=e55]:
          - link "Informe por Procesos" [ref=e56] [cursor=pointer]:
            - /url: /informe-procesos
            - img [ref=e58]
            - generic [ref=e59]: Informe por Procesos
          - link "Indicadores POLISIGS" [ref=e60] [cursor=pointer]:
            - /url: /polisigs
            - img [ref=e62]
            - generic [ref=e63]: Indicadores POLISIGS
          - link "Plan de Mejoramiento" [ref=e64] [cursor=pointer]:
            - /url: /plan-mejoramiento
            - img [ref=e66]
            - generic [ref=e67]: Plan de Mejoramiento
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
  30 |   await expect(msBtn).toBeVisible({ timeout: 8_000 });
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
> 66 |   expect(page.url()).toMatch(/\/(login|resumen-general)/);
     |                      ^ Error: expect(received).toMatch(expected)
  67 | });
  68 | 
```