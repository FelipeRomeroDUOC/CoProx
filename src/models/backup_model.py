"""
Modelo de Backup - CoProx

PROPÓSITO:
Este módulo gestiona el estado y metadatos del sistema de backup y restauración.
Mantiene información sobre backups creados, importaciones y operaciones en progreso.

FUNCIONAMIENTO:
- Almacena metadatos de backups exportados e importados
- Rastrea el progreso de operaciones de backup/restore
- Mantiene historial de operaciones realizadas
- Valida integridad de archivos de backup

PARÁMETROS DE ENTRADA:
- backup_metadata: Diccionario con información del backup (fecha, cuentas incluidas)
- export_progress: Float entre 0-1 indicando progreso de exportación
- import_progress: Float entre 0-1 indicando progreso de importación
- backup_history: Lista de backups creados anteriormente
- validation_results: Diccionario con resultados de validación de archivos

SALIDA ESPERADA:
- current_operation: String indicando operación actual (export/import/idle)
- operation_progress: Float con progreso de la operación actual
- backup_list: Lista de backups disponibles para importar
- last_backup_info: Diccionario con información del último backup creado
- validation_status: String indicando estado de validación

PROCESAMIENTO DE DATOS:
- Genera metadatos automáticamente durante exportación
- Valida estructura y contenido de archivos ZIP
- Calcula estadísticas de cuentas incluidas en backup
- Detecta duplicados durante importación

INTERACCIONES CON OTROS MÓDULOS:
- Actualizado por: backup_controller.py (operaciones de backup)
- Leído por: backup_view.py (mostrar progreso y estado)
- Consultado por: file_service.py (validación de archivos)
- Usado por: auth_controller.py (importar tokens)

INTERACCIONES CON MAIN:
- main.py puede inicializar con estado de backup previo
- Se actualiza durante operaciones de export/import
- Proporciona información para mostrar en la interfaz
"""