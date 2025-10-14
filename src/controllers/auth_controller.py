"""
Controlador de Autenticación - CoProx

PROPÓSITO:
Este controlador coordina toda la lógica de autenticación incluyendo gestión de tokens,
rotación automática de cuentas y adición de nuevas cuentas de GitHub Copilot.

FUNCIONAMIENTO:
- Coordina el flujo completo de autenticación OAuth para nuevas cuentas
- Gestiona la rotación automática de tokens cuando se agotan cuotas
- Mantiene el estado de autenticación actualizado en los modelos
- Implementa lógica de recuperación de cuentas agotadas

PARÁMETROS DE ENTRADA:
- add_account_request: Boolean para iniciar proceso de nueva cuenta
- token_rotation_trigger: Evento que indica necesidad de rotar token
- quota_check_interval: Entero con segundos entre verificaciones de cuota
- recovery_check_trigger: Evento para verificar tokens agotados

SALIDA ESPERADA:
- authentication_result: Diccionario con resultado de autenticación
- current_active_token: String con token válido para usar
- account_status_update: Diccionario con estado actualizado de cuentas
- rotation_success: Boolean indicando éxito de rotación de token

PROCESAMIENTO DE DATOS:
- Valida tokens obtenidos antes de almacenarlos
- Coordina con oauth_service para obtener nuevos tokens
- Actualiza auth_model con información de nuevas cuentas
- Implementa lógica para detectar y manejar tokens expirados
- Gestiona numeración secuencial de archivos de tokens

INTERACCIONES CON OTROS MÓDULOS:
- Utiliza: oauth_service.py (autenticación OAuth)
- Utiliza: file_service.py (guardar/leer tokens)
- Actualiza: auth_model.py (estado de autenticación)
- Notifica a: auth_view.py (cambios en cuentas)
- Coordina con: proxy_controller.py (tokens para solicitudes)

INTERACCIONES CON MAIN:
- main.py llama a este controlador cuando detecta --add-account
- Se ejecuta continuamente para mantener tokens válidos
- Proporciona tokens activos para el funcionamiento del proxy

Metodología: Test-Driven Development (TDD)
Fase: GREEN - Implementación que hace pasar los tests
"""

from typing import Optional, Dict, Any
import requests
import time
import logging

from src.models.auth_model import AuthModel
from src.models.config_model import (
    CLIENT_ID, 
    OAUTH_SCOPE, 
    REQUEST_TIMEOUT,
    OAUTH_DEVICE_CODE_URL,
    OAUTH_TOKEN_URL
)

# Configurar logger
logger = logging.getLogger(__name__)


class AuthController:
    """
    Controlador para gestión de autenticación OAuth con GitHub.
    
    Implementa el flujo OAuth 2.0 Device Authorization Grant según:
    https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow
    """
    
    def __init__(self, auth_model: Optional[AuthModel] = None):
        """
        Inicializa el controlador de autenticación.
        
        Args:
            auth_model: Modelo de autenticación opcional. Si no se proporciona,
                       se crea uno por defecto.
        """
        self._auth_model = auth_model if auth_model is not None else AuthModel()
        self._device_code_data: Optional[Dict[str, Any]] = None
    
    def request_device_code(self) -> Dict[str, Any]:
        """
        Solicita código de dispositivo a GitHub OAuth.
        
        Paso 1 del Device Flow: Obtiene device_code, user_code y verification_uri
        que se usarán para que el usuario autorice la aplicación.
        
        Returns:
            Dict con las siguientes claves:
                - device_code: str - Código de dispositivo (40 caracteres)
                - user_code: str - Código para mostrar al usuario (8 caracteres)
                - verification_uri: str - URL donde el usuario ingresa el código
                - expires_in: int - Segundos antes de que expiren los códigos
                - interval: int - Segundos mínimos entre cada polling request
        
        Raises:
            requests.Timeout: Error de timeout en la conexión
            requests.ConnectionError: Error de red
            requests.RequestException: Error general de HTTP
            ValueError: Respuesta inválida de la API o CLIENT_ID no configurado
        """
        # Validar que CLIENT_ID está configurado
        if not CLIENT_ID or not isinstance(CLIENT_ID, str):
            raise ValueError("CLIENT_ID not configured or invalid")
        
        try:
            response = requests.post(
                OAUTH_DEVICE_CODE_URL,
                data={
                    "client_id": CLIENT_ID,
                    "scope": OAUTH_SCOPE
                },
                headers={"accept": "application/json"},
                timeout=REQUEST_TIMEOUT
            )
            
            # Verificar que la respuesta fue exitosa
            if response.status_code != 200:
                raise requests.RequestException(
                    f"GitHub API returned status {response.status_code}"
                )
            
            data = response.json()
            
            # Validar que la respuesta contiene los campos necesarios
            required_fields = ["device_code", "user_code", "verification_uri", "interval"]
            if not all(field in data for field in required_fields):
                raise ValueError(
                    "Invalid response from GitHub API: missing required fields"
                )
            
            # Guardar para uso posterior
            self._device_code_data = data
            
            return data
            
        except requests.Timeout as e:
            raise requests.Timeout(f"Timeout requesting device code: {e}") from e
        except requests.ConnectionError as e:
            raise requests.ConnectionError(f"Network error requesting device code: {e}") from e
        except ValueError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e
    
    def _handle_polling_error(self, error: str, device_code: str) -> tuple[bool, int]:
        """
        Maneja errores del polling de autorización.
        
        Args:
            error: Código de error de GitHub OAuth
            device_code: Código de dispositivo siendo verificado
        
        Returns:
            Tupla (should_continue, new_interval_addition)
            - should_continue: True si debe continuar polling, False si debe lanzar excepción
            - new_interval_addition: Segundos adicionales para el intervalo (0 si no aplica)
        
        Raises:
            ValueError: Para errores fatales (expired, access_denied, incorrect_device_code)
        """
        if error == "authorization_pending":
            # Usuario aún no ha autorizado, continuar polling
            return (True, 0)
        
        if error == "slow_down":
            # Rate limit: agregar 5 segundos al intervalo
            return (True, 5)
        
        if error == "expired_token":
            raise ValueError(
                "Device code expired. Please request a new device code."
            )
        
        if error == "access_denied":
            raise ValueError(
                "User denied access or cancelled authorization."
            )
        
        if error == "incorrect_device_code":
            raise ValueError(
                f"Invalid device code: {device_code}"
            )
        
        # Error desconocido
        raise ValueError(f"Authorization error: {error}")
    
    def poll_for_authorization(
        self, 
        device_code: str, 
        interval: int,
        max_attempts: int = 100
    ) -> str:
        """
        Hace polling hasta que el usuario autorice la aplicación.
        
        Paso 3 del Device Flow: Verifica periódicamente si el usuario ha autorizado
        la aplicación ingresando el user_code en GitHub.
        
        Args:
            device_code: Código de dispositivo obtenido de request_device_code()
            interval: Segundos mínimos entre cada request (respeta rate limiting)
            max_attempts: Número máximo de intentos antes de timeout (default: 100)
        
        Returns:
            str: access_token autorizado por el usuario
        
        Raises:
            TimeoutError: Usuario no autorizó en el tiempo límite
            ValueError: Token expiró, acceso denegado, device_code inválido o error de autorización
            requests.RequestException: Error en la comunicación con GitHub
        """
        # Validar inputs
        if not device_code or not isinstance(device_code, str):
            raise ValueError("device_code must be a non-empty string")
        if not isinstance(interval, int) or interval < 1:
            raise ValueError("interval must be a positive integer")
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        
        current_interval = interval
        
        for attempt in range(max_attempts):
            try:
                # Esperar el intervalo requerido antes de cada request
                if attempt > 0:  # No esperar en el primer intento
                    time.sleep(current_interval)
                
                response = requests.post(
                    OAUTH_TOKEN_URL,
                    data={
                        "client_id": CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    },
                    headers={"accept": "application/json"},
                    timeout=REQUEST_TIMEOUT
                )
                
                data = response.json()
                
                # Si recibimos access_token, autorización exitosa
                if "access_token" in data:
                    return data["access_token"]
                
                # Manejar errores según documentación de GitHub
                if "error" in data:
                    should_continue, interval_addition = self._handle_polling_error(
                        data["error"], device_code
                    )
                    
                    if should_continue:
                        current_interval += interval_addition
                        continue
                
            except requests.RequestException as e:
                # En errores de red, reintentar
                if attempt < max_attempts - 1:
                    continue
                raise requests.RequestException(f"Network error during polling: {e}")
        
        # Si se excedieron los intentos máximos
        raise TimeoutError(
            f"Authorization timeout: user did not authorize within {max_attempts} attempts"
        )
    
    def authenticate(self) -> str:
        """
        Ejecuta el flujo completo de autenticación OAuth Device Flow.
        
        Este método orquesta los 3 pasos del Device Flow:
        1. Solicitar device_code y user_code
        2. (Usuario ingresa código en GitHub - manual)
        3. Polling hasta obtener access_token
        
        Returns:
            str: access_token autorizado
        
        Raises:
            TimeoutError: Usuario no autorizó en tiempo límite
            ValueError: Error en el proceso de autorización
            requests.RequestException: Error de red o HTTP
        
        Example:
            >>> controller = AuthController()
            >>> token = controller.authenticate()
            >>> print(f"Token obtenido: {token}")
        """
        logger.info("Iniciando flujo de autenticación OAuth Device Flow")
        
        # Paso 1: Solicitar códigos de dispositivo
        device_data = self.request_device_code()
        logger.info("Device code obtenido. User code: %s", device_data['user_code'])
        
        # Paso 2: Mostrar información al usuario (en implementación real)
        # print(f"Visita: {device_data['verification_uri']}")
        # print(f"Ingresa el código: {device_data['user_code']}")
        
        # Paso 3: Polling para verificar autorización
        access_token = self.poll_for_authorization(
            device_code=device_data["device_code"],
            interval=device_data["interval"]
        )
        
        logger.info("Autenticación OAuth completada exitosamente")
        return access_token
    
    def verify_token_quota(self, access_token: str) -> Dict[str, Any]:
        """
        Verifica cuota disponible del token con GitHub Copilot API.
        
        Args:
            access_token: Token de acceso de GitHub OAuth
        
        Returns:
            Dict con información de cuota y token de Copilot:
                - token: str - Token de Copilot para usar en API
                - limited_user_quotas: dict - Cuotas disponibles por tipo
                - limited_user_reset_date: str - Fecha de reseteo de cuotas (opcional)
        
        Raises:
            requests.RequestException: Error en la comunicación con GitHub
            ValueError: Token vacío o respuesta inválida de la API
        
        Example:
            >>> controller = AuthController()
            >>> quota_info = controller.verify_token_quota("gho_...")
            >>> print(f"Cuota chat: {quota_info['limited_user_quotas']['chat']}")
        """
        # Validar input
        if not access_token or not isinstance(access_token, str):
            raise ValueError("access_token must be a non-empty string")
        
        try:
            from src.models.config_model import HEADERS_BASE
            
            response = requests.get(
                "https://api.github.com/copilot_internal/v2/token",
                headers={
                    "authorization": f"token {access_token}",
                    **HEADERS_BASE
                },
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                raise requests.RequestException(
                    f"GitHub Copilot API returned status {response.status_code}"
                )
            
            data = response.json()
            
            # Validar que la respuesta contiene información de cuota
            if "token" not in data:
                raise ValueError("Invalid response: missing 'token' field")
            
            return data
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Error verifying token quota: {e}") from e
        except ValueError as e:
            raise ValueError(f"Invalid quota response: {e}") from e
    
    def add_account(self) -> Dict[str, Any]:
        """
        Ejecuta flujo completo: autenticar + verificar cuota + guardar en AuthModel.
        
        Este método coordina:
        1. Autenticación OAuth Device Flow
        2. Verificación de cuota del token obtenido
        3. Almacenamiento en AuthModel si tiene cuota disponible
        4. Detección de duplicados
        
        Returns:
            Dict con resultado de la operación:
                - access_token: str - Token obtenido
                - quota_info: dict - Información de cuota
                - duplicate: bool - True si el token ya existía
                - success: bool - True si se agregó exitosamente
        
        Raises:
            TimeoutError: Usuario no autorizó en tiempo límite
            ValueError: Error en autenticación o verificación
            requests.RequestException: Error de red
        
        Example:
            >>> controller = AuthController()
            >>> result = controller.add_account()
            >>> if result['success']:
            ...     print(f"Cuenta agregada con {result['quota_info']['chat']} cuota")
        """
        logger.info("Iniciando proceso de agregar nueva cuenta")
        
        # Paso 1: Autenticar y obtener access_token
        access_token = self.authenticate()
        
        # Paso 2: Verificar cuota del token
        quota_info = self.verify_token_quota(access_token)
        chat_quota = quota_info.get("limited_user_quotas", {}).get("chat", 0)
        logger.info("Token verificado. Cuota disponible: %d", chat_quota)
        
        # Paso 3: Verificar si el token ya existe (detectar duplicados)
        try:
            # Intentar obtener el token actual - si existe, es duplicado
            current_token = self._auth_model.get_current_token()
            is_duplicate = (current_token == access_token)
        except (KeyError, ValueError):
            # No hay tokens, no es duplicado
            is_duplicate = False
        
        # Paso 4: Agregar al AuthModel si no es duplicado
        if not is_duplicate:
            self._auth_model.add_account(
                token=access_token,
                quota_remaining=chat_quota,
                quota_total=chat_quota
            )
            logger.info("Cuenta agregada exitosamente")
        else:
            logger.warning("Token duplicado detectado. No se agregó la cuenta")
        
        return {
            "access_token": access_token,
            "quota_info": quota_info.get("limited_user_quotas", {}),
            "duplicate": is_duplicate,
            "success": not is_duplicate
        }
    
    def verify_specific_token(self, token: str) -> bool:
        """
        Verifica si un token específico tiene cuota disponible.
        
        Este método es útil para verificar tokens en la carpeta TokensAgotados/
        y determinar si han sido restablecidos y pueden ser recuperados.
        
        Args:
            token: Token de acceso a verificar
        
        Returns:
            True si el token tiene cuota disponible (chat > 0), False si no
        
        Raises:
            ValueError: Si el token está vacío o es inválido
        
        Example:
            >>> controller = AuthController()
            >>> if controller.verify_specific_token("gho_..."):
            ...     print("Token tiene cuota disponible")
        """
        # Validar input
        if not token or not isinstance(token, str):
            raise ValueError("token must be a non-empty string")
        
        try:
            quota_info = self.verify_token_quota(token)
            chat_quota = quota_info.get("limited_user_quotas", {}).get("chat", 0)
            return chat_quota > 0
        except (requests.RequestException, ValueError) as e:
            # En caso de error, asumir que no tiene cuota
            logger.warning("Error verificando token: %s", e)
            return False
    
    def check_exhausted_tokens(self, exhausted_dir: Optional[str] = None) -> list[str]:
        """
        Verifica tokens en TokensAgotados/ y restaura los que tienen cuota.
        
        Este método:
        1. Escanea la carpeta TokensAgotados/
        2. Verifica la cuota de cada token
        3. Restaura tokens con cuota disponible agregándolos al AuthModel
        4. Actualiza las estadísticas del modelo
        
        Args:
            exhausted_dir: Ruta a la carpeta de tokens exhaustos (opcional).
                          Por defecto usa "TokensAgotados"
        
        Returns:
            Lista de tokens que fueron restaurados exitosamente
        
        Example:
            >>> controller = AuthController()
            >>> restored = controller.check_exhausted_tokens()
            >>> print(f"Tokens restaurados: {len(restored)}")
        """
        import os
        
        # Usar directorio por defecto si no se especifica
        if exhausted_dir is None:
            exhausted_dir = "TokensAgotados"
        
        logger.info("Verificando tokens exhaustos en: %s", exhausted_dir)
        
        # Verificar si existe la carpeta
        if not os.path.exists(exhausted_dir):
            logger.info("Directorio %s no existe", exhausted_dir)
            return []
        
        restored_tokens = []
        
        try:
            # Obtener todos los archivos .copilot_token en la carpeta
            token_files = [
                f for f in os.listdir(exhausted_dir)
                if f.endswith(".copilot_token")
            ]
            
            logger.info("Encontrados %d archivos de tokens", len(token_files))
            
            for token_file in token_files:
                try:
                    # Leer el contenido del token
                    token_path = os.path.join(exhausted_dir, token_file)
                    with open(token_path, 'r', encoding='utf-8') as f:
                        token = f.read().strip()
                    
                    # Verificar si el token tiene cuota
                    if self.verify_specific_token(token):
                        # Token tiene cuota - agregarlo al AuthModel
                        quota_info = self.verify_token_quota(token)
                        chat_quota = quota_info.get("limited_user_quotas", {}).get("chat", 0)
                        
                        self._auth_model.add_account(
                            token=token,
                            quota_remaining=chat_quota,
                            quota_total=chat_quota
                        )
                        
                        restored_tokens.append(token)
                        logger.info("Token restaurado: %s", token_file)
                        
                        # Opcional: eliminar el archivo de TokensAgotados/
                        # os.remove(token_path)
                        
                except (OSError, ValueError) as e:
                    # Error leyendo un archivo específico - continuar con el siguiente
                    logger.warning("Error procesando %s: %s", token_file, e)
                    continue
            
            logger.info("Proceso completado. Tokens restaurados: %d", len(restored_tokens))
            return restored_tokens
            
        except OSError as e:
            # Error accediendo a la carpeta
            logger.error("Error accediendo a %s: %s", exhausted_dir, e)
            return []