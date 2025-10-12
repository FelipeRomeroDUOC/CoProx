"""
Controlador de Backup - CoProx

PROPÓSITO:
Este controlador gestiona las operaciones de exportación e importación de backups,
incluyendo creación de archivos ZIP protegidos y restauración de cuentas.

FUNCIONAMIENTO:
- Coordina exportación de todas las cuentas a archivo ZIP
- Maneja importación y validación de backups desde archivos ZIP
- Implementa protección opcional con contraseña para backups
- Gestiona detección y manejo de cuentas duplicadas durante importación

PARÁMETROS DE ENTRADA:
- export_request: Diccionario con configuración de exportación (contraseña, ubicación)
- import_request: Diccionario con archivo a importar y contraseña si aplica
- backup_metadata: Diccionario con información a incluir en backup
- validation_config: Diccionario con parámetros de validación

SALIDA ESPERADA:
- export_result: Diccionario con resultado de exportación (ruta, estadísticas)
- import_result: Diccionario con resultado de importación (cuentas añadidas)
- validation_status: Diccionario con estado de validación del backup
- operation_progress: Float entre 0-1 indicando progreso de operación

PROCESAMIENTO DE DATOS:
- Genera metadatos automáticamente incluyendo fecha y versión
- Valida estructura de archivos ZIP antes de importar
- Detecta duplicados comparando con cuentas existentes
- Crea estructura temporal para operaciones seguras
- Implementa rollback en caso de errores durante importación

INTERACCIONES CON OTROS MÓDULOS:
- Utiliza: file_service.py (operaciones ZIP y archivos)
- Utiliza: auth_controller.py (importar tokens nuevos)
- Actualiza: backup_model.py (progreso y estado)
- Notifica a: backup_view.py (actualizaciones de progreso)
- Coordina con: android_service.py (selector de archivos)

INTERACCIONES CON MAIN:
- main.py puede usar este controlador para backup automático al iniciar
- Se activa por interacción del usuario desde la interfaz
- Proporciona funcionalidad de migración entre dispositivos
"""