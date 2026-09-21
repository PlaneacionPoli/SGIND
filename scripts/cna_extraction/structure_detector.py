"""
scripts/cna_extraction/structure_detector.py

Detector genérico de la geometría de cada hoja de datos del Anexo
Estadístico: localiza el bloque de encabezado (Tabla NO/Nombre), el eje de
periodos (horizontal, vertical o inexistente), las columnas/filas de
categoría (con forward-fill de etiquetas dispersas/mergeadas), y separa las
filas "Total" explícitas (que representan el valor del indicador principal)
de las filas de detalle (subindicadores).

Diseño: una cadena de funciones puras sobre listas de filas crudas
(`list[list[Any]]`), no una jerarquía de clases — cada hoja pasa por los
mismos pasos de descomposición geométrica, solo que con distintos puntos de
corte. Nunca lanza excepción por la forma de los datos: toda hoja produce un
SheetStructure con un `kind`, incluso "unresolved"/"event_log_atypical", para
que el reporte de diagnóstico quede completo.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.cna_extraction.models import HeaderBlock, PeriodColumn, SheetStructure

NA_STRINGS = {"-", "", "\xa0", " ", " ", "n/a", "na", "nd"}

_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
_SEMESTER_RE = re.compile(r"^(19|20)\d{2}-[12]$")
_SEMESTER_DOT_RE = re.compile(r"^(19|20)\d{2}\.[12]$")  # typo frecuente en el Anexo: "2024.1"
_HEADER_LABEL_RE = re.compile(r"^(tabla\s*n[oº°]?\.?|gr[aá]fico\s*n[oº°]?\.?|\*)$", re.IGNORECASE)
_NUM_RE = re.compile(r"(\d+)")


def normalize_missing(value: Any) -> Any:
    """Colapsa placeholders de 'sin dato' (guion, vacío, nbsp, espacios
    especiales, etc.) a None. Números/fechas pasan intactos."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "" or text.lower() in NA_STRINGS:
            return None
        return value
    return value


def is_period_label(label: Any) -> str | None:
    """Devuelve el periodo normalizado ('YYYY' o 'YYYY-N') si `label` es un
    encabezado de periodo, o None si no lo es."""
    if label is None:
        return None
    text = str(label).strip()
    if _SEMESTER_RE.match(text):
        return text
    if isinstance(label, str) and _SEMESTER_DOT_RE.match(text):
        return text.replace(".", "-")
    if _YEAR_RE.match(text):
        return text
    return None


def is_total_label(label: Any) -> bool:
    if label is None:
        return False
    return str(label).strip().lower().startswith("total")


def _row_is_blank(row: list[Any]) -> bool:
    return all(normalize_missing(v) is None for v in row)


def forward_fill(values: list[Any]) -> list[Any]:
    """Forward-fill genérico izquierda-a-derecha (o arriba-a-abajo, según
    cómo se le pase la secuencia): usado tanto para etiquetas de grupo en
    encabezados de 2 niveles como para columnas de categoría dispersas."""
    result: list[Any] = []
    last: Any = None
    for v in values:
        v = normalize_missing(v)
        if v is not None:
            last = v
        result.append(last)
    return result


def find_header_block(raw_rows: list[list[Any]]) -> HeaderBlock:
    """Localiza, dentro de las primeras filas, el número/nombre declarados
    de la tabla y la fila donde empiezan los datos reales (tolerante a la
    variación de 0-2 filas en blanco después de 'Nombre')."""
    numero: int | None = None
    nombre: str | None = None
    data_start_row = 0
    max_scan = min(len(raw_rows), 6)

    for idx in range(max_scan):
        row = raw_rows[idx]
        if not row:
            continue
        label = str(row[0] or "").strip()
        if _HEADER_LABEL_RE.match(label):
            candidate = row[1] if len(row) > 1 else None
            if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                numero = int(candidate)
            elif isinstance(candidate, str):
                match = _NUM_RE.search(candidate)
                if match:
                    numero = int(match.group(1))
            data_start_row = idx + 1
        elif label.lower() == "nombre":
            candidate = row[1] if len(row) > 1 else None
            nombre = str(candidate) if candidate is not None else None
            data_start_row = idx + 1

    while data_start_row < len(raw_rows) and _row_is_blank(raw_rows[data_start_row]):
        data_start_row += 1

    return HeaderBlock(numero_declarado=numero, nombre=nombre, data_start_row=data_start_row)


def detect_event_log(raw_rows: list[list[Any]], data_start_row: int) -> bool:
    """Heurística para hojas tipo bitácora de eventos (columnas
    'Actividad'/'Población impactada' en texto libre) — se chequea ANTES de
    la detección de periodos para no forzar un ajuste incorrecto."""
    if data_start_row >= len(raw_rows):
        return False
    header_row = [str(v).strip().lower() if v is not None else "" for v in raw_rows[data_start_row]]
    has_actividad = any("actividad" in c for c in header_row)
    has_poblacion = any("poblaci" in c for c in header_row)
    return has_actividad and has_poblacion


_TRAS_ANIO_RE = re.compile(r"^a[ñn]o\s+del\s+", re.IGNORECASE)


def _etiqueta_categoria(valor: Any, encabezado: Any) -> Any:
    """Una categoría que es solo un año ("2019") se confunde con un periodo. Si
    la columna tiene encabezado ("AÑO DEL INFORME", Tabla 29) se usa para
    nombrarla: "Informe 2019"."""
    if (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and float(valor).is_integer()
        and 1900 <= int(valor) <= 2100
        and isinstance(encabezado, str)
        and encabezado.strip()
    ):
        nombre = _TRAS_ANIO_RE.sub("", encabezado.strip()).strip()
        return f"{nombre.capitalize()} {int(valor)}"
    return valor


_INICIO_BLOQUE_RE = re.compile(r"^(nombre|tabla\s*n[oº°]?\.?|gr[aá]fico\s*n[oº°]?\.?)$", re.IGNORECASE)
_TOTAL_CON_NOMBRE_RE = re.compile(r"^total\s+\S", re.IGNORECASE)
_TOTAL_PREFIJO_RE = re.compile(r"^\s*total\s+", re.IGNORECASE)


def _es_titulo_de_bloque(row: list[Any]) -> bool:
    etiqueta = str(row[0]).strip() if row and row[0] is not None else ""
    return bool(etiqueta and _INICIO_BLOQUE_RE.match(etiqueta))


def _es_inicio_de_otro_bloque(row: list[Any]) -> bool:
    """Fila que abre un bloque distinto de la hoja (otro título "Nombre"/"Tabla"
    o un nuevo encabezado de periodos), no una continuación de los datos."""
    etiqueta = str(row[0]).strip() if row and row[0] is not None else ""
    if etiqueta and _INICIO_BLOQUE_RE.match(etiqueta):
        return True
    # Encabezado de periodos: TODAS las celdas con valor (salvo la primera) son
    # periodos. Un dato suelto como 2023 en una fila de cifras no lo convierte en
    # encabezado (Tablas 77 y 173).
    celdas = [v for v in row[1:] if v is not None]
    return len(celdas) >= 2 and all(is_period_label(v) for v in celdas)


def _bloques_de_datos(raw_rows: list[list[Any]], data_row_start: int) -> list[list[int]]:
    """Índices de las filas de datos agrupadas en bloques separados por filas en
    blanco. Las filas en blanco INICIALES se ignoran (Tablas 61, 65, 68 traen una
    fila vacía entre el encabezado y los datos: antes se leían 0 filas)."""
    bloques: list[list[int]] = [[]]
    for idx in range(data_row_start, len(raw_rows)):
        row = raw_rows[idx]
        if _row_is_blank(row):
            if bloques[-1]:
                bloques.append([])
            continue
        # Un encabezado a mitad de un bloque contiguo (Tablas 122 y 224 repiten la
        # fila de periodos) es parte de la hoja, como se leía antes; solo abre un
        # bloque nuevo si viene tras una fila en blanco o es un título "Nombre/Tabla".
        if _es_inicio_de_otro_bloque(row) and (not bloques[-1] or _es_titulo_de_bloque(row)):
            break
        bloques[-1].append(idx)
    return [b for b in bloques if b]


def _extract_rows(
    raw_rows: list[list[Any]],
    data_row_start: int,
    category_columns: list[int],
    period_columns: list[PeriodColumn],
    category_headers: dict[int, Any] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    has_explicit_total = False
    state: dict[int, Any] = {}
    ambiguous_seen: dict[tuple[Any, ...], int] = {}

    bloques = _bloques_de_datos(raw_rows, data_row_start)

    def tiene_total(idx: int) -> bool:
        # "Total Activos", "Total Pasivos": total NOMBRADO de su bloque. Un
        # "Total" a secas cierra la tabla, no define un grupo.
        return any(
            isinstance(raw_rows[idx][c], str) and _TOTAL_CON_NOMBRE_RE.match(raw_rows[idx][c].strip())
            for c in category_columns
            if c < len(raw_rows[idx])
        )

    # Varios bloques, cada uno con su propio "Total" (Tabla 66: Total Activos,
    # Total Pasivos, Patrimonio): es una jerarquía de 3 niveles, no un solo
    # bloque. Otras hojas con bloques (porcentajes, notas, revistas) no cumplen
    # esto y se leen solo hasta la primera fila en blanco, como antes.
    multibloque = sum(1 for b in bloques if any(tiene_total(i) for i in b)) >= 2
    indices = [(n, i) for n, b in enumerate(bloques) for i in b] if multibloque else [(0, i) for i in bloques[:1][0]] if bloques else []

    items: list[dict[str, Any]] = []
    for n_bloque, idx in indices:
        row = raw_rows[idx]
        category_path: list[Any] = []
        row_has_raw_category = False
        for col in category_columns:
            val = normalize_missing(row[col]) if col < len(row) else None
            if val is not None and category_headers:
                val = _etiqueta_categoria(val, category_headers.get(col))
            if val is not None:
                state[col] = val
                row_has_raw_category = True
            if state.get(col) is not None:
                category_path.append(state[col])

        row_is_total = any(is_total_label(v) for v in category_path)
        has_explicit_total = has_explicit_total or row_is_total
        row_kind = "total_explicito" if row_is_total else "detalle"

        # Fila sin ninguna etiqueta propia (todas las columnas de categoría
        # vacías en la fuente): el forward-fill la deja con el MISMO
        # category_path que la fila de detalle anterior, lo que colisiona su
        # Llave y provoca pérdida silenciosa de datos en la deduplicación de
        # escritura (ver caso real: Gráfico 19 "Proporción por tipo de
        # contrato" — una fila así trae valores ~1279/1234/... que NO suman
        # en el Total de la hoja, o sea es una categoría propia sin
        # etiqueta, no una continuación de "Medio tiempo - Anualizado").
        # Se distingue con un sufijo ordinal en vez de asumir en silencio
        # que es la misma categoría de la fila anterior.
        category_ambiguous = bool(category_path) and not row_has_raw_category and not row_is_total
        if category_ambiguous:
            key = tuple(category_path)
            ambiguous_seen[key] = ambiguous_seen.get(key, 0) + 1
            category_path = [*category_path, f"(sin etiqueta #{ambiguous_seen[key]})"]

        items.append(
            {
                "row": row,
                "path": category_path,
                "kind": row_kind,
                "ambiguous": category_ambiguous,
                "bloque": n_bloque,
            }
        )

    if multibloque:
        has_explicit_total = False
        for n_bloque in {it["bloque"] for it in items}:
            del_bloque = [it for it in items if it["bloque"] == n_bloque]
            total = next((it for it in del_bloque if it["kind"] == "total_explicito"), None)
            if total is not None:
                etiqueta = str(total["path"][-1])
                grupo = _TOTAL_PREFIJO_RE.sub("", etiqueta).strip() or etiqueta
            elif len(del_bloque) == 1:
                grupo = str(del_bloque[0]["path"][-1])
            else:
                grupo = "Otros"
            for it in del_bloque:
                es_subtotal = it is total
                it["path"] = [grupo, grupo] if (es_subtotal or len(del_bloque) == 1) else [grupo, *it["path"]]
                it["kind"] = "detalle"

    grupos_de_columna = {
        str(pc.group_label).strip()
        for pc in period_columns
        if pc.group_label is not None and is_period_label(pc.group_label) is None
    }
    for it in items:
        for pc in period_columns:
            value = normalize_missing(it["row"][pc.col_index]) if pc.col_index < len(it["row"]) else None
            # Encabezado de 2 niveles con la categoría ARRIBA de los periodos
            # (Ilustración 20: medio de comunicación sobre 2022|2023|2024): la
            # categoría es un nivel más, Medio - Opción. Sin él, todos los medios
            # compartían la misma Llave y solo sobrevivía uno.
            grupo_columna = pc.group_label
            con_grupo = (
                len(grupos_de_columna) >= 2 and grupo_columna is not None and is_period_label(grupo_columna) is None
            )
            fila = {
                "category_path": [str(grupo_columna).strip(), *it["path"]] if con_grupo else it["path"],
                "period": pc.period,
                "value": value,
                "row_kind": it["kind"],
                "category_ambiguous": it["ambiguous"],
            }
            if multibloque or con_grupo:
                # Los grupos (Activos/Pasivos/Patrimonio, cada medio con sus % de
                # respuesta) no se suman entre sí.
                fila["sin_total_global"] = True
            if pc.variable:
                # Subvariable (Títulos/Volúmenes): el TOTAL es un grupo más
                # ("TOTAL - Títulos"), no el total del indicador, porque las
                # variables no se suman entre sí.
                fila["variable"] = pc.variable
                fila["row_kind"] = "detalle"
            rows.append(fila)

    return rows, has_explicit_total


_NUM_TEXTO_RE = re.compile(r"^-?\d{1,3}(?:\.\d{3})+(?:,\d+)?$|^-?\d+(?:[.,]\d+)?$")


def _es_numerico(valor: Any) -> bool:
    if isinstance(valor, bool):
        return False
    if isinstance(valor, (int, float)):
        return True
    if isinstance(valor, str):
        return bool(_NUM_TEXTO_RE.match(valor.replace("$", "").replace("%", "").strip()))
    return False


def _columna_de_periodo(raw_rows: list[list[Any]], header_row_idx: int) -> int | None:
    """Columna (0-2) cuyos valores, hacia abajo, son periodos: la 0 en lo habitual;
    la 1 cuando la 0 va vacía (Gráficos 6 y 8: años en la segunda columna)."""
    for col in range(3):
        n = sum(1 for r in raw_rows[header_row_idx + 1 :] if col < len(r) and is_period_label(r[col]))
        if n >= 2:
            return col
    return None


def _extract_vertical_rows(
    raw_rows: list[list[Any]], header_row_idx: int, period_col: int = 0
) -> list[dict[str, Any]]:
    if header_row_idx >= len(raw_rows):
        return []
    header_row = raw_rows[header_row_idx]
    if is_period_label(header_row[period_col] if len(header_row) > period_col else None):
        col_labels = {i: f"col_{i}" for i in range(period_col + 1, len(header_row))}
        first_data_row = header_row_idx
    else:
        col_labels = {
            i: header_row[i]
            for i in range(period_col + 1, len(header_row))
            if normalize_missing(header_row[i]) is not None
        }
        first_data_row = header_row_idx + 1

    rows: list[dict[str, Any]] = []
    for row in raw_rows[first_data_row:]:
        if _row_is_blank(row):
            break
        period = is_period_label(row[period_col] if len(row) > period_col else None)
        if period is None:
            continue
        for col, label in col_labels.items():
            value = normalize_missing(row[col]) if col < len(row) else None
            row_kind = "total_explicito" if is_total_label(label) else "detalle"
            fila = {
                "category_path": [label] if label else [],
                "period": period,
                "value": value,
                "row_kind": row_kind,
                "category_ambiguous": False,
            }
            if period_col > 0:
                # Años en la 2ª columna (Gráficos 6 y 8): las columnas son variables
                # distintas (capital de trabajo vs índice de liquidez) y no se suman.
                fila["sin_total_global"] = True
            rows.append(fila)
    return rows


def _extract_snapshot_rows(raw_rows: list[list[Any]], header_row_idx: int) -> list[dict[str, Any]]:
    """Hoja sin eje de periodos: filas de categorías (una o varias columnas de
    texto, con etiquetas combinadas hacia abajo) y una o más columnas numéricas.
    Tabla 189: Beneficio | Nivel de formación | Monto."""
    if header_row_idx >= len(raw_rows):
        return []
    header_row = raw_rows[header_row_idx]
    col_labels = {
        i: header_row[i]
        for i in range(1, len(header_row))
        if normalize_missing(header_row[i]) is not None
    }
    filas: list[list[Any]] = []
    for row in raw_rows[header_row_idx + 1 :]:
        if _row_is_blank(row):
            break
        filas.append(row)

    def celdas(col: int) -> list[Any]:
        return [normalize_missing(r[col]) for r in filas if col < len(r) and normalize_missing(r[col]) is not None]

    numericas = [c for c in col_labels if celdas(c) and sum(_es_numerico(v) for v in celdas(c)) * 2 >= len(celdas(c))]
    textuales = [c for c in col_labels if c not in numericas]
    if textuales and numericas and (
        max(textuales) > min(numericas) or any(len(celdas(c)) < len(filas) for c in textuales)
    ):
        # Columnas de texto DESPUÉS de las numéricas (listas en paralelo, p.ej.
        # país/valor/país/valor) o incompletas (rellenar hacia abajo inventaría
        # categorías, Tabla 217): no es una jerarquía de categorías.
        textuales = []
        numericas = list(col_labels)
    columnas_categoria = [0, *textuales]

    rows: list[dict[str, Any]] = []
    estado: dict[int, Any] = {}
    for row in filas:
        camino: list[Any] = []
        hay_etiqueta = False
        for col in columnas_categoria:
            valor = normalize_missing(row[col]) if col < len(row) else None
            if valor is not None:
                estado[col] = valor
                hay_etiqueta = True
            if estado.get(col) is not None:
                camino.append(estado[col])
        if not hay_etiqueta or not camino:
            continue
        row_kind = "total_explicito" if any(is_total_label(v) for v in camino) else "detalle"
        for col in numericas or ([] if textuales else list(col_labels)):
            value = normalize_missing(row[col]) if col < len(row) else None
            rows.append(
                {
                    "category_path": [*camino, col_labels[col]] if (not textuales or len(numericas) > 1) else camino,
                    "period": None,
                    "value": value,
                    "row_kind": row_kind,
                    "category_ambiguous": False,
                }
            )
    return rows


def _detecta_encabezado_transpuesto(
    raw_rows: list[list[Any]], candidate_idx: int
) -> tuple[list[PeriodColumn], list[int]] | None:
    """Encabezado de 2 niveles con el PERIODO arriba (combinado sobre varias
    columnas) y la VARIABLE abajo, p.ej. Tabla 40:

        (vacío) | 2025    |            | 2026    |
        Áreas   | Títulos | Volúmenes  | Títulos | Volúmenes

    Cada columna con etiqueta abajo es (periodo de arriba, variable de abajo).
    Devuelve (columnas de periodo, columnas de categoría) o None si la hoja no
    tiene esa forma."""
    if candidate_idx + 1 >= len(raw_rows):
        return None
    arriba, abajo = raw_rows[candidate_idx], raw_rows[candidate_idx + 1]
    n_periodos_arriba = sum(1 for v in arriba if is_period_label(v))
    etiquetas = [
        (i, str(v).strip())
        for i, v in enumerate(abajo)
        if i > 0 and isinstance(v, str) and v.strip() and is_period_label(v) is None
    ]
    if n_periodos_arriba == 0 or any(is_period_label(v) for v in abajo):
        return None
    if len(etiquetas) < 2 or len(etiquetas) <= n_periodos_arriba:
        return None

    arriba_ff = forward_fill(arriba)
    columnas = []
    for col, variable in etiquetas:
        periodo = is_period_label(arriba_ff[col])
        if periodo is None:
            return None
        columnas.append(PeriodColumn(col_index=col, label=arriba_ff[col], period=periodo, variable=variable))
    primera = min(c.col_index for c in columnas)
    return columnas, list(range(primera))


def detect_structure(raw_rows: list[list[Any]], catalog_numero: int | None) -> SheetStructure:
    """Orquesta la detección completa de geometría para una hoja. Nunca
    lanza excepción por forma de datos (solo `unresolved` cuando no hay
    filas de datos después del bloque de encabezado)."""
    raw_rows = [[normalize_missing(v) for v in row] for row in raw_rows]
    header = find_header_block(raw_rows)

    if detect_event_log(raw_rows, header.data_start_row):
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="event_log_atypical",
            header=header,
            issues=["Detectada estructura de bitácora de eventos (no periódica); requiere revisión manual."],
        )

    if header.data_start_row >= len(raw_rows):
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="unresolved",
            header=header,
            issues=["No se encontraron filas de datos después del bloque de encabezado."],
        )

    candidate_idx = header.data_start_row
    header_row_idx = candidate_idx
    group_row_idx: int | None = None

    row_at_candidate = raw_rows[candidate_idx]
    if not any(is_period_label(v) for v in row_at_candidate):
        next_idx = candidate_idx + 1
        if next_idx < len(raw_rows):
            row_at_next = raw_rows[next_idx]
            period_count_next = sum(1 for v in row_at_next if is_period_label(v))
            if period_count_next >= 2:
                header_row_idx = next_idx
                group_row_idx = candidate_idx

    transpuesto = _detecta_encabezado_transpuesto(raw_rows, candidate_idx)
    if transpuesto is not None:
        period_columns, category_columns = transpuesto
        rows, has_explicit_total = _extract_rows(
            raw_rows,
            candidate_idx + 2,
            category_columns,
            period_columns,
            {c: raw_rows[candidate_idx + 1][c] for c in category_columns},
        )
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="horizontal_periods_2level_header",
            header=header,
            period_columns=period_columns,
            category_columns=category_columns,
            rows=rows,
            has_explicit_total=has_explicit_total,
        )

    header_row = raw_rows[header_row_idx]
    group_labels = forward_fill(raw_rows[group_row_idx]) if group_row_idx is not None else None

    period_columns: list[PeriodColumn] = []
    category_columns: list[int] = []
    excluded_columns: list[int] = []
    seen_first_period = False

    for col_idx, label in enumerate(header_row):
        period = is_period_label(label)
        if period is not None:
            seen_first_period = True
            group_label = group_labels[col_idx] if group_labels else None
            period_columns.append(PeriodColumn(col_index=col_idx, label=label, period=period, group_label=group_label))
        elif is_total_label(label):
            excluded_columns.append(col_idx)
        elif label is None:
            if seen_first_period:
                excluded_columns.append(col_idx)
            else:
                category_columns.append(col_idx)
        else:
            if seen_first_period:
                excluded_columns.append(col_idx)
            else:
                category_columns.append(col_idx)

    if period_columns:
        data_row_start = header_row_idx + 1
        rows, has_explicit_total = _extract_rows(
            raw_rows,
            data_row_start,
            category_columns,
            period_columns,
            {c: header_row[c] for c in category_columns},
        )
        if group_row_idx is not None:
            kind = "horizontal_periods_2level_header"
        elif len(category_columns) >= 2:
            kind = "horizontal_periods_2level_rows"
        else:
            kind = "horizontal_periods_flat"
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind=kind,
            header=header,
            period_columns=period_columns,
            category_columns=category_columns,
            excluded_columns=excluded_columns,
            rows=rows,
            has_explicit_total=has_explicit_total,
        )

    # Sin periodos horizontales: intentar vertical, luego snapshot.
    period_col = _columna_de_periodo(raw_rows, header_row_idx)
    if period_col is not None:
        rows = _extract_vertical_rows(raw_rows, header_row_idx, period_col)
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="vertical_periods",
            header=header,
            rows=rows,
        )

    rows = _extract_snapshot_rows(raw_rows, header_row_idx)
    return SheetStructure(
        catalog_numero=catalog_numero,
        kind="snapshot_no_period",
        header=header,
        rows=rows,
        issues=["No se detectó eje de periodos; tratada como tabla snapshot."],
    )
