# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navegacion.spec.ts >> Navegación — selección de PDI >> entrar a un módulo sin PDI muestra el selector con ambos ciclos
- Location: e2e\navegacion.spec.ts:85:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('PDI 2022-2026')
Expected: visible
Error: strict mode violation: getByText('PDI 2022-2026') resolved to 2 elements:
    1) <div class="flex h-56 items-center justify-center text-3xl font-bold text-white bg-gradient-to-br from-slate-500 to-slate-800">PDI 2022-2026</div> aka getByRole('link', { name: 'PDI 2022-2026 Cerrado PDI' })
    2) <p class="text-base font-semibold text-slate-900">PDI 2022-2026</p> aka getByRole('link', { name: 'PDI 2022-2026 Cerrado PDI' })

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('PDI 2022-2026')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e4]:
      - generic [ref=e5]:
        - generic [ref=e6]:
          - img "Politécnico Grancolombiano"
        - heading "Sistema de Indicadores" [level=1] [ref=e7]
      - navigation [ref=e8]:
        - link "Menú principal" [ref=e9] [cursor=pointer]:
          - /url: /menu
          - img [ref=e10]
          - generic [ref=e12]: Menú principal
        - list [ref=e13]:
          - listitem [ref=e14]:
            - link "Resumen General" [ref=e15] [cursor=pointer]:
              - /url: /resumen-general
              - img [ref=e16]
              - generic [ref=e21]: Resumen General
          - listitem [ref=e22]:
            - link "CMI Estratégico" [ref=e23] [cursor=pointer]:
              - /url: /cmi-estrategico
              - img [ref=e24]
              - generic [ref=e28]: CMI Estratégico
          - listitem [ref=e29]:
            - link "CMI por Procesos" [ref=e30] [cursor=pointer]:
              - /url: /cmi-procesos
              - img [ref=e31]
              - generic [ref=e35]: CMI por Procesos
          - listitem [ref=e36]:
            - link "Informe por Procesos" [ref=e37] [cursor=pointer]:
              - /url: /informe-procesos
              - img [ref=e38]
              - generic [ref=e41]: Informe por Procesos
          - listitem [ref=e42]:
            - link "Indicadores POLISIGS" [ref=e43] [cursor=pointer]:
              - /url: /polisigs
              - img [ref=e44]
              - generic [ref=e47]: Indicadores POLISIGS
          - listitem [ref=e48]:
            - link "Plan de Mejoramiento" [ref=e49] [cursor=pointer]:
              - /url: /plan-mejoramiento
              - img [ref=e50]
              - generic [ref=e54]: Plan de Mejoramiento
          - listitem [ref=e55]:
            - link "Seguimiento Operativo" [ref=e56] [cursor=pointer]:
              - /url: /seguimiento-operativo
              - img [ref=e57]
              - generic [ref=e59]: Seguimiento Operativo
          - listitem [ref=e60]:
            - link "Gestión OM" [ref=e61] [cursor=pointer]:
              - /url: /gestion-om
              - img [ref=e62]
              - generic [ref=e64]: Gestión OM
      - generic [ref=e65]:
        - text: Politécnico Grancolombiano
        - text: Gerencia de Planeación
        - text: Medición y Mejora
    - generic [ref=e66]:
      - banner [ref=e67]:
        - generic [ref=e68]: Panel de indicadores institucionales
        - generic [ref=e69]:
          - generic [ref=e70]:
            - generic [ref=e71]: dev@poligran.edu.co
            - generic [ref=e72]: "Rol: calidad"
          - button "Cerrar sesión" [ref=e73] [cursor=pointer]
      - main [ref=e74]:
        - generic [ref=e75]:
          - generic [ref=e76]:
            - paragraph [ref=e77]: CMI Estratégico
            - heading "Selecciona el Plan de Desarrollo Institucional" [level=2] [ref=e78]
            - paragraph [ref=e79]: Cada PDI tiene su propio catálogo de indicadores, líneas, objetivos y metas estratégicas.
          - generic [ref=e80]:
            - 'link "PDI 2026-2030 Vigente PDI 2026-2030 Plan de Desarrollo Institucional 2026-2030 (ciclo vigente) Datos 2026–2030 Disponible: CMI Estratégico · CMI por Procesos Entrar →" [ref=e81] [cursor=pointer]':
              - /url: /cmi-estrategico?pdi=PDI-2026-2030
              - generic [ref=e82]:
                - generic [ref=e83]: PDI 2026-2030
                - generic [ref=e84]: Vigente
              - generic [ref=e85]:
                - generic [ref=e86]:
                  - paragraph [ref=e87]: PDI 2026-2030
                  - paragraph [ref=e88]: Plan de Desarrollo Institucional 2026-2030 (ciclo vigente)
                  - paragraph [ref=e89]: Datos 2026–2030
                  - paragraph [ref=e90]: "Disponible: CMI Estratégico · CMI por Procesos"
                - generic [ref=e91]: Entrar →
            - link "PDI 2022-2026 Cerrado PDI 2022-2026 Plan de Desarrollo Institucional 2022-2026 (ciclo cerrado) Datos 2022–2025 Entrar →" [ref=e92] [cursor=pointer]:
              - /url: /cmi-estrategico?pdi=PDI-2022-2026
              - generic [ref=e93]:
                - generic [ref=e94]: PDI 2022-2026
                - generic [ref=e95]: Cerrado
              - generic [ref=e96]:
                - generic [ref=e97]:
                  - paragraph [ref=e98]: PDI 2022-2026
                  - paragraph [ref=e99]: Plan de Desarrollo Institucional 2022-2026 (ciclo cerrado)
                  - paragraph [ref=e100]: Datos 2022–2025
                - generic [ref=e101]: Entrar →
  - alert [ref=e102]
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
  48  |       await expect(heading).toBeVisible({ timeout: 8_000 });
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
> 88  |     await expect(page.getByText("PDI 2022-2026")).toBeVisible();
      |                                                   ^ Error: expect(locator).toBeVisible() failed
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