import pandas as pd
from pathlib import Path

# Rutas de los archivos consolidados
ROOT = Path(__file__).parent.parent
KAWAK_PATH = ROOT / "data" / "raw" / "Fuentes Consolidadas" / "Indicadores Kawak.xlsx"
API_PATH = ROOT / "data" / "raw" / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"


def cargar_catalogo_kawak():
    """Carga el catálogo Kawak consolidado en un DataFrame."""
    return pd.read_excel(KAWAK_PATH)

def cargar_consolidado_api():
    """Carga el consolidado API en un DataFrame."""
    return pd.read_excel(API_PATH)


def consultar_indicador_kawak(id_indicador):
    """Devuelve un DataFrame con los datos del indicador específico en el catálogo Kawak."""
    df = cargar_catalogo_kawak()
    return df[df["Id"] == str(id_indicador)]


def consultar_indicador_api(id_indicador):
    """Devuelve un DataFrame con los datos del indicador específico en el consolidado API."""
    df = cargar_consolidado_api()
    return df[df["ID"] == str(id_indicador)]


# Ejemplo de uso interactivo:
if __name__ == "__main__":
    id_ind = input("Ingrese el ID del indicador a consultar: ")
    print("\n--- Catálogo Kawak ---")
    print(consultar_indicador_kawak(id_ind))
    print("\n--- Consolidado API ---")
    print(consultar_indicador_api(id_ind))
