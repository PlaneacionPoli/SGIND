# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: kpis.spec.ts >> Resumen General — valor de KPI coincide con mock (paridad)
- Location: e2e\kpis.spec.ts:32:5

# Error details

```
Error: expect(received).toMatch(expected)

Expected pattern: /120/
Received string:  "<!DOCTYPE html><html id=\"__next_error__\"><head><link rel=\"stylesheet\" href=\"/_next/static/css/0a8f8ecf2aa33264.css\" data-precedence=\"next\"><script src=\"/_next/static/chunks/fd9d1056-f03b6d7356759837.js\" async=\"\"></script><script src=\"/_next/static/chunks/117-6e7025ba7430bb0a.js\" async=\"\"></script><script src=\"/_next/static/chunks/main-app-f730005f4900c503.js\" async=\"\"></script><script src=\"/_next/static/chunks/713-3779ef5b344f070a.js\" async=\"\"></script><script src=\"/_next/static/chunks/polyfills-42372ed130431b0a.js\" nomodule=\"\"></script><link rel=\"preload\" as=\"image\" fetchpriority=\"high\" imagesrcset=\"/_next/image?url=%2Fpoli-logo.png&amp;w=1920&amp;q=75 1x, /_next/image?url=%2Fpoli-logo.png&amp;w=3840&amp;q=75 2x\"></head><body><script src=\"/_next/static/chunks/webpack-1f26426ae93dbde7.js\" async=\"\"></script><script>(self.__next_f=self.__next_f||[]).push([0]);self.__next_f.push([2,null])</script><script>self.__next_f.push([1,\"1:HL[\\\"/_next/static/css/0a8f8ecf2aa33264.css\\\",\\\"style\\\"]\\n\"])</script><script>self.__next_f.push([1,\"2:I[12846,[],\\\"\\\"]\\n4:I[19107,[],\\\"ClientPageRoot\\\"]\\n5:I[49400,[\\\"189\\\",\\\"static/chunks/189-37f99f6bf308321a.js\\\",\\\"919\\\",\\\"static/chunks/919-a263102756c62912.js\\\",\\\"713\\\",\\\"static/chunks/713-3779ef5b344f070a.js\\\",\\\"448\\\",\\\"static/chunks/448-f4972ee9813e932b.js\\\",\\\"669\\\",\\\"static/chunks/669-7eebffdc3ca356ef.js\\\",\\\"9\\\",\\\"static/chunks/9-4a39470c46bf4539.js\\\",\\\"569\\\",\\\"static/chunks/app/(dashboard)/resumen-general/page-56ae072080fd2460.js\\\"],\\\"default\\\",1]\\n6:I[4707,[],\\\"\\\"]\\n7:I[36423,[],\\\"\\\"]\\n8:I[87327,[\\\"189\\\",\\\"static/chunks/189-37f99f6bf308321a.js\\\",\\\"448\\\",\\\"static/chunks/448-f4972ee9813e932b.js\\\",\\\"145\\\",\\\"static/chunks/145-c20f5e9fc7010c3f.js\\\",\\\"416\\\",\\\"static/chunks/416-20856b275f118891.js\\\",\\\"397\\\",\\\"static/chunks/397-f0f8be4476de9783.js\\\",\\\"642\\\",\\\"static/chunks/app/(dashboard)/layout-ab9f0d7afb78c3cf.js\\\"],\\\"AuthGuard\\\"]\\n9:I[70705,[\\\"189\\\",\\\"static/chunks/189-37f99f6bf308321a.js\\\",\\\"448\\\",\\\"static/chunks/448-f4972ee9813e932b.js\\\",\\\"145\\\",\\\"static/chunks/145-c20f5e9fc7010c3f.js\\\",\\\"416\\\",\\\"static/chunks/416-20856b275f118891.js\\\",\\\"397\\\",\\\"static/chunks/397-f0f8be4476de9783.js\\\",\\\"642\\\",\\\"static/chunks/app/(dashboard)/layout-ab9f0d7afb78c3cf.js\\\"],\\\"Sidebar\\\"]\\na:I[28278,[\\\"189\\\",\\\"static/chunks/189-37f99f6bf308321a.js\\\",\\\"448\\\",\\\"static/chunks/448-f4972ee9813e932b.js\\\",\\\"145\\\",\\\"static/chunks/145-c20f5e9fc7010c3f.js\\\",\\\"416\\\",\\\"static/chunks/416-20856b275f118891.js\\\",\\\"397\\\",\\\"static/chunks/397-f0f8be4476de9783.js\\\",\\\"642\\\",\\\"static/chunks/app/(dashboard)/layout-ab9f0d7afb78c3cf.js\\\"],\\\"Header\\\"]\\nb:I[37695,[\\\"189\\\",\\\"static/chunks/189-37f99f6bf308321a.js\\\",\\\"919\\\",\\\"static/chunks/919-a263102756c62912.js\\\",\\\"185\\\",\\\"static/chunks/app/layout-4255a1e68513a2f5.js\\\"],\\\"Providers\\\"]\\n11:I[61060,[],\\\"\\\"]\\nc:{\\\"fontFamily\\\":\\\"system-ui,\\\\\\\"Segoe UI\\\\\\\",Roboto,Helvetica,Arial,sans-serif,\\\\\\\"Apple Color Emoji\\\\\\\",\\\\\\\"Segoe UI Emoji\\\\\\\"\\\",\\\"height\\\":\\\"100vh\\\",\\\"textAlign\\\":\\\"center\\\",\\\"display\\\":\\\"flex\\\",\\\"flexDirection\\\":\\\"column\\\",\\\"alignItems\\\":\\\"center\\\",\\\"justifyContent\\\":\\\"center\\\"}\\nd:{\\\"display\\\":\\\"inline-block\\\",\\\"margin\\\":\\\"0 20px 0 0\\\",\\\"padding\\\":\\\"0 23px 0 0\\\",\\\"fontSize\\\":24,\\\"fontWeight\\\":500,\\\"verticalAlign\\\":\\\"top\\\",\\\"lineHeight\\\":\\\"49px\\\"}\\ne:{\\\"display\\\":\\\"inline-block\\\"}\\nf:{\\\"fontSize\\\":14,\\\"fontWeigh\"])</script><script>self.__next_f.push([1,\"t\\\":400,\\\"lineHeight\\\":\\\"49px\\\",\\\"margin\\\":0}\\n12:[]\\n\"])</script><script>self.__next_f.push([1,\"0:[\\\"$\\\",\\\"$L2\\\",null,{\\\"buildId\\\":\\\"NrD-_ZC7iitdchMGMVbVp\\\",\\\"assetPrefix\\\":\\\"\\\",\\\"urlParts\\\":[\\\"\\\",\\\"resumen-general\\\"],\\\"initialTree\\\":[\\\"\\\",{\\\"children\\\":[\\\"(dashboard)\\\",{\\\"children\\\":[\\\"resumen-general\\\",{\\\"children\\\":[\\\"__PAGE__\\\",{}]}]}]},\\\"$undefined\\\",\\\"$undefined\\\",true],\\\"initialSeedData\\\":[\\\"\\\",{\\\"children\\\":[\\\"(dashboard)\\\",{\\\"children\\\":[\\\"resumen-general\\\",{\\\"children\\\":[\\\"__PAGE__\\\",{},[[\\\"$L3\\\",[\\\"$\\\",\\\"$L4\\\",null,{\\\"props\\\":{\\\"params\\\":{},\\\"searchParams\\\":{}},\\\"Component\\\":\\\"$5\\\"}],null],null],null]},[null,[\\\"$\\\",\\\"$L6\\\",null,{\\\"parallelRouterKey\\\":\\\"children\\\",\\\"segmentPath\\\":[\\\"children\\\",\\\"(dashboard)\\\",\\\"children\\\",\\\"resumen-general\\\",\\\"children\\\"],\\\"error\\\":\\\"$undefined\\\",\\\"errorStyles\\\":\\\"$undefined\\\",\\\"errorScripts\\\":\\\"$undefined\\\",\\\"template\\\":[\\\"$\\\",\\\"$L7\\\",null,{}],\\\"templateStyles\\\":\\\"$undefined\\\",\\\"templateScripts\\\":\\\"$undefined\\\",\\\"notFound\\\":\\\"$undefined\\\",\\\"notFoundStyles\\\":\\\"$undefined\\\"}]],null]},[[null,[\\\"$\\\",\\\"$L8\\\",null,{\\\"children\\\":[\\\"$\\\",\\\"div\\\",null,{\\\"className\\\":\\\"flex h-screen overflow-hidden bg-slate-50\\\",\\\"children\\\":[[\\\"$\\\",\\\"$L9\\\",null,{}],[\\\"$\\\",\\\"div\\\",null,{\\\"className\\\":\\\"flex flex-1 flex-col overflow-hidden\\\",\\\"children\\\":[[\\\"$\\\",\\\"$La\\\",null,{}],[\\\"$\\\",\\\"main\\\",null,{\\\"className\\\":\\\"flex-1 overflow-y-auto p-6\\\",\\\"children\\\":[\\\"$\\\",\\\"$L6\\\",null,{\\\"parallelRouterKey\\\":\\\"children\\\",\\\"segmentPath\\\":[\\\"children\\\",\\\"(dashboard)\\\",\\\"children\\\"],\\\"error\\\":\\\"$undefined\\\",\\\"errorStyles\\\":\\\"$undefined\\\",\\\"errorScripts\\\":\\\"$undefined\\\",\\\"template\\\":[\\\"$\\\",\\\"$L7\\\",null,{}],\\\"templateStyles\\\":\\\"$undefined\\\",\\\"templateScripts\\\":\\\"$undefined\\\",\\\"notFound\\\":[[\\\"$\\\",\\\"title\\\",null,{\\\"children\\\":\\\"404: This page could not be found.\\\"}],[\\\"$\\\",\\\"div\\\",null,{\\\"style\\\":{\\\"fontFamily\\\":\\\"system-ui,\\\\\\\"Segoe UI\\\\\\\",Roboto,Helvetica,Arial,sans-serif,\\\\\\\"Apple Color Emoji\\\\\\\",\\\\\\\"Segoe UI Emoji\\\\\\\"\\\",\\\"height\\\":\\\"100vh\\\",\\\"textAlign\\\":\\\"center\\\",\\\"display\\\":\\\"flex\\\",\\\"flexDirection\\\":\\\"column\\\",\\\"alignItems\\\":\\\"center\\\",\\\"justifyContent\\\":\\\"center\\\"},\\\"children\\\":[\\\"$\\\",\\\"div\\\",null,{\\\"children\\\":[[\\\"$\\\",\\\"style\\\",null,{\\\"dangerouslySetInnerHTML\\\":{\\\"__html\\\":\\\"body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}\\\"}}],[\\\"$\\\",\\\"h1\\\",null,{\\\"className\\\":\\\"next-error-h1\\\",\\\"style\\\":{\\\"display\\\":\\\"inline-block\\\",\\\"margin\\\":\\\"0 20px 0 0\\\",\\\"padding\\\":\\\"0 23px 0 0\\\",\\\"fontSize\\\":24,\\\"fontWeight\\\":500,\\\"verticalAlign\\\":\\\"top\\\",\\\"lineHeight\\\":\\\"49px\\\"},\\\"children\\\":\\\"404\\\"}],[\\\"$\\\",\\\"div\\\",null,{\\\"style\\\":{\\\"display\\\":\\\"inline-block\\\"},\\\"children\\\":[\\\"$\\\",\\\"h2\\\",null,{\\\"style\\\":{\\\"fontSize\\\":14,\\\"fontWeight\\\":400,\\\"lineHeight\\\":\\\"49px\\\",\\\"margin\\\":0},\\\"children\\\":\\\"This page could not be found.\\\"}]}]]}]}]],\\\"notFoundStyles\\\":[]}]}]]}]]}]}]],null],null]},[[[[\\\"$\\\",\\\"link\\\",\\\"0\\\",{\\\"rel\\\":\\\"stylesheet\\\",\\\"href\\\":\\\"/_next/static/css/0a8f8ecf2aa33264.css\\\",\\\"precedence\\\":\\\"next\\\",\\\"crossOrigin\\\":\\\"$undefined\\\"}]],[\\\"$\\\",\\\"html\\\",null,{\\\"lang\\\":\\\"es\\\",\\\"children\\\":[\\\"$\\\",\\\"body\\\",null,{\\\"className\\\":\\\"__variable_d8ebd1 font-sans antialiased\\\",\\\"children\\\":[\\\"$\\\",\\\"$Lb\\\",null,{\\\"children\\\":[\\\"$\\\",\\\"$L6\\\",null,{\\\"parallelRouterKey\\\":\\\"children\\\",\\\"segmentPath\\\":[\\\"children\\\"],\\\"error\\\":\\\"$undefined\\\",\\\"errorStyles\\\":\\\"$undefined\\\",\\\"errorScripts\\\":\\\"$undefined\\\",\\\"template\\\":[\\\"$\\\",\\\"$L7\\\",null,{}],\\\"templateStyles\\\":\\\"$undefined\\\",\\\"templateScripts\\\":\\\"$undefined\\\",\\\"notFound\\\":[[\\\"$\\\",\\\"title\\\",null,{\\\"children\\\":\\\"404: This page could not be found.\\\"}],[\\\"$\\\",\\\"div\\\",null,{\\\"style\\\":\\\"$c\\\",\\\"children\\\":[\\\"$\\\",\\\"div\\\",null,{\\\"children\\\":[[\\\"$\\\",\\\"style\\\",null,{\\\"dangerouslySetInnerHTML\\\":{\\\"__html\\\":\\\"body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}\\\"}}],[\\\"$\\\",\\\"h1\\\",null,{\\\"className\\\":\\\"next-error-h1\\\",\\\"style\\\":\\\"$d\\\",\\\"children\\\":\\\"404\\\"}],[\\\"$\\\",\\\"div\\\",null,{\\\"style\\\":\\\"$e\\\",\\\"children\\\":[\\\"$\\\",\\\"h2\\\",null,{\\\"style\\\":\\\"$f\\\",\\\"children\\\":\\\"This page could not be found.\\\"}]}]]}]}]],\\\"notFoundStyles\\\":[]}]}]}]}]],null],null],\\\"couldBeIntercepted\\\":false,\\\"initialHead\\\":[null,\\\"$L10\\\"],\\\"globalErrorComponent\\\":\\\"$11\\\",\\\"missingSlots\\\":\\\"$W12\\\"}]\\n\"])</script><script>self.__next_f.push([1,\"10:[[\\\"$\\\",\\\"meta\\\",\\\"0\\\",{\\\"name\\\":\\\"viewport\\\",\\\"content\\\":\\\"width=device-width, initial-scale=1\\\"}],[\\\"$\\\",\\\"meta\\\",\\\"1\\\",{\\\"charSet\\\":\\\"utf-8\\\"}],[\\\"$\\\",\\\"title\\\",\\\"2\\\",{\\\"children\\\":\\\"SGIND — Sistema de Indicadores\\\"}],[\\\"$\\\",\\\"meta\\\",\\\"3\\\",{\\\"name\\\":\\\"description\\\",\\\"content\\\":\\\"Sistema de Gestión de Indicadores Institucionales — Politécnico Grancolombiano\\\"}],[\\\"$\\\",\\\"link\\\",\\\"4\\\",{\\\"rel\\\":\\\"icon\\\",\\\"href\\\":\\\"/favicon.ico\\\",\\\"type\\\":\\\"image/x-icon\\\",\\\"sizes\\\":\\\"16x16\\\"}]]\\n3:null\\n\"])</script><div style=\"font-family: system-ui, &quot;Segoe UI&quot;, Roboto, Helvetica, Arial, sans-serif, &quot;Apple Color Emoji&quot;, &quot;Segoe UI Emoji&quot;; height: 100vh; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;\"><div><h2 style=\"font-size: 14px; font-weight: 400; line-height: 28px; margin: 0px 8px;\">Application error: a client-side exception has occurred (see the browser console for more information).</h2></div></div></body></html>"
```

# Page snapshot

```yaml
- 'heading "Application error: a client-side exception has occurred (see the browser console for more information)." [level=2] [ref=e4]'
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
  29  |   await expect(kpiCards).toBeVisible({ timeout: 8_000 });
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
> 46  |   expect(pageContent).toMatch(/120/);
      |                       ^ Error: expect(received).toMatch(expected)
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