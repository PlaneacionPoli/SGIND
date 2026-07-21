# Inventario de Deuda Tecnica No Destructiva (2026-05-11)

## Objetivo
Aplicar limpieza no destructiva para reducir ruido tecnico en validaciones y revisiones, sin borrar archivos historicos.

## Reglas aplicadas
- Ignorar archivos temporales y de depuracion en Git.
- Excluir archivos temporales y respaldos en Ruff.
- Excluir archivos temporales y respaldos en Pytest.
- Mantener trazabilidad con este inventario.

## Inventario detectado
- debug_cierres_ids.py
- debug_compute_trends.py
- debug_duplicate_columns.py
- debug_duplicate_error.py
- debug_filter.log
- debug_merge_error.py
- debug_preparar_pdi.py
- debug_proyectos_linebyline.py
- scripts/_archived/debug_cascada.py
- services/strategic_indicators_legacy_backup.py
- services/strategic_indicators_old.py.bak
- streamlit_app/pages/resumen_general_backup_20260415.py
- tmp_audit_proyectos_ids.py
- tmp_buscar_ids_900.py
- tmp_cierres_structure.py
- tmp_debug_ids.py
- tmp_diagnostic.py
- tmp_full_structure.py
- tmp_ids_mismatch.py
- tmp_proyectos_columns.py
- tmp_proyectos_diagnostic.py
- tmp_relationship.py
- tmp_test_new_proyectos.py
- tmp_test_proyectos_fix.py
- tmp_verificar_ids_cruzar.py

## Siguiente fase recomendada
Mover los archivos listados a una carpeta unica de historico (por ejemplo, scripts/_archived/tmp_debug/) mediante un cambio planificado y revisado.

## Estado de ejecucion
- 2026-05-11: Archivos movidos a scripts/_archived/tmp_debug/ (no destructivo).
- Resultado: 0 archivos tmp/debug fuera de scripts/_archived y fuera de entornos locales.
