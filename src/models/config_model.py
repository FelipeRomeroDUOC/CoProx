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

from typing import Final

# ============================================================================
# CONFIGURACIÓN OAUTH - GitHub Device Flow
# ============================================================================

CLIENT_ID: Final[str] = "01ab8ac9400c4e429b23"
"""
ID de cliente OAuth para GitHub Copilot.
Este ID se usa en el flujo de autenticación de dispositivo (Device Flow).
Fuente: proxy_original.py línea 27
"""

OAUTH_SCOPE: Final[str] = "user:email"
"""
Permisos solicitados durante la autenticación OAuth.
Scope mínimo requerido para acceder a GitHub Copilot.
Fuente: proxy_original.py línea 49
"""

OAUTH_DEVICE_CODE_URL: Final[str] = "https://github.com/login/device/code"
"""
URL para solicitar código de dispositivo en OAuth Device Flow.
Paso 1 del flujo: obtener device_code y user_code.
Fuente: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow
"""

OAUTH_TOKEN_URL: Final[str] = "https://github.com/login/oauth/access_token"
"""
URL para intercambiar código de dispositivo por access_token.
Paso 3 del flujo: polling hasta que usuario autorice.
Fuente: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow
"""

OAUTH_VERIFICATION_URL: Final[str] = "https://github.com/login/device"
"""
URL donde el usuario debe ingresar el user_code.
Paso 2 del flujo: usuario ingresa código manualmente.
Fuente: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow
"""


# ============================================================================
# CONFIGURACIÓN API - GitHub Copilot
# ============================================================================

API_URL: Final[str] = "https://api.githubcopilot.com"
"""
URL base de la API de GitHub Copilot.
Todos los endpoints se construyen a partir de esta URL.
Fuente: proxy_original.py línea 28
"""

REQUEST_TIMEOUT: Final[int] = 30
"""
Timeout en segundos para todas las solicitudes HTTP.
Previene bloqueos indefinidos en requests.
Fuente: proxy_original.py línea 10
"""

CONTENT_TYPE_JSON: Final[str] = "application/json"
"""
Content-Type estándar para solicitudes y respuestas JSON.
Usado en headers de requests HTTP.
Fuente: proxy_original.py línea 7
"""


# ============================================================================
# HEADERS HTTP - GitHub Copilot API
# ============================================================================

HEADERS_BASE: Final[dict[str, str]] = {
    "copilot-integration-id": "vscode-chat",
    "editor-plugin-version": "copilot-chat/0.23.2",
    "editor-version": "vscode/1.96.3",
    "user-agent": "GitHubCopilotChat/0.23.2",
    "x-github-api-version": "2024-12-15"
}
"""
Headers HTTP base requeridos por la API de GitHub Copilot.
Estos headers se incluyen en todas las solicitudes a la API.
Simulan que las requests provienen de VS Code oficial.
Fuente: proxy_original.py líneas 34-40
"""


# ============================================================================
# CONFIGURACIÓN DEL SERVIDOR PROXY
# ============================================================================

DEFAULT_HOST: Final[str] = "0.0.0.0"
"""
Host por defecto del servidor proxy.
0.0.0.0 permite conexiones desde todas las interfaces de red.
Fuente: proxy_original.py línea 256
"""

DEFAULT_PORT: Final[int] = 5000
"""
Puerto por defecto del servidor proxy.
Puerto estándar usado por el proxy para escuchar solicitudes.
Fuente: proxy_original.py línea 256
"""


# ============================================================================
# CONFIGURACIÓN DE ALMACENAMIENTO - Tokens
# ============================================================================

TOKEN_DIRECTORY: Final[str] = "."
"""
Directorio donde se almacenan los archivos de tokens.
Por defecto es el directorio actual del proyecto.
Fuente: proxy_original.py (almacenamiento en directorio raíz)
"""

TOKEN_FILE_PREFIX: Final[str] = ".copilot_token"
"""
Nombre del archivo token principal.
Los tokens se guardan con este prefijo.
Fuente: proxy_original.py línea 8
"""

TOKEN_FILE_EXTENSION: Final[str] = ".copilot_token"
"""
Extensión de los archivos de tokens.
Tokens adicionales: 1.copilot_token, 2.copilot_token, etc.
Fuente: proxy_original.py línea 9
"""

TOKENS_EXHAUSTED_DIR: Final[str] = "TokensAgotados"
"""
Directorio donde se mueven los tokens sin cuota disponible.
Permite recuperación automática cuando la cuota se restablece.
Fuente: proxy_original.py línea 11
"""