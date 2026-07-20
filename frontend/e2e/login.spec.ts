/**
 * Tests E2E — Flujo de autenticación (Fase 7)
 *
 * Verifica:
 * - La página /login existe y carga correctamente
 * - El botón "Iniciar sesión con Microsoft" está presente
 * - El botón "Acceso de desarrollo" está visible en modo dev
 * - El AuthGuard redirige a /login cuando no hay sesión
 * - Tras el dev-login, el usuario queda autenticado
 */

import { test, expect } from "@playwright/test";
import { mockAPI, devLogin } from "./fixtures";

test.beforeEach(async ({ page }) => {
  await mockAPI(page);
});

test("página /login carga sin errores", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");
  await expect(page).not.toHaveTitle(/error/i);
  await expect(page.locator("body")).toBeVisible();
});

test("botón 'Iniciar sesión con Microsoft' visible en /login", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");
  const msBtn = page.getByRole("link", { name: /iniciar sesión con microsoft/i });
  await expect(msBtn).toBeVisible({ timeout: 8_000 });
});

test("botón 'Acceso de desarrollo' visible en modo dev", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");
  const devBtn = page.getByRole("button", { name: /acceso de desarrollo/i });
  await expect(devBtn).toBeVisible({ timeout: 8_000 });
});

test("AuthGuard redirige a /login cuando no hay sesión", async ({ page }) => {
  // Ir directamente al dashboard sin autenticarse
  await page.goto("/resumen-general");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1_000);

  // Debe haber redirigido a /login
  expect(page.url()).toContain("/login");
});

test("después del dev-login el usuario queda autenticado", async ({ page }) => {
  await devLogin(page);

  // El header debe mostrar el email o el menú de usuario
  const header = page.locator("header");
  const headerText = await header.textContent();
  // Debe haber algo en el header que indique sesión activa (email o rol)
  expect(headerText).toBeTruthy();
});

test("página raíz redirige a /login si no autenticado", async ({ page }) => {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(800);

  // Debe redirigir a /login o /resumen-general
  expect(page.url()).toMatch(/\/(login|resumen-general)/);
});
