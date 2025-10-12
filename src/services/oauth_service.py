"""
Servicio OAuth - CoProx

PROPÓSITO:
Este servicio maneja toda la comunicación OAuth con GitHub para obtener tokens de acceso.
Implementa el flujo de device-code flow para autenticación sin navegador.

FUNCIONAMIENTO:
- Inicia el flujo OAuth solicitando un código de dispositivo a GitHub
- Proporciona al usuario un código y URL para autorizar en el navegador
- Realiza polling periódico para verificar si el usuario completó la autorización
- Obtiene y retorna el token de acceso una vez completada la autenticación

PARÁMETROS DE ENTRADA:
- client_id: String con el identificador OAuth de la aplicación
- scope: String con los permisos solicitados (ej. "user:email")
- polling_interval: Entero con segundos entre verificaciones
- timeout: Entero con tiempo máximo de espera en segundos

SALIDA ESPERADA:
- access_token: String con el token de acceso obtenido
- device_code_response: Diccionario con código de dispositivo y URL de verificación
- authentication_status: String indicando estado del proceso (pending/completed/error)
- error_message: String con descripción de errores si ocurren

PROCESAMIENTO DE DATOS:
- Formatea solicitudes HTTP según especificación OAuth de GitHub
- Parsea respuestas JSON y extrae información necesaria
- Maneja errores específicos como token expirado o acceso denegado
- Implementa reintento automático en caso de errores temporales

INTERACCIONES CON OTROS MÓDULOS:
- Usado por: auth_controller.py (iniciar autenticación de nuevas cuentas)
- Utiliza: config_model.py (CLIENT_ID y URLs)
- Notifica a: auth_model.py (nuevos tokens obtenidos)
- Interactúa con: file_service.py (guardar tokens)

INTERACCIONES CON MAIN:
- main.py llama a este servicio cuando se usa --add-account
- Se ejecuta en modo interactivo requiriendo acción del usuario
- Maneja la comunicación con APIs externas de GitHub
"""