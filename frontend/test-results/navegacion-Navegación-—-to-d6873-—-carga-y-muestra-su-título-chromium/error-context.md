# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navegacion.spec.ts >> Navegación — todas las rutas del dashboard >> /cmi-estrategico — carga y muestra su título
- Location: e2e\navegacion.spec.ts:38:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: /cmi estratégico/i }).or(locator('h2').filter({ hasText: /cmi estratégico/i }))
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 8000ms
  - waiting for getByRole('heading', { name: /cmi estratégico/i }).or(locator('h2').filter({ hasText: /cmi estratégico/i }))

```

```yaml
- complementary:
  - img "Politécnico Grancolombiano"
  - heading "Sistema de Indicadores" [level=1]
  - navigation:
    - link "Menú principal":
      - /url: /menu
    - list:
      - listitem:
        - link "Resumen General":
          - /url: /resumen-general
      - listitem:
        - link "CMI Estratégico":
          - /url: /cmi-estrategico
      - listitem:
        - link "CMI por Procesos":
          - /url: /cmi-procesos
      - listitem:
        - link "Informe por Procesos":
          - /url: /informe-procesos
      - listitem:
        - link "Indicadores POLISIGS":
          - /url: /polisigs
      - listitem:
        - link "Plan de Mejoramiento":
          - /url: /plan-mejoramiento
      - listitem:
        - link "Seguimiento Operativo":
          - /url: /seguimiento-operativo
      - listitem:
        - link "Gestión OM":
          - /url: /gestion-om
  - text: Politécnico Grancolombiano Gerencia de Planeación Medición y Mejora
- banner:
  - text: "Panel de indicadores institucionales dev@poligran.edu.co Rol: calidad"
  - button "Cerrar sesión"
- main:
  - paragraph: CMI Estratégico
  - heading "Selecciona el Plan de Desarrollo Institucional" [level=2]
  - paragraph: Cada PDI tiene su propio catálogo de indicadores, líneas, objetivos y metas estratégicas.
  - 'link "PDI 2026-2030 Vigente PDI 2026-2030 Plan de Desarrollo Institucional 2026-2030 (ciclo vigente) Datos 2026–2030 Disponible: CMI Estratégico · CMI por Procesos Entrar →"':
    - /url: /cmi-estrategico?pdi=PDI-2026-2030
    - text: PDI 2026-2030 Vigente
    - paragraph: PDI 2026-2030
    - paragraph: Plan de Desarrollo Institucional 2026-2030 (ciclo vigente)
    - paragraph: Datos 2026–2030
    - paragraph: "Disponible: CMI Estratégico · CMI por Procesos"
    - text: Entrar →
  - link "PDI 2022-2026 Cerrado PDI 2022-2026 Plan de Desarrollo Institucional 2022-2026 (ciclo cerrado) Datos 2022–2025 Entrar →":
    - /url: /cmi-estrategico?pdi=PDI-2022-2026
    - text: PDI 2022-2026 Cerrado
    - paragraph: PDI 2022-2026
    - paragraph: Plan de Desarrollo Institucional 2022-2026 (ciclo cerrado)
    - paragraph: Datos 2022–2025
    - text: Entrar →
- alert
```

# Test source

```ts
  1   | /**
  2   |  * Tests E2E — Navegación entre las 7 páginas del dashboard
  3   |  *
  4   |  * Verifica que todas las rutas del dashboard:
  5   |  * 1. Responden con HTTP 200
  6   |  * 2. Renderizan el título de la sección correspondiente
  7   |  * 3. No generan errores de JavaScript sin capturar
  8   |  *
  9   |  * No incluye /diagnostico (herramienta interna, deliberadamente sin enlace
  10  |  * de navegación y gateada fuera de desarrollo — ver docs/tecnico/09-gaps-y-riesgos.md
  11  |  * G-16) ni /pdi-acreditacion (módulo eliminado, mismo hallazgo).
  12  |  */
  13  | 
  14  | import { test, expect, type Page } from "@playwright/test";
  15  | import { mockAPI, devLogin } from "./fixtures";
  16  | 
  17  | const PAGINAS = [
  18  |   { ruta: "/resumen-general", titulo: /resumen general/i },
  19  |   { ruta: "/cmi-estrategico", titulo: /cmi estratégico/i },
  20  |   { ruta: "/cmi-procesos", titulo: /cmi por procesos/i },
  21  |   { ruta: "/gestion-om", titulo: /gestión.*om|om.*gestión/i },
  22  |   { ruta: "/plan-mejoramiento", titulo: /plan de mejoramiento/i },
  23  |   { ruta: "/seguimiento-operativo", titulo: /seguimiento operativo/i },
  24  |   { ruta: "/informe-procesos", titulo: /informe.*procesos/i },
  25  | ];
  26  | 
  27  | test.describe("Navegación — todas las rutas del dashboard", () => {
  28  |   let jsErrors: string[] = [];
  29  | 
  30  |   test.beforeEach(async ({ page }) => {
  31  |     jsErrors = [];
  32  |     page.on("pageerror", (err) => jsErrors.push(err.message));
  33  |     await mockAPI(page);
  34  |     await devLogin(page);
  35  |   });
  36  | 
  37  |   for (const { ruta, titulo } of PAGINAS) {
  38  |     test(`${ruta} — carga y muestra su título`, async ({ page }) => {
  39  |       const response = await page.goto(ruta);
  40  |       expect(response?.status()).toBe(200);
  41  | 
  42  |       await page.waitForLoadState("networkidle");
  43  | 
  44  |       // Verificar que el heading de la página está presente
  45  |       const heading = page.getByRole("heading", { name: titulo }).or(
  46  |         page.locator("h2").filter({ hasText: titulo })
  47  |       );
> 48  |       await expect(heading).toBeVisible({ timeout: 8_000 });
      |                             ^ Error: expect(locator).toBeVisible() failed
  49  | 
  50  |       // No debe haber errores críticos de JS sin capturar
  51  |       const criticalErrors = jsErrors.filter(
  52  |         (e) => !e.includes("ResizeObserver") && !e.includes("Non-Error promise rejection")
  53  |       );
  54  |       expect(criticalErrors).toHaveLength(0);
  55  |     });
  56  |   }
  57  | });
  58  | 
  59  | test.describe("Navegación — sidebar accesible", () => {
  60  |   test.beforeEach(async ({ page }) => {
  61  |     await mockAPI(page);
  62  |     await devLogin(page);
  63  |   });
  64  | 
  65  |   test("sidebar tiene links para las 9 secciones", async ({ page }) => {
  66  |     await page.goto("/resumen-general");
  67  |     await page.waitForLoadState("networkidle");
  68  | 
  69  |     const nav = page.locator("nav").or(page.locator("aside")).first();
  70  |     await expect(nav).toBeVisible({ timeout: 5_000 });
  71  | 
  72  |     // Verificar que el nav tiene al menos 6 links (puede haber más)
  73  |     const links = nav.locator("a");
  74  |     const count = await links.count();
  75  |     expect(count).toBeGreaterThanOrEqual(6);
  76  |   });
  77  | });
  78  | 
  79  | test.describe("Navegación — selección de PDI", () => {
  80  |   test.beforeEach(async ({ page }) => {
  81  |     await mockAPI(page);
  82  |     await devLogin(page);
  83  |   });
  84  | 
  85  |   test("entrar a un módulo sin PDI muestra el selector con ambos ciclos", async ({ page }) => {
  86  |     await page.goto("/cmi-estrategico");
  87  |     await page.waitForURL(/\/seleccion-pdi\?destino=%2Fcmi-estrategico/);
  88  |     await expect(page.getByText("PDI 2022-2026")).toBeVisible();
  89  |     await expect(page.getByText("PDI 2026-2030")).toBeVisible();
  90  | 
  91  |     await page.getByRole("link", { name: /PDI 2022-2026/ }).click();
  92  |     await page.waitForURL(/\/cmi-estrategico\?pdi=PDI-2022-2026/);
  93  |     await expect(page.locator("h2").filter({ hasText: /cmi estratégico/i })).toBeVisible();
  94  |   });
  95  | 
  96  |   test("un módulo no habilitado para el PDI muestra aviso y no datos de otro ciclo", async ({ page }) => {
  97  |     await page.goto("/resumen-general?pdi=PDI-2026-2030");
  98  |     await expect(page.getByText(/módulo en preparación/i)).toBeVisible();
  99  |   });
  100 | });
  101 | 
  102 | 
```