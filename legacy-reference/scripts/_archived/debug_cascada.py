"""Genera archivos de depuración para la cascada: pdi.csv, cascada.csv, cierres_sample.csv, worksheet_flags.csv
Este script no requiere Streamlit y puede ejecutarse localmente desde la raíz del repo.
"""
from pathlib import Path
import pandas as pd


ROOT = Path.cwd()
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"
RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
OUT_DIR = ROOT / "artifacts" / "debug_cascada"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_col_like(df, cands):
    names = {c.lower(): c for c in df.columns}
    for cand in cands:
        if cand.lower() in names:
            return names[cand.lower()]
    for k, v in names.items():
        for cand in cands:
            if cand.lower() in k:
                return v
    return None


def calcular_cascada(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'cumplimiento_pct' not in df.columns:
        df['cumplimiento_pct'] = pd.NA
    nivel4 = df.copy()
    nivel4["Nivel"] = 4
    nivel4["Total_Indicadores"] = 1
    cols4 = [c for c in ["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "cumplimiento_pct", "Total_Indicadores"] if c in nivel4.columns]
    nivel4 = nivel4[cols4]
    nivel4 = nivel4.rename(columns={"cumplimiento_pct": "Cumplimiento"})

    nivel3 = (
        df.groupby(["Linea", "Objetivo", "Meta_PDI"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel3["Nivel"] = 3
    nivel3["Indicador"] = None
    nivel3 = nivel3[["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "Cumplimiento", "Total_Indicadores"]]

    nivel2 = (
        df.groupby(["Linea", "Objetivo"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel2["Nivel"] = 2
    nivel2["Meta_PDI"] = None
    nivel2["Indicador"] = None
    nivel2 = nivel2[["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "Cumplimiento", "Total_Indicadores"]]

    nivel1 = (
        df.groupby(["Linea"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel1["Nivel"] = 1
    nivel1["Objetivo"] = None
    nivel1["Meta_PDI"] = None
    nivel1["Indicador"] = None
    nivel1 = nivel1[["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "Cumplimiento", "Total_Indicadores"]]

    cascada = pd.concat([nivel1, nivel2, nivel3, nivel4], ignore_index=True)
    return cascada


def main():
    print("ROOT:", ROOT)

    if not OUT_XLSX.exists():
        print("ERROR: data/output/Resultados Consolidados.xlsx no encontrado")
        return

    xl = pd.ExcelFile(OUT_XLSX, engine='openpyxl')
    sheet = 'Consolidado Cierres' if 'Consolidado Cierres' in xl.sheet_names else ('Cierre historico' if 'Cierre historico' in xl.sheet_names else xl.sheet_names[0])
    df = xl.parse(sheet)
    df.columns = [str(c).strip() for c in df.columns]
    print(f"Loaded {sheet} shape={df.shape}")

    c_id = find_col_like(df, ['Id', 'ID'])
    c_meta = find_col_like(df, ['Meta'])
    c_ejec = find_col_like(df, ['Ejecucion', 'Ejecución'])
    c_sent = find_col_like(df, ['Sentido'])
    c_cump = find_col_like(df, ['cumplimiento_pct', 'Cumplimiento'])

    if c_meta and c_ejec:
        meta_n = pd.to_numeric(df[c_meta], errors='coerce')
        ejec_n = pd.to_numeric(df[c_ejec], errors='coerce')
        valid = meta_n.notna() & ejec_n.notna() & (meta_n != 0)
        sentido_neg = df[c_sent].astype(str).str.lower() == 'negativo' if c_sent else pd.Series([False]*len(df))
        ratio = pd.Series(pd.NA, index=df.index)
        ratio.loc[valid & ~sentido_neg] = (ejec_n[valid & ~sentido_neg] / meta_n[valid & ~sentido_neg])
        ratio.loc[valid & sentido_neg] = (meta_n[valid & sentido_neg] / ejec_n[valid & sentido_neg])
        df['cumplimiento_pct_calc'] = pd.to_numeric(ratio, errors='coerce') * 100
    else:
        df['cumplimiento_pct_calc'] = pd.NA

    # Export a sample of cierres
    sample_cols = [c for c in [c_id, c_meta, c_ejec, c_sent, c_cump, 'cumplimiento_pct_calc'] if c]
    sample_df = df[sample_cols].head(200).copy()
    sample_df.to_excel(OUT_DIR / 'cierres_sample.xlsx', index=False)
    print(f"Wrote: {OUT_DIR / 'cierres_sample.xlsx'} shape={sample_df.shape}")

    # Worksheet flags
    if RAW_XLSX.exists():
        xl2 = pd.ExcelFile(RAW_XLSX, engine='openpyxl')
        if 'Worksheet' in xl2.sheet_names:
            wks = xl2.parse('Worksheet')
            wks.columns = [str(c).strip() for c in wks.columns]
            # detect flag columns
            flag_candidates = [c for c in wks.columns if any(x in c.lower() for x in ['plan', 'flag', 'plan estrategico', 'indicadores plan'])]
            cols_show = [c for c in ['Id'] if c in wks.columns] + flag_candidates
            wks[cols_show].head(200).to_excel(OUT_DIR / 'worksheet_flags.xlsx', index=False)
            print(f"Wrote: {OUT_DIR / 'worksheet_flags.xlsx'} shape={(wks[cols_show].head(200).shape)}")
        else:
            print("RAW: Worksheet sheet not found")
    else:
        print("RAW XLSX not found")

    # Build PDI-like merged table (mimic preparar_pdi_con_cierre minimal)
    # load worksheet flags and cierres from previously read dataframes
    plan_df = None
    if RAW_XLSX.exists():
        xl2 = pd.ExcelFile(RAW_XLSX, engine='openpyxl')
        if 'Worksheet' in xl2.sheet_names:
            wks = xl2.parse('Worksheet')
            wks.columns = [str(c).strip() for c in wks.columns]
            # find id and plan flag
            c_id_w = find_col_like(wks, ['Id', 'ID'])
            c_plan = find_col_like(wks, ['Indicadores Plan estrategico', 'Plan anual o trabajo', 'Indicadores Plan estrategico'])
            if c_id_w:
                plan_df = wks[[c_id_w]].copy()
                plan_df = plan_df.rename(columns={c_id_w: 'Id'})
                if c_plan and c_plan in wks.columns:
                    plan_df['FlagPlanEstrategico'] = pd.to_numeric(wks[c_plan], errors='coerce').fillna(0).astype(int)
                else:
                    plan_df['FlagPlanEstrategico'] = 0
                # bring Linea/Objetivo if exist
                for col in ['Linea', 'Objetivo']:
                    if col in wks.columns:
                        plan_df[col] = wks[col].astype(str).str.strip()
    if plan_df is None:
        print('No worksheet plan table available; aborting PDI build')
    else:
        # merge with cierre df on Id
        close = df.copy()
        cols_close = ['Id', 'Indicador', 'Cumplimiento', 'Anio', 'Mes', 'Meta', 'Ejecucion', 'Sentido']
        cols_close = [c for c in cols_close if c in close.columns]
        merged = plan_df.merge(close[cols_close], on='Id', how='left')
        # Construir campo `cumplimiento_pct` usando las fuentes disponibles
        merged['cumplimiento_pct'] = pd.NA
        # 1) Si ya existe columna numérica
        if 'cumplimiento_pct' in merged.columns:
            merged['cumplimiento_pct'] = pd.to_numeric(merged['cumplimiento_pct'], errors='coerce')
        # 2) Si existe 'Cumplimiento' en formato texto, intentar parsear (quitar % y normalizar coma)
        if merged['cumplimiento_pct'].isna().all() and 'Cumplimiento' in merged.columns:
            parsed = (
                merged['Cumplimiento'].astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            merged['cumplimiento_pct'] = pd.to_numeric(parsed, errors='coerce')
        # 3) Rellenar con cálculo desde Meta/Ejecucion cuando falte
        if merged['cumplimiento_pct'].isna().any() and 'Meta' in merged.columns and 'Ejecucion' in merged.columns:
            meta_n = pd.to_numeric(merged['Meta'], errors='coerce')
            ejec_n = pd.to_numeric(merged['Ejecucion'], errors='coerce')
            valid = meta_n.notna() & ejec_n.notna() & (meta_n != 0)
            sentido_neg = merged['Sentido'].astype(str).str.lower() == 'negativo' if 'Sentido' in merged.columns else pd.Series([False] * len(merged))
            ratio = pd.Series(pd.NA, index=merged.index)
            ratio.loc[valid & ~sentido_neg] = (ejec_n[valid & ~sentido_neg] / meta_n[valid & ~sentido_neg])
            ratio.loc[valid & sentido_neg] = (meta_n[valid & sentido_neg] / ejec_n[valid & sentido_neg])
            merged.loc[merged['cumplimiento_pct'].isna(), 'cumplimiento_pct'] = pd.to_numeric(ratio, errors='coerce') * 100

        merged['Nivel de cumplimiento'] = merged['cumplimiento_pct'].apply(lambda v: 'Pendiente' if pd.isna(v) else 'Con dato')
        merged.to_excel(OUT_DIR / 'pdi.xlsx', index=False)
        print(f"Wrote: {OUT_DIR / 'pdi.xlsx'} shape={merged.shape}")

        # Asegurar columnas requeridas por calcular_cascada
        for col in ["Linea", "Objetivo", "Meta_PDI", "Indicador"]:
            if col not in merged.columns:
                merged[col] = None
        # build cascada
        cascada = calcular_cascada(merged)
        cascada.to_excel(OUT_DIR / 'cascada.xlsx', index=False)
        print(f"Wrote: {OUT_DIR / 'cascada.xlsx'} shape={cascada.shape}")

        # print quick summary
        print('\nSummary:')
        print('pdi rows:', merged.shape[0])
        print('pdi cumplimiento_pct notna:', int(merged['cumplimiento_pct'].notna().sum()))
        print('cascada Nivel value_counts:\n', cascada['Nivel'].value_counts().to_dict())


if __name__ == '__main__':
    main()
