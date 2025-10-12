"""
Vista de Notificaciones Android - CoProx

PROPÓSITO:
Este componente maneja la interfaz específica de Android para notificaciones
persistentes y gestión del estado del servicio en background.

FUNCIONAMIENTO:
- Configura y actualiza la notificación persistente del sistema
- Maneja eventos cuando usuario toca la notificación
- Proporciona información visual del estado del proxy en la notificación
- Gestiona transiciones entre estado foreground y background

PARÁMETROS DE ENTRADA:
- service_status: String indicando estado actual del servicio
- notification_config: Diccionario con configuración de la notificación
- proxy_statistics: Diccionario con estadísticas para mostrar
- lifecycle_event: String indicando evento de ciclo de vida Android

SALIDA ESPERADA:
- notification_tap_event: Evento cuando usuario toca notificación
- service_status_update: Actualización del contenido de la notificación
- foreground_service_request: Solicitud para mantener servicio activo
- notification_visibility_change: Cambio en visibilidad de notificación

PROCESAMIENTO DE DATOS:
- Formatea información de estado para mostrar en espacio limitado
- Selecciona iconos apropiados basándose en estado del servicio
- Actualiza contenido de notificación en tiempo real
- Maneja configuración específica de Android para persistencia

INTERACCIONES CON OTROS MÓDULOS:
- Utiliza: android_service.py (APIs de notificación nativa)
- Recibe datos de: proxy_model.py (estado para mostrar)
- Coordina con: flet_app.py (eventos de reapertura)
- Notifica a: app_controller.py (eventos de lifecycle)

INTERACCIONES CON MAIN:
- main.py activa esta vista cuando detecta plataforma Android
- Funciona independientemente para mantener presencia del servicio
- Proporciona la funcionalidad clave de supervivencia al minimizar
"""