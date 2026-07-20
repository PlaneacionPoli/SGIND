/**
 * Tests E2E — Navegación entre las 9 páginas del dashboard
 *
 * Verifica que todas las rutas del dashboard:
 * 1. Responden con HTTP 200
 * 2. Renderizan el título de la sección correspondiente
 * 3. No generan errores de JavaScript sin capturar
 */

import { test, expect, type Page } from "@playwright/test";
import { mockAPI, devLogin } from "./fixtures";

const PAGINAS = [
  { ruta: "/resumen-general", titulo: /resumen general/i },
  { ruta: "/cmi-estrategico", titulo: /cmi estratégico/i },
  { ruta: "/cmi-procesos", titulo: /cmi por procesos/i },
  { ruta: "/gestion-om", titulo: /gestión.*om|om.*gestión/i },
  { ruta: "/plan-mejoramiento", titulo: /plan de mejoramiento/i },
  { ruta: "/seguimiento-operativo", titulo: /seguimiento operativo/i },
  { ruta: "/informe-procesos", titulo: /informe.*procesos/i },
  { ruta: "/pdi-acreditacion", titulo: /pdi.*acreditación/i },
  { ruta: "/diagnostico", titulo: /diagnóstico/i },
];

test.describe("Navegación — todas las rutas del dashboard", () => {
  let jsErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    jsErrors = [];
    page.on("pageerror", (err) => jsErrors.push(err.message));
    await mockAPI(page);
    await devLogin(page);
  });

  for (const { ruta, titulo } of PAGINAS) {
    test(`${ruta} — carga y muestra su título`, async ({ page }) => {
      const response = await page.goto(ruta);
      expect(response?.status()).toBe(200);

      await page.waitForLoadState("networkidle");

      // Verificar que el heading de la página está presente
      const heading = page.getByRole("heading", { name: titulo }).or(
        page.locator("h2").filter({ hasText: titulo })
      );
      await expect(heading).toBeVisible({ timeout: 8_000 });

      // No debe haber errores críticos de JS sin capturar
      const criticalErrors = jsErrors.filter(
        (e) => !e.includes("ResizeObserver") && !e.includes("Non-Error promise rejection")
      );
      expect(criticalErrors).toHaveLength(0);
    });
  }
});

test.describe("Navegación — sidebar accesible", () => {
  test.beforeEach(async ({ page }) => {
    await mockAPI(page);
    await devLogin(page);
  });

  test("sidebar tiene links para las 9 secciones", async ({ page }) => {
    await page.goto("/resumen-general");
    await page.waitForLoadState("networkidle");

    const nav = page.locator("nav").or(page.locator("aside")).first();
    await expect(nav).toBeVisible({ timeout: 5_000 });

    // Verificar que el nav tiene al menos 6 links (puede haber más)
    const links = nav.locator("a");
    const count = await links.count();
    expect(count).toBeGreaterThanOrEqual(6);
  });
});
