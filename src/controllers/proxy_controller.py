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

import multiprocessing
import signal
import sys
from typing import Dict, Any, Tuple, Optional
from flask import Flask, request, jsonify
import requests
import waitress

# Importar modelos
from src.models.config_model import (
    API_URL,
    HEADERS_BASE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    REQUEST_TIMEOUT
)
from src.models.auth_model import AuthModel
from src.models.proxy_model import ProxyModel


class ProxyController:
    """
    Controlador principal del proxy que gestiona el servidor HTTP
    y coordina todas las operaciones de reenvío.
    """
    
    def __init__(self):
        """Inicializa el controlador del proxy con modelos integrados"""
        self._running = False
        self._server_process: Optional[multiprocessing.Process] = None
        self._host = DEFAULT_HOST
        self._port = DEFAULT_PORT
        self._app = self._create_flask_app()
        
        # Modelos integrados
        self._auth_model = AuthModel()
        self._proxy_model = ProxyModel()
        
    def _create_flask_app(self) -> Flask:
        """Crea y configura la aplicación Flask"""
        app = Flask(__name__)
        
        # Endpoint principal: /v1/chat/completions
        @app.route("/v1/chat/completions", methods=["POST"])
        @app.route("/chat/completions", methods=["POST"])
        def chat_completions():
            """Endpoint para completions de chat"""
            try:
                # Validar y preparar solicitud
                validation_result = self._validate_chat_completion_request(request.json)
                if validation_result is not None:
                    return validation_result
                
                data = request.json
                assert data is not None, "Data should not be None after validation"
                
                # Procesar solicitud
                return self._process_chat_completion(data)
                
            except (requests.RequestException, ValueError, KeyError, TypeError, 
                    AttributeError, AssertionError) as e:
                return jsonify(self.format_error_response(str(e))), 500
        
        # Endpoint de modelos
        @app.route("/models", methods=["GET"])
        def list_models():
            """Endpoint para listar modelos disponibles"""
            try:
                return self._process_list_models()
            except (requests.RequestException, ValueError, KeyError, TypeError) as e:
                return jsonify(self.format_error_response(f"API request failed: {str(e)}")), 500
        
        return app
    
    def start_server(self, host: str = '0.0.0.0', port: int = 5000) -> bool:
        """
        Inicia el servidor Waitress en un proceso separado
        
        Args:
            host: Host donde escuchar
            port: Puerto donde escuchar
            
        Returns:
            True si se inició correctamente, False si ya estaba corriendo
        """
        if self._running:
            return False
        
        self._host = host
        self._port = port
        self._running = True
        
        # Crear proceso separado (NO daemon para graceful shutdown)
        self._server_process = multiprocessing.Process(
            target=self._run_server_process,
            args=(host, port),
            daemon=False
        )
        self._server_process.start()
        
        return True
    
    def _run_server_process(self, host: str, port: int):
        """
        Ejecuta el servidor Waitress en un proceso separado
        
        Esta función se ejecuta en un proceso diferente, lo que permite
        que el servidor y la UI de Flet coexistan sin bloquearse.
        
        Args:
            host: Host donde escuchar
            port: Puerto donde escuchar
        """
        # Configurar manejo de señales para shutdown graceful
        def signal_handler(signum, frame):  # pylint: disable=unused-argument
            """Handler para señales SIGTERM/SIGINT. Los parámetros son requeridos por signal API."""
            print("Recibida señal de shutdown, cerrando servidor...")
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            print(f"Servidor proxy iniciado en {host}:{port}")
            waitress.serve(
                self._app,
                host=host,
                port=port,
                threads=4,
                channel_timeout=30
            )
        except (OSError, RuntimeError, ValueError) as e:
            # Errores de red, configuración o servidor
            print(f"Error en servidor: {e}")
    
    def stop_server(self) -> bool:
        """
        Detiene el servidor de forma graceful
        
        Envía señal SIGTERM al proceso del servidor y espera hasta 5 segundos
        a que termine procesando las solicitudes actuales. Si no responde,
        fuerza el cierre con SIGKILL.
        
        Returns:
            True si se detuvo correctamente, False si no estaba corriendo
        """
        if not self._running:
            return False
        
        self._running = False
        
        try:
            if self._server_process and self._server_process.is_alive():
                print("Deteniendo servidor proxy...")
                
                # Enviar señal SIGTERM (shutdown graceful)
                self._server_process.terminate()
                
                # Esperar hasta 5 segundos a que termine
                self._server_process.join(timeout=5.0)
                
                # Si después de 5 segundos sigue vivo, forzar cierre
                if self._server_process.is_alive():
                    print("Servidor no respondió, forzando cierre...")
                    self._server_process.kill()
                    self._server_process.join(timeout=1.0)
                
                print("Servidor detenido correctamente")
            
            return True
            
        except (OSError, RuntimeError) as e:
            # Errores al detener proceso (OSError incluye TimeoutError)
            print(f"Error al detener servidor: {e}")
            return False
    
    def is_running(self) -> bool:
        """Retorna si el servidor está corriendo"""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado del servidor"""
        return {
            'running': self._running,
            'host': self._host,
            'port': self._port
        }
    
    def get_flask_app(self) -> Flask:
        """Retorna la instancia de Flask para testing"""
        return self._app
    
    def _validate_chat_completion_request(self, data: Optional[Dict]) -> Optional[Tuple[Any, int]]:
        """
        Valida solicitud de chat y retorna error si no es válida.
        
        Args:
            data: Datos de la solicitud
            
        Returns:
            Tupla (response, status_code) si hay error, None si es válida
        """
        # Validar estructura básica
        is_valid, error = self.validate_chat_request(data)
        if not is_valid:
            return jsonify(self.format_error_response(error or "Invalid request")), 400
        
        # Validar streaming
        if data and data.get('stream'):
            return jsonify(self.format_streaming_disabled_response()), 200
        
        # Validar disponibilidad de token
        token = self.get_current_token()
        if token is None:
            return jsonify(self.format_error_response(
                "No authentication tokens available"
            )), 503
        
        return None
    
    def _process_chat_completion(self, data: Dict) -> Tuple[Any, int]:
        """
        Procesa una solicitud de chat completion.
        
        Args:
            data: Datos validados de la solicitud
            
        Returns:
            Tupla (response, status_code)
        """
        token = self.get_current_token()
        assert token is not None, "Token should exist after validation"
        
        # Reenviar a Copilot
        response = self.forward_to_copilot(data, token)
        
        # Actualizar ProxyModel
        self._proxy_model.update_last_request_time()
        
        # Reescribir nombre de modelo
        response = self.rewrite_model_name(data, response)
        
        # Formatear respuesta
        formatted = self.format_openai_response(response)
        
        # Incrementar contador
        self.increment_request_counter()
        
        return jsonify(formatted), 200
    
    def _process_list_models(self) -> Tuple[Any, int]:
        """
        Procesa solicitud de listado de modelos.
        
        Returns:
            Tupla (response, status_code)
        """
        token = self.get_current_token()
        if token is None:
            return jsonify(self.format_error_response(
                "No authentication tokens available"
            )), 503
        
        resp = requests.get(
            f"{API_URL}/models",
            headers={
                "authorization": f"Bearer {token}",
                **HEADERS_BASE
            },
            timeout=REQUEST_TIMEOUT
        )
        
        return resp.text, resp.status_code
    
    def validate_chat_request(self, data: Optional[Dict]) -> Tuple[bool, Optional[str]]:
        """
        Valida que una solicitud de chat tenga el formato correcto
        
        Args:
            data: Datos de la solicitud
            
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if data is None:
            return False, "Request body must be valid JSON"
        
        if 'model' not in data:
            return False, "Missing required field: model"
        
        if 'messages' not in data:
            return False, "Missing required field: messages"
        
        if not isinstance(data['messages'], list) or len(data['messages']) == 0:
            return False, "Field 'messages' must be a non-empty array"
        
        return True, None
    
    def forward_to_copilot(self, data: Dict, token: str) -> Dict:
        """
        Reenvía una solicitud a la API de GitHub Copilot
        
        Args:
            data: Datos de la solicitud
            token: Token de autenticación
            
        Returns:
            Respuesta de la API o error formateado
        """
        try:
            resp = requests.post(
                f"{API_URL}/chat/completions",
                headers={
                    "authorization": f"Bearer {token}",
                    "content-type": "application/json",
                    **HEADERS_BASE
                },
                json=data,
                timeout=REQUEST_TIMEOUT
            )
            
            return resp.json()
            
        except requests.Timeout:
            return self.format_error_response("Request timeout: API took too long to respond")
        except requests.ConnectionError:
            return self.format_error_response("Connection error: Could not reach GitHub Copilot API")
        except requests.RequestException as e:
            return self.format_error_response(f"API request failed: {str(e)}")
        except (ValueError, TypeError, KeyError) as e:
            # Errores al parsear JSON o acceder a datos de respuesta
            return self.format_error_response(f"Invalid API response: {str(e)}")
    
    def rewrite_model_name(self, request_data: Dict, response_data: Dict) -> Dict:
        """
        Reescribe el nombre del modelo en la respuesta para compatibilidad
        
        Args:
            request_data: Datos de la solicitud original
            response_data: Datos de la respuesta
            
        Returns:
            Respuesta con modelo reescrito
        """
        requested_model = request_data.get('model', '')
        
        # Mantener nombre para modelos específicos
        if any(model in requested_model.lower() for model in ["claude-3.5-sonnet", "gpt-4o"]):
            response_data['model'] = requested_model
        
        return response_data
    
    def handle_streaming(self, request_data: Dict) -> Dict:
        """
        Maneja la desactivación de streaming
        
        Args:
            request_data: Datos de la solicitud
            
        Returns:
            Solicitud modificada con streaming desactivado
        """
        if request_data.get('stream'):
            request_data['stream'] = False
        return request_data
    
    def format_openai_response(self, response: Dict) -> Dict:
        """
        Formatea una respuesta según especificación OpenAI
        
        Args:
            response: Respuesta cruda
            
        Returns:
            Respuesta formateada
        """
        return response
    
    def format_error_response(self, error_message: str) -> Dict:
        """
        Formatea un mensaje de error según especificación OpenAI
        
        Args:
            error_message: Mensaje de error
            
        Returns:
            Error formateado
        """
        return {
            "error": {
                "message": error_message,
                "type": "internal_error"
            }
        }
    
    def format_streaming_disabled_response(self) -> Dict:
        """
        Retorna un mensaje indicando que el streaming debe desactivarse
        
        Returns:
            Respuesta con mensaje
        """
        return {
            "choices": [{
                "message": {
                    "content": "Por favor desactiva el streaming en tu cliente",
                    "role": "assistant"
                }
            }]
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas del servidor usando modelos"""
        proxy_stats = self._proxy_model.get_statistics()
        auth_stats = self._auth_model.get_statistics()
        
        return {
            'total_requests': proxy_stats['total_requests'],
            'current_quota': auth_stats.get('current_quota'),
            'total_accounts': auth_stats['total_accounts']
        }
    
    def increment_request_counter(self):
        """Incrementa el contador de solicitudes en ProxyModel"""
        self._proxy_model.increment_request_counter()
    
    # Métodos de acceso a modelos para tests
    def get_auth_model(self) -> AuthModel:
        """Retorna la instancia de AuthModel"""
        return self._auth_model
    
    def get_proxy_model(self) -> ProxyModel:
        """Retorna la instancia de ProxyModel"""
        return self._proxy_model
    
    def get_current_token(self) -> Optional[str]:
        """Obtiene el token actual desde AuthModel"""
        return self._auth_model.get_current_token()
    
    def get_api_url(self) -> str:
        """Retorna la URL de la API desde ConfigModel"""
        return API_URL
    
    def get_headers_base(self) -> Dict[str, str]:
        """Retorna los headers base desde ConfigModel"""
        return HEADERS_BASE