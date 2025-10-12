"""
Modelo del Proxy - CoProx

PROPÓSITO:
Este módulo mantiene el estado del servidor proxy HTTP y sus estadísticas de funcionamiento.
Rastrea si el proxy está activo, puerto en uso y métricas de solicitudes procesadas.

FUNCIONAMIENTO:
- Almacena el estado actual del servidor proxy (activo/inactivo)
- Mantiene estadísticas de solicitudes procesadas
- Rastrea errores y tiempo de actividad
- Proporciona información sobre el puerto y host del servidor

PARÁMETROS DE ENTRADA:
- server_status: Boolean indicando si el servidor está activo
- port: Entero con el puerto donde escucha el servidor
- host: String con la dirección IP del servidor
- request_count: Entero con número de solicitudes procesadas
- error_count: Entero con número de errores ocurridos
- uptime: Tiempo transcurrido desde el inicio del servidor

SALIDA ESPERADA:
- is_running: Boolean del estado actual del proxy
- server_info: Diccionario con host, puerto y configuración
- statistics: Diccionario con métricas de uso y rendimiento
- last_request_time: Timestamp de la última solicitud procesada
- health_status: String indicando el estado de salud del servidor

PROCESAMIENTO DE DATOS:
- Actualiza contadores de solicitudes en tiempo real
- Calcula estadísticas de rendimiento y uptime
- Determina estado de salud basándose en errores recientes
- Formatea métricas para mostrar en la interfaz

INTERACCIONES CON OTROS MÓDULOS:
- Actualizado por: proxy_controller.py (estadísticas del servidor)
- Leído por: proxy_view.py (mostrar estado del proxy)
- Consultado por: app_controller.py (estado general de la aplicación)
- Modificado por: android_service.py (notificaciones de estado)

INTERACCIONES CON MAIN:
- main.py consulta este modelo para determinar si iniciar el proxy
- Se actualiza cuando el usuario inicia/detiene el servidor
- Proporciona información para la notificación persistente de Android
"""