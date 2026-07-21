#!/usr/bin/env python
"""Verificar tabla Consolidado Cierre - fuente oficial de proyectos"""

from core.db_manager import get_db_session
from sqlalchemy import text, inspect
import pandas as pd

print("="*70)
print("INSPECCIÓN: TABLA 'CONSOLIDADO CIERRE'")
print("="*70)

try:
    # Conectar a BD
    session = get_db_session()
    inspector = inspect(session.bind)
    
    # Listar todas las tablas
    print("\n1. TABLAS DISPONIBLES EN SUPABASE:")
    tables = inspector.get_table_names()
    print(f"   Total: {len(tables)} tablas")
    
    # Buscar tabla consolidado
    consolidado_tables = [t for t in tables if "consolidado" in t.lower()]
    print(f"\n2. TABLAS CON 'CONSOLIDADO':")
    for t in consolidado_tables:
        print(f"   - {t}")
    
    # Intentar cargar consolidado_cierre
    print(f"\n3. INTENTANDO CARGAR 'consolidado_cierre':")
    
    query = """
    SELECT COUNT(*) as total, 
           COUNT(DISTINCT "Id") as unique_ids,
           MIN("Id") as min_id, 
           MAX("Id") as max_id
    FROM consolidado_cierre
    """
    
    result = session.execute(text(query)).fetchone()
    print(f"   Total registros: {result[0]}")
    print(f"   IDs únicos: {result[1]}")
    print(f"   Rango ID: {result[2]} - {result[3]}")
    
    # Ver columnas
    consolidado_cols = inspector.get_columns("consolidado_cierre")
    print(f"\n4. COLUMNAS EN consolidado_cierre:")
    for col in consolidado_cols:
        print(f"   - {col['name']} ({col['type']})")
    
    # Buscar IDs de proyectos
    proy_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 900, 901, 902, 903, 904]
    placeholders = ','.join([str(x) for x in proy_ids])
    
    print(f"\n5. BÚSQUEDA DE IDS DE PROYECTOS (1-13, 900+):")
    
    query2 = f"""
    SELECT COUNT(*) as total, COUNT(DISTINCT "Id") as unique_ids
    FROM consolidado_cierre
    WHERE "Id" IN ({placeholders})
    """
    
    result2 = session.execute(text(query2)).fetchone()
    print(f"   Registros encontrados: {result2[0]}")
    print(f"   IDs únicos encontrados: {result2[1]}")
    
    # Si hay coincidencias, mostrar datos
    if result2[0] > 0:
        print(f"\n6. MUESTRA DE PROYECTOS EN consolidado_cierre:")
        query3 = f"""
        SELECT "Id", "Indicador", "Meta", "Ejecucion", "cumplimiento_pct", "Linea", "Objetivo"
        FROM consolidado_cierre
        WHERE "Id" IN ({placeholders})
        LIMIT 10
        """
        df = pd.read_sql(query3, session.bind)
        print(df.to_string())
    
    session.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
