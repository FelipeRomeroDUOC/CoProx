"""
Servicio HTTP - CoProx

PROPÓSITO:
Este servicio maneja toda la comunicación HTTP con la API oficial de GitHub Copilot.
Actúa como cliente HTTP especializado para solicitudes de chat completions y modelos.

FUNCIONAMIENTO:
- Envía solicitudes POST a la API de chat completions de GitHub Copilot
- Maneja autenticación usando tokens Bearer en headers
- Realiza solicitudes GET para obtener lista de modelos disponibles
- Implementa reintentos automáticos y manejo de errores de red

PARÁMETROS DE ENTRADA:
- request_data: Diccionario con payload de la solicitud (messages, model, etc.)
- auth_token: String con token de autenticación para headers
- api_endpoint: String con el endpoint específico a llamar
- timeout: Entero con tiempo límite para la solicitud
- retry_count: Entero con número de reintentos en caso de error

SALIDA ESPERADA:
- response_data: Diccionario con la respuesta de la API de Copilot
- status_code: Entero con código HTTP de la respuesta
- response_headers: Diccionario con headers de la respuesta
- error_info: Diccionario con información de errores si ocurren

PROCESAMIENTO DE DATOS:
- Serializa datos de entrada a JSON válido
- Añade headers de autenticación y metadata requeridos
- Parsea respuestas JSON de la API
- Maneja códigos de error HTTP específicos (401, 429, 500)
- Implementa lógica de reintentos con backoff exponencial

INTERACCIONES CON OTROS MÓDULOS:
- Usado por: proxy_controller.py (reenviar solicitudes de clientes)
- Utiliza: config_model.py (API_URL y headers base)
- Notifica a: auth_model.py (si token es inválido)
- Interactúa con: proxy_model.py (actualizar estadísticas)

INTERACCIONES CON MAIN:
- No interactúa directamente con main.py
- Se utiliza indirectamente cuando el proxy procesa solicitudes
- Maneja toda la comunicación externa con APIs de GitHub
"""