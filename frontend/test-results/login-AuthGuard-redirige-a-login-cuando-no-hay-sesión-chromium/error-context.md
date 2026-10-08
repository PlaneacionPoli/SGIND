# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> AuthGuard redirige a /login cuando no hay sesión
- Location: e2e\login.spec.ts:40:5

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "/login"
Received string:    "http://localhost:3000/seleccion-pdi?destino=%2Fresumen-general"
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - complementary [ref=e5]:
      - generic [ref=e6]:
        - generic [ref=e7]:
          - img "Politécnico Grancolombiano"
        - heading "Sistema de Indicadores" [level=1] [ref=e8]
      - navigation [ref=e9]:
        - link "Menú principal" [ref=e10] [cursor=pointer]:
          - /url: /menu
          - img [ref=e11]
          - generic [ref=e13]: Menú principal
        - list [ref=e14]:
          - listitem [ref=e15]:
            - link "Resumen General" [ref=e16] [cursor=pointer]:
              - /url: /resumen-general
              - img [ref=e17]
              - generic [ref=e22]: Resumen General
          - listitem [ref=e23]:
            - link "CMI Estratégico" [ref=e24] [cursor=pointer]:
              - /url: /cmi-estrategico
              - img [ref=e25]
              - generic [ref=e29]: CMI Estratégico
          - listitem [ref=e30]:
            - link "CMI por Procesos" [ref=e31] [cursor=pointer]:
              - /url: /cmi-procesos
              - img [ref=e32]
              - generic [ref=e36]: CMI por Procesos
          - listitem [ref=e37]:
            - link "Informe por Procesos" [ref=e38] [cursor=pointer]:
              - /url: /informe-procesos
              - img [ref=e39]
              - generic [ref=e42]: Informe por Procesos
          - listitem [ref=e43]:
            - link "Indicadores POLISIGS" [ref=e44] [cursor=pointer]:
              - /url: /polisigs
              - img [ref=e45]
              - generic [ref=e48]: Indicadores POLISIGS
          - listitem [ref=e49]:
            - link "Plan de Mejoramiento" [ref=e50] [cursor=pointer]:
              - /url: /plan-mejoramiento
              - img [ref=e51]
              - generic [ref=e55]: Plan de Mejoramiento
          - listitem [ref=e56]:
            - link "Seguimiento Operativo" [ref=e57] [cursor=pointer]:
              - /url: /seguimiento-operativo
              - img [ref=e58]
              - generic [ref=e60]: Seguimiento Operativo
          - listitem [ref=e61]:
            - link "Gestión OM" [ref=e62] [cursor=pointer]:
              - /url: /gestion-om
              - img [ref=e63]
              - generic [ref=e65]: Gestión OM
      - generic [ref=e66]:
        - text: Politécnico Grancolombiano
        - text: Gerencia de Planeación
        - text: Medición y Mejora
    - generic [ref=e67]:
      - banner [ref=e68]:
        - generic [ref=e69]: Panel de indicadores institucionales
        - generic [ref=e70]:
          - generic [ref=e71]:
            - generic [ref=e72]: dev@poligran.edu.co
            - generic [ref=e73]: "Rol: calidad"
          - button "Cerrar sesión" [ref=e74] [cursor=pointer]
      - main [ref=e75]:
        - generic [ref=e76]:
          - generic [ref=e77]:
            - paragraph [ref=e78]: Resumen General
            - heading "Selecciona el Plan de Desarrollo Institucional" [level=2] [ref=e79]
            - paragraph [ref=e80]: Cada PDI tiene su propio catálogo de indicadores, líneas, objetivos y metas estratégicas.
          - generic [ref=e81]:
            - 'link "PDI 2026-2030 Vigente PDI 2026-2030 Plan de Desarrollo Institucional 2026-2030 (ciclo vigente) Datos 2026–2030 Disponible: CMI Estratégico · CMI por Procesos Entrar →" [ref=e82] [cursor=pointer]':
              - /url: /resumen-general?pdi=PDI-2026-2030
              - generic [ref=e83]:
                - generic [ref=e84]: PDI 2026-2030
                - generic [ref=e85]: Vigente
              - generic [ref=e86]:
                - generic [ref=e87]:
                  - paragraph [ref=e88]: PDI 2026-2030
                  - paragraph [ref=e89]: Plan de Desarrollo Institucional 2026-2030 (ciclo vigente)
                  - paragraph [ref=e90]: Datos 2026–2030
                  - paragraph [ref=e91]: "Disponible: CMI Estratégico · CMI por Procesos"
                - generic [ref=e92]: Entrar →
            - link "PDI 2022-2026 Cerrado PDI 2022-2026 Plan de Desarrollo Institucional 2022-2026 (ciclo cerrado) Datos 2022–2025 Entrar →" [ref=e93] [cursor=pointer]:
              - /url: /resumen-general?pdi=PDI-2022-2026
              - generic [ref=e94]:
                - generic [ref=e95]: PDI 2022-2026
                - generic [ref=e96]: Cerrado
              - generic [ref=e97]:
                - generic [ref=e98]:
                  - paragraph [ref=e99]: PDI 2022-2026
                  - paragraph [ref=e100]: Plan de Desarrollo Institucional 2022-2026 (ciclo cerrado)
                  - paragraph [ref=e101]: Datos 2022–2025
                - generic [ref=e102]: Entrar →
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
> 47 |   expect(page.url()).toContain("/login");
     |                      ^ Error: expect(received).toContain(expected) // indexOf
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