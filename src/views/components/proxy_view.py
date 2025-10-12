"""
Vista de Controles del Proxy - CoProx

PROPÓSITO:
Este componente de vista maneja la interfaz para iniciar/detener el servidor proxy
y mostrar estadísticas de funcionamiento en tiempo real.

FUNCIONAMIENTO:
- Muestra botones para iniciar y detener el servidor proxy
- Presenta estadísticas en tiempo real (solicitudes, errores, uptime)
- Indica estado visual del servidor (activo/inactivo)
- Proporciona información sobre puerto y endpoint URLs

PARÁMETROS DE ENTRADA:
- proxy_status: Diccionario con estado actual del servidor
- server_statistics: Diccionario con métricas de rendimiento
- user_interaction: Eventos de clic en botones de control
- refresh_interval: Entero con segundos entre actualizaciones de estadísticas

SALIDA ESPERADA:
- start_server_event: Evento generado cuando usuario inicia servidor
- stop_server_event: Evento generado cuando usuario detiene servidor
- ui_update_request: Solicitud de actualización de estadísticas mostradas
- status_display: Componentes UI actualizados con estado actual

PROCESAMIENTO DE DATOS:
- Formatea estadísticas numéricas para mostrar de forma legible
- Implementa indicadores visuales de estado (colores, iconos)
- Valida acciones de usuario antes de generar eventos
- Actualiza componentes UI en respuesta a cambios de estado

INTERACCIONES CON OTROS MÓDULOS:
- Recibe datos de: proxy_model.py (estado y estadísticas)
- Genera eventos para: proxy_controller.py (iniciar/detener servidor)
- Se integra en: flet_app.py (como componente de la interfaz principal)
- Coordina con: android_service.py (actualizaciones de notificación)

INTERACCIONES CON MAIN:
- No interactúa directamente con main.py
- Se inicializa a través de flet_app.py cuando main.py arranca la UI
- Proporciona la interfaz principal para la funcionalidad core del proxy
"""