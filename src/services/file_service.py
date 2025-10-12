"""
Servicio de Archivos - CoProx

PROPÓSITO:
Este servicio maneja todas las operaciones de archivo del sistema incluyendo tokens,
backups ZIP y gestión de directorios. Proporciona funciones centralizadas para I/O.

FUNCIONAMIENTO:
- Lee y escribe archivos de tokens de forma segura
- Crea y extrae archivos ZIP para backups
- Gestiona directorios de tokens activos y agotados
- Valida integridad de archivos y estructura de directorios

PARÁMETROS DE ENTRADA:
- file_path: String con ruta del archivo a procesar
- file_content: String o bytes con contenido a escribir
- directory_path: String con ruta del directorio a crear/validar
- zip_password: String opcional para proteger archivos ZIP
- backup_data: Diccionario con datos a incluir en backup

SALIDA ESPERADA:
- file_content: String con contenido leído del archivo
- operation_success: Boolean indicando éxito de la operación
- file_list: Lista de archivos encontrados en directorio
- backup_metadata: Diccionario con información del backup creado
- validation_result: Boolean indicando si archivo/directorio es válido

PROCESAMIENTO DE DATOS:
- Maneja codificación UTF-8 para archivos de texto
- Implementa compresión ZIP con protección opcional por contraseña
- Valida formato de tokens antes de guardarlos
- Crea estructura de directorios automáticamente si no existe
- Implementa respaldos automáticos antes de operaciones destructivas

INTERACCIONES CON OTROS MÓDULOS:
- Usado por: auth_controller.py (gestión de archivos de tokens)
- Usado por: backup_controller.py (crear/extraer archivos ZIP)
- Utiliza: config_model.py (rutas de directorios)
- Notifica a: backup_model.py (progreso de operaciones)

INTERACCIONES CON MAIN:
- main.py utiliza este servicio para verificar archivos existentes al inicio
- Se usa durante todo el ciclo de vida para persistencia de datos
- Maneja la migración de datos entre diferentes versiones
"""