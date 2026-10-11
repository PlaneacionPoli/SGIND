import { describe, expect, it } from "vitest";
import type { OMFila } from "@/lib/types";
import { agruparPorTipoAccion } from "./GraficosOM";
import { contarPorEstado, estadoOM, filtrarFilas, formatNumero, ordenarFilas, validarRegistro } from "./utils";

const fila = (o: Partial<OMFila>): OMFila => ({
  id: "1",
  indicador: "Indicador",
  proceso: "P",
  subproceso: "S",
  periodicidad: "Anual",
  meta: 10,
  ejecucion: 1,
  cumplimiento_pct: 10,
  categoria: "Peligro",
  categoria_color: "#f00",
  tipo_accion: "Sin acción",
  tipo_accion_color: "#999",
  tiene_om: 0,
  numero_om: "",
  comentario: "",
  om_id: null,
  avance_om: null,
  row_bg: "#fff",
  ...o,
});

const FILAS = [
  fila({ id: "10", indicador: "Gestión de Residuos", proceso: "GESTIÓN AMBIENTAL", cumplimiento_pct: 5 }),
  fila({ id: "2", indicador: "Satisfacción", proceso: "Contabilidad", cumplimiento_pct: 60, tiene_om: 1, om_id: 7, numero_om: "440", tipo_accion: "OM Kawak", avance_om: 30 }),
  fila({ id: "3", indicador: "Cartera", proceso: "Tesorería", cumplimiento_pct: null, om_id: 8, tiene_om: 0, tipo_accion: "Otro" }),
  fila({ id: "4", indicador: "Facturas", proceso: "Contabilidad", cumplimiento_pct: 20 }),
];

describe("estado de la OM", () => {
  it("distingue sin OM, en gestión y cerrada", () => {
    expect(estadoOM(FILAS[0])).toBe("sin_om");
    expect(estadoOM(FILAS[1])).toBe("en_gestion");
    expect(estadoOM(FILAS[2])).toBe("cerrada"); // tiene registro pero ya no está activo
    expect(contarPorEstado(FILAS)).toEqual({ sin_om: 2, en_gestion: 1, cerrada: 1 });
  });
});

describe("formatNumero", () => {
  it("compacta cifras enormes y mantiene decimales útiles en las pequeñas", () => {
    expect(formatNumero(10049277970)).toBe("10.049,3 M");
    expect(formatNumero(30907)).toMatch(/30[.\s]?907/);
    expect(formatNumero(-732.08)).toBe("-732,08");
    expect(formatNumero(0.05)).toBe("0,05");
    expect(formatNumero(null)).toBe("—");
  });
});

describe("filtrarFilas", () => {
  it("aplica la pestaña", () => {
    expect(filtrarFilas(FILAS, "pendientes", "").map((f) => f.id)).toEqual(["10", "4"]);
    expect(filtrarFilas(FILAS, "en_gestion", "").map((f) => f.id)).toEqual(["2"]);
    expect(filtrarFilas(FILAS, "cerradas", "").map((f) => f.id)).toEqual(["3"]);
    expect(filtrarFilas(FILAS, "todos", "")).toHaveLength(4);
  });
  it("busca sin distinguir tildes ni mayúsculas, incluido el N° de OM", () => {
    expect(filtrarFilas(FILAS, "todos", "gestion").map((f) => f.id)).toEqual(["10"]);
    expect(filtrarFilas(FILAS, "todos", "TESORERIA").map((f) => f.id)).toEqual(["3"]);
    expect(filtrarFilas(FILAS, "todos", "440").map((f) => f.id)).toEqual(["2"]);
    expect(filtrarFilas(FILAS, "todos", "zzz")).toEqual([]);
  });
});

describe("ordenarFilas", () => {
  it("por prioridad: sin OM primero y, dentro, el menor cumplimiento", () => {
    const o = ordenarFilas(FILAS, { por: "prioridad", dir: "asc" }).map((f) => f.id);
    expect(o).toEqual(["10", "4", "2", "3"]);
  });
  it("por cumplimiento deja los nulos al final en ambas direcciones", () => {
    expect(ordenarFilas(FILAS, { por: "cumplimiento", dir: "asc" }).map((f) => f.id)).toEqual(["10", "4", "2", "3"]);
    expect(ordenarFilas(FILAS, { por: "cumplimiento", dir: "desc" }).map((f) => f.id)).toEqual(["2", "4", "10", "3"]);
  });
  it("por id ordena numéricamente (2 antes que 10)", () => {
    expect(ordenarFilas(FILAS, { por: "id", dir: "asc" }).map((f) => f.id)).toEqual(["2", "3", "4", "10"]);
  });
  it("agrupar por proceso mantiene juntas las filas del mismo proceso", () => {
    const o = ordenarFilas(FILAS, { por: "prioridad", dir: "asc" }, true).map((f) => f.proceso);
    expect(o).toEqual(["Contabilidad", "Contabilidad", "GESTIÓN AMBIENTAL", "Tesorería"]);
  });
  it("no muta la lista original", () => {
    const copia = FILAS.map((f) => f.id);
    ordenarFilas(FILAS, { por: "id", dir: "desc" });
    expect(FILAS.map((f) => f.id)).toEqual(copia);
  });
});

describe("validarRegistro", () => {
  it("exige N° de OM numérico solo para OM Kawak", () => {
    expect(validarRegistro("OM Kawak", "")).toMatch(/N° de la OM/);
    expect(validarRegistro("OM Kawak", "abc")).toMatch(/número/);
    expect(validarRegistro("OM Kawak", "OM 440")).toBeNull();
    expect(validarRegistro("Otro", "")).toBeNull();
  });
});

describe("agruparPorTipoAccion", () => {
  it("ignora los indicadores sin OM y ordena por cantidad", () => {
    expect(agruparPorTipoAccion(FILAS)).toEqual([
      { nombre: "OM Kawak", valor: 1 },
      { nombre: "Otro", valor: 1 },
    ]);
  });
});
