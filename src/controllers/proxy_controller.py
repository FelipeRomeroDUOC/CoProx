"""
Controlador del Proxy - CoProx

PROPÓSITO:
Este controlador gestiona el servidor HTTP proxy incluyendo endpoints Flask,
servidor Waitress en background y toda la lógica de reenvío de solicitudes.

FUNCIONAMIENTO:
- Inicia y detiene el servidor Waitress en un hilo separado
- Define y maneja endpoints Flask (/v1/chat/completions, /models)
- Coordina reenvío de solicitudes a la API oficial de GitHub Copilot
- Implementa lógica de compatibilidad con clientes OpenAI

PARÁMETROS DE ENTRADA:
- start_server_request: Boolean para iniciar el servidor proxy
- stop_server_request: Boolean para detener el servidor proxy
- client_request: Diccionario con solicitud HTTP del cliente
- server_config: Diccionario con configuración del servidor (host, puerto)

SALIDA ESPERADA:
- server_status: String indicando estado actual del servidor
- proxy_response: Diccionario con respuesta procesada para el cliente
- server_statistics: Diccionario con métricas del servidor
- operation_result: Boolean indicando éxito de operación

PROCESAMIENTO DE DATOS:
- Procesa solicitudes HTTP entrantes y las valida
- Reescribe nombres de modelo para compatibilidad con clientes
- Maneja desactivación forzada de streaming
- Agrega headers necesarios para comunicación con GitHub API
- Formatea respuestas según especificación OpenAI

INTERACCIONES CON OTROS MÓDULOS:
- Utiliza: http_service.py (comunicación con API Copilot)
- Utiliza: auth_controller.py (obtener tokens válidos)
- Actualiza: proxy_model.py (estadísticas del servidor)
- Notifica a: proxy_view.py (cambios de estado)
- Coordina con: android_service.py (notificaciones de estado)

INTERACCIONES CON MAIN:
- main.py inicializa este controlador al arrancar
- Funciona independientemente una vez iniciado
- Proporciona el servicio principal de la aplicación
"""