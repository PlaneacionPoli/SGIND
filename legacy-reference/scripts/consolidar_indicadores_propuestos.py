import pandas as pd

# Ruta del archivo Excel
EXCEL_PATH = r"C:/Users/ximen/OneDrive/Proyectos_DS/Sistema_Indicadores_Poli/data/raw/Propuesta Indicadores/Indicadores Propuestos.xlsx"

# Función para extraer y filtrar indicadores de cada hoja
def extraer_indicadores():
    # Retos
    retos = pd.read_excel(EXCEL_PATH, sheet_name="Retos")
    retos_filtrados = retos[retos["Aplica Desempeño"].str.upper() == "SI"][["Proceso", "Subproceso", "Indicador Propuesto"]]
    retos_filtrados = retos_filtrados.dropna(subset=["Indicador Propuesto"])
    retos_filtrados["Indicador Propuesto"] = retos_filtrados["Indicador Propuesto"].astype(str)

    # Proyectos
    proyectos = pd.read_excel(EXCEL_PATH, sheet_name="Proyectos")
    proyectos_filtrados = proyectos[proyectos["Propuesta"].str.upper() == "SI"][["Proceso", "Subproceso", "Nombre del Indicador Propuesto"]]
    proyectos_filtrados = proyectos_filtrados.rename(columns={"Nombre del Indicador Propuesto": "Indicador Propuesto"})
    proyectos_filtrados = proyectos_filtrados.dropna(subset=["Indicador Propuesto"])
    proyectos_filtrados["Indicador Propuesto"] = proyectos_filtrados["Indicador Propuesto"].astype(str)

    # Plan de mejoramiento (header en la segunda fila)
    plan = pd.read_excel(EXCEL_PATH, sheet_name="Plan de mejoramiento", header=1)
    plan_filtrados = plan[plan["Propuesta Indicador"].str.upper() == "SI"][["Proceso", "Subproceso", "INDICADOR DE RESULTADO O IMPACTO"]]
    plan_filtrados = plan_filtrados.rename(columns={"INDICADOR DE RESULTADO O IMPACTO": "Indicador Propuesto"})
    plan_filtrados = plan_filtrados.dropna(subset=["Indicador Propuesto"])
    plan_filtrados["Indicador Propuesto"] = plan_filtrados["Indicador Propuesto"].astype(str)

    # Calidad
    calidad = pd.read_excel(EXCEL_PATH, sheet_name="Calidad")
    calidad_filtrados = calidad[["Proceso", "Subroceso", "Propuesta SGC (Indicadores)"]]
    calidad_filtrados = calidad_filtrados.rename(columns={"Subroceso": "Subproceso", "Propuesta SGC (Indicadores)": "Indicador Propuesto"})
    calidad_filtrados = calidad_filtrados.dropna(subset=["Indicador Propuesto"])
    calidad_filtrados["Indicador Propuesto"] = calidad_filtrados["Indicador Propuesto"].astype(str)

    # Unir todos
    df_final = pd.concat([
        retos_filtrados,
        proyectos_filtrados,
        plan_filtrados,
        calidad_filtrados
    ], ignore_index=True)

    # Eliminar duplicados
    df_final = df_final.drop_duplicates()
    return df_final

if __name__ == "__main__":
    df = extraer_indicadores()
    print(df.head())
    # Guardar como CSV temporal para revisión
    df.to_csv("artifacts/indicadores_propuestos_consolidados.csv", index=False)
