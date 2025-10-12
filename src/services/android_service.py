"""
Servicio Android - CoProx

PROPÓSITO:
Este servicio maneja funcionalidades específicas de Android incluyendo notificaciones
persistentes, gestión de ciclo de vida y supervivencia al minimizar la aplicación.

FUNCIONAMIENTO:
- Crea notificaciones persistentes que mantienen la app en primer plano
- Maneja eventos de minimizar y reabrir la aplicación
- Configura el servicio para sobrevivir cuando la UI se oculta
- Proporciona APIs específicas de Android para selector de archivos

PARÁMETROS DE ENTRADA:
- notification_title: String con título de la notificación persistente
- notification_content: String con texto descriptivo de la notificación
- icon_resource: String con ruta del icono para la notificación
- service_status: String indicando estado del servicio (active/inactive)
- file_picker_filter: String con tipos de archivo para selector

SALIDA ESPERADA:
- notification_id: Entero con ID de la notificación creada
- lifecycle_events: Lista de eventos de ciclo de vida capturados
- file_selection_result: String con ruta del archivo seleccionado
- permission_status: Boolean indicando si permisos están concedidos
- service_health: String indicando estado del servicio Android

PROCESAMIENTO DE DATOS:
- Configura parámetros de notificación según especificaciones Android
- Maneja permisos de sistema necesarios para funcionamiento
- Procesa eventos de ciclo de vida y los traduce a acciones internas
- Integra con sistema de archivos Android para selector nativo

INTERACCIONES CON OTROS MÓDULOS:
- Usado por: app_controller.py (gestión de ciclo de vida)
- Utiliza: proxy_model.py (estado para mostrar en notificación)
- Notifica a: notification_view.py (actualizaciones de estado)
- Interactúa con: backup_controller.py (selector de archivos)

INTERACCIONES CON MAIN:
- main.py inicializa este servicio al detectar plataforma Android
- Se mantiene activo durante toda la ejecución de la aplicación
- Proporciona la funcionalidad clave de supervivencia al minimizar
"""