"""
Modelo de Configuración - CoProx

PROPÓSITO:
Este módulo almacena todas las configuraciones constantes e inmutables del sistema.
Es el único lugar donde se definen valores como CLIENT_ID, URLs de API y headers HTTP.

FUNCIONAMIENTO:
- Actúa como una fuente única de verdad para la configuración
- Proporciona constantes que no cambian durante la ejecución
- Define los headers HTTP necesarios para comunicarse con GitHub Copilot
- Establece la configuración de OAuth para el flujo de autenticación

PARÁMETROS DE ENTRADA:
- Ninguno (solo constantes predefinidas)

SALIDA ESPERADA:
- CLIENT_ID: String con el identificador OAuth de GitHub
- API_URL: String con la URL base de la API de GitHub Copilot  
- HEADERS_BASE: Diccionario con headers HTTP estándar para todas las solicitudes
- OAUTH_SCOPE: String con los permisos solicitados en OAuth
- TOKEN_DIRECTORY: String con la ruta donde se almacenan los tokens

PROCESAMIENTO DE DATOS:
Los datos se mantienen como constantes inmutables. No requieren procesamiento,
solo lectura por parte de otros módulos.

INTERACCIONES CON OTROS MÓDULOS:
- Leído por: oauth_service.py (CLIENT_ID, headers)
- Leído por: http_service.py (API_URL, headers)
- Leído por: auth_controller.py (configuración de tokens)
- Leído por: file_service.py (directorios de tokens)

INTERACCIONES CON MAIN:
- main.py importa este módulo para acceder a configuraciones globales
- No requiere inicialización especial
- Se usa como referencia constante en toda la aplicación
"""