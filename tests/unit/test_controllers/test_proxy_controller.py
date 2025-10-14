"""
Tests Unitarios para ProxyController - CoProx

Estrategia TDD:
1. RED: Escribir tests que fallen
2. GREEN: Implementar código mínimo para pasar tests
3. REFACTOR: Mejorar código manteniendo tests verdes

Cobertura objetivo: 95%+
"""

from unittest.mock import Mock, patch


class TestProxyControllerServerLifecycle:
    """Tests para inicio y detención del servidor Waitress"""
    
    @patch('src.controllers.proxy_controller.multiprocessing.Process')
    @patch('src.controllers.proxy_controller.waitress.serve')
    def test_start_server_creates_process(self, mock_serve, mock_process):
        """Test: start_server() debe crear un proceso para el servidor"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        result = controller.start_server(host='0.0.0.0', port=5000)
        
        # Verificar que se creó un proceso
        mock_process.assert_called_once()
        assert result is True
        assert controller.is_running() is True
    
    @patch('src.controllers.proxy_controller.multiprocessing.Process')
    def test_start_server_process_not_daemon(self, mock_process):
        """Test: El proceso del servidor NO debe ser daemon para shutdown graceful"""
        from src.controllers.proxy_controller import ProxyController
        
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance
        
        controller = ProxyController()
        controller.start_server(host='0.0.0.0', port=5000)
        
        # Verificar que daemon=False (para poder hacer terminate)
        call_kwargs = mock_process.call_args[1]
        assert call_kwargs.get('daemon') is False
    
    def test_stop_server_when_running(self):
        """Test: stop_server() debe detener el servidor correctamente"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        # Simular servidor corriendo
        controller._running = True
        mock_process = Mock()
        mock_process.is_alive.return_value = True
        controller._server_process = mock_process
        
        result = controller.stop_server()
        
        # Verificar que se llamó terminate() para graceful shutdown
        mock_process.terminate.assert_called_once()
        mock_process.join.assert_called()
        assert result is True
        assert controller.is_running() is False
    
    def test_stop_server_graceful_timeout(self):
        """Test: Si el proceso no termina en 5s, debe forzar con kill()"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        controller._running = True
        mock_process = Mock()
        # Simular que sigue vivo después de terminate
        mock_process.is_alive.side_effect = [True, True, True]
        controller._server_process = mock_process
        
        result = controller.stop_server()
        
        # Verificar que se llamó kill() después de terminate
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert result is True
    
    def test_stop_server_already_stopped(self):
        """Test: Si el proceso ya terminó, no hacer nada"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        controller._running = True
        mock_process = Mock()
        mock_process.is_alive.return_value = False
        controller._server_process = mock_process
        
        result = controller.stop_server()
        
        # No debe llamar terminate si ya está muerto
        mock_process.terminate.assert_not_called()
        assert result is True
    
    def test_stop_server_when_not_running(self):
        """Test: stop_server() debe retornar False si no está corriendo"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        result = controller.stop_server()
        
        assert result is False
    
    def test_cannot_start_server_twice(self):
        """Test: No se debe poder iniciar el servidor si ya está corriendo"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        controller._running = True
        
        result = controller.start_server(host='0.0.0.0', port=5000)
        
        assert result is False
    
    def test_get_server_status(self):
        """Test: get_status() debe retornar información del servidor"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        controller._running = True
        controller._host = '0.0.0.0'
        controller._port = 5000
        
        status = controller.get_status()
        
        assert status['running'] is True
        assert status['host'] == '0.0.0.0'
        assert status['port'] == 5000


class TestProxyControllerFlaskApp:
    """Tests para la aplicación Flask y sus endpoints"""
    
    def test_flask_app_creation(self):
        """Test: El controlador debe crear una instancia de Flask"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        app = controller.get_flask_app()
        
        assert app is not None
        assert hasattr(app, 'route')
    
    def test_chat_completions_endpoint_exists(self):
        """Test: Endpoint /v1/chat/completions debe existir"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        app = controller.get_flask_app()
        
        # Verificar que la ruta existe
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/v1/chat/completions' in rules
    
    def test_chat_completions_alternative_endpoint_exists(self):
        """Test: Endpoint /chat/completions debe existir como alternativa"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        app = controller.get_flask_app()
        
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/chat/completions' in rules
    
    def test_models_endpoint_exists(self):
        """Test: Endpoint /models debe existir"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        app = controller.get_flask_app()
        
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/models' in rules
    
    def test_chat_completions_accepts_post_only(self):
        """Test: /v1/chat/completions solo debe aceptar POST"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        app = controller.get_flask_app()
        client = app.test_client()
        
        # GET debe retornar 405 (Method Not Allowed)
        response = client.get('/v1/chat/completions')
        assert response.status_code == 405
    
    def test_models_accepts_get_only(self):
        """Test: /models debe aceptar GET"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        app = controller.get_flask_app()
        client = app.test_client()
        
        # POST debe retornar 405 (Method Not Allowed)
        response = client.post('/models')
        assert response.status_code == 405


class TestProxyControllerRequestValidation:
    """Tests para validación de solicitudes HTTP"""
    
    def test_validate_chat_request_valid_json(self):
        """Test: Solicitud válida debe pasar validación"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        valid_request = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        is_valid, error = controller.validate_chat_request(valid_request)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_chat_request_missing_model(self):
        """Test: Solicitud sin modelo debe fallar"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        invalid_request = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        is_valid, error = controller.validate_chat_request(invalid_request)
        
        assert is_valid is False
        assert error is not None
        assert "model" in error.lower()
    
    def test_validate_chat_request_missing_messages(self):
        """Test: Solicitud sin messages debe fallar"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        invalid_request = {
            "model": "gpt-4o"
        }
        
        is_valid, error = controller.validate_chat_request(invalid_request)
        
        assert is_valid is False
        assert error is not None
        assert "messages" in error.lower()
    
    def test_validate_chat_request_empty_messages(self):
        """Test: messages vacío debe fallar"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        invalid_request = {
            "model": "gpt-4o",
            "messages": []
        }
        
        is_valid, error = controller.validate_chat_request(invalid_request)
        
        assert is_valid is False
        assert error is not None
        assert "messages" in error.lower()
    
    def test_validate_chat_request_none_data(self):
        """Test: Datos None deben fallar validación"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        
        is_valid, error = controller.validate_chat_request(None)
        
        assert is_valid is False
        assert error is not None


class TestProxyControllerRequestForwarding:
    """Tests para reenvío de solicitudes a GitHub Copilot API"""
    
    @patch('src.controllers.proxy_controller.requests.post')
    def test_forward_to_copilot_success(self, mock_post):
        """Test: Reenvío exitoso a la API de Copilot"""
        from src.controllers.proxy_controller import ProxyController
        
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!", "role": "assistant"}}]
        }
        mock_post.return_value = mock_response
        
        controller = ProxyController()
        request_data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}]
        }
        
        response = controller.forward_to_copilot(request_data, token="fake_token")
        
        assert response is not None
        assert response['choices'][0]['message']['content'] == "Hello!"
    
    @patch('src.controllers.proxy_controller.requests.post')
    def test_forward_includes_required_headers(self, mock_post):
        """Test: Verificar que se incluyen headers requeridos"""
        from src.controllers.proxy_controller import ProxyController
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response
        
        controller = ProxyController()
        request_data = {"model": "gpt-4o", "messages": []}
        
        controller.forward_to_copilot(request_data, token="fake_token")
        
        # Verificar que se llamó con los headers correctos
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        
        assert 'authorization' in headers
        assert 'copilot-integration-id' in headers
        assert 'editor-version' in headers
        assert headers['authorization'] == 'Bearer fake_token'
    
    @patch('src.controllers.proxy_controller.requests.post')
    def test_forward_handles_api_error(self, mock_post):
        """Test: Manejar errores de la API correctamente"""
        from src.controllers.proxy_controller import ProxyController
        import requests
        
        # Usar una excepción específica de requests en lugar de Exception genérico
        mock_post.side_effect = requests.RequestException("API Error")
        
        controller = ProxyController()
        request_data = {"model": "gpt-4o", "messages": []}
        
        response = controller.forward_to_copilot(request_data, token="fake_token")
        
        # Debe retornar un error estructurado
        assert 'error' in response or 'choices' in response
    
    @patch('src.controllers.proxy_controller.requests.post')
    def test_forward_uses_correct_api_url(self, mock_post):
        """Test: Verificar que se usa la URL correcta de Copilot"""
        from src.controllers.proxy_controller import ProxyController
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response
        
        controller = ProxyController()
        request_data = {"model": "gpt-4o", "messages": []}
        
        controller.forward_to_copilot(request_data, token="fake_token")
        
        # Verificar URL
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert 'api.githubcopilot.com' in url
        assert 'chat/completions' in url


class TestProxyControllerOpenAICompatibility:
    """Tests para compatibilidad con clientes OpenAI"""
    
    def test_rewrite_model_name_claude(self):
        """Test: Mantener nombre de modelo claude-3.5-sonnet"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        request_data = {"model": "claude-3.5-sonnet"}
        response_data = {"model": "gpt-4o"}
        
        result = controller.rewrite_model_name(request_data, response_data)
        
        assert result['model'] == "claude-3.5-sonnet"
    
    def test_rewrite_model_name_gpt4o(self):
        """Test: Mantener nombre de modelo gpt-4o"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        request_data = {"model": "gpt-4o"}
        response_data = {"model": "some-other-model"}
        
        result = controller.rewrite_model_name(request_data, response_data)
        
        assert result['model'] == "gpt-4o"
    
    def test_disable_streaming_in_request(self):
        """Test: Desactivar streaming si está activo"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        request_data = {
            "model": "gpt-4o",
            "messages": [],
            "stream": True
        }
        
        modified = controller.handle_streaming(request_data)
        
        assert modified['stream'] is False
    
    def test_streaming_already_disabled(self):
        """Test: No modificar si streaming ya está desactivado"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        request_data = {
            "model": "gpt-4o",
            "messages": [],
            "stream": False
        }
        
        modified = controller.handle_streaming(request_data)
        
        assert modified['stream'] is False


class TestProxyControllerMetrics:
    """Tests para métricas del servidor"""
    
    def test_get_metrics_returns_dict(self):
        """Test: get_metrics() debe retornar un diccionario"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        metrics = controller.get_metrics()
        
        assert isinstance(metrics, dict)
    
    def test_metrics_includes_request_count(self):
        """Test: Métricas deben incluir contador de solicitudes"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        metrics = controller.get_metrics()
        
        assert 'total_requests' in metrics
        assert isinstance(metrics['total_requests'], int)
    
    def test_metrics_includes_quota_info(self):
        """Test: Métricas deben incluir información de cuota"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        controller._current_quota = {'chat': 50}
        
        metrics = controller.get_metrics()
        
        assert 'current_quota' in metrics
    
    def test_metrics_includes_account_count(self):
        """Test: Métricas deben incluir número de cuentas"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        # Agregar cuentas al AuthModel con cuota
        auth_model = controller.get_auth_model()
        auth_model.add_account("token_1234567890123456789012345678901234", quota_remaining=100)
        auth_model.add_account("token_2345678901234567890123456789012345", quota_remaining=100)
        auth_model.add_account("token_3456789012345678901234567890123456", quota_remaining=100)
        
        metrics = controller.get_metrics()
        
        assert 'total_accounts' in metrics
        assert metrics['total_accounts'] == 3
    
    def test_increment_request_counter(self):
        """Test: Contador de solicitudes debe incrementar"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        initial_count = controller.get_metrics()['total_requests']
        
        controller.increment_request_counter()
        
        new_count = controller.get_metrics()['total_requests']
        assert new_count == initial_count + 1


class TestProxyControllerResponseFormatting:
    """Tests para formateo de respuestas según especificación OpenAI"""
    
    def test_format_response_keeps_structure(self):
        """Test: Formateo debe mantener estructura OpenAI"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        copilot_response = {
            "choices": [{
                "message": {"role": "assistant", "content": "Hello"}
            }],
            "model": "gpt-4o"
        }
        
        formatted = controller.format_openai_response(copilot_response)
        
        assert 'choices' in formatted
        assert 'model' in formatted
        assert formatted['choices'][0]['message']['role'] == 'assistant'
    
    def test_format_error_response(self):
        """Test: Formatear respuestas de error correctamente"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        error_msg = "Invalid request"
        
        formatted = controller.format_error_response(error_msg)
        
        assert 'error' in formatted
        assert formatted['error']['message'] == error_msg
    
    def test_format_streaming_disabled_message(self):
        """Test: Mensaje para desactivar streaming"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        
        formatted = controller.format_streaming_disabled_response()
        
        assert 'choices' in formatted
        assert 'streaming' in formatted['choices'][0]['message']['content'].lower()


class TestProxyControllerModelIntegration:
    """Tests para integración con ConfigModel, AuthModel y ProxyModel"""
    
    def test_uses_config_model_for_api_url(self):
        """Test: Debe usar ConfigModel para API_URL"""
        from src.controllers.proxy_controller import ProxyController
        from src.models.config_model import API_URL
        
        controller = ProxyController()
        
        # Verificar que usa la constante de ConfigModel
        assert controller.get_api_url() == API_URL
    
    def test_uses_config_model_for_headers(self):
        """Test: Debe usar ConfigModel para headers base"""
        from src.controllers.proxy_controller import ProxyController
        from src.models.config_model import HEADERS_BASE
        
        controller = ProxyController()
        
        # Verificar que los headers coinciden con ConfigModel
        headers = controller.get_headers_base()
        assert headers == HEADERS_BASE
    
    def test_uses_auth_model_for_token(self):
        """Test: Debe obtener token desde AuthModel"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        
        # Agregar cuenta de prueba al AuthModel (token válido de 40 caracteres)
        test_token = "test_token_1234567890123456789012345678"
        controller.get_auth_model().add_account(test_token, quota_remaining=100)
        
        # Obtener token actual
        token = controller.get_current_token()
        
        assert token == test_token
    
    def test_updates_proxy_model_on_request(self):
        """Test: Debe actualizar ProxyModel al procesar solicitud"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        proxy_model = controller.get_proxy_model()
        
        initial_requests = proxy_model.get_total_requests()
        
        # Simular procesamiento de solicitud
        controller.increment_request_counter()
        
        final_requests = proxy_model.get_total_requests()
        
        assert final_requests == initial_requests + 1
    
    def test_rotates_token_when_quota_exhausted(self):
        """Test: Debe rotar al siguiente token cuando la cuota se agota"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        auth_model = controller.get_auth_model()
        
        # Agregar dos cuentas (tokens válidos de 40 caracteres) con cuota
        token1 = "token_1234567890123456789012345678901234"
        token2 = "token_2345678901234567890123456789012345"
        auth_model.add_account(token1, quota_remaining=100)
        auth_model.add_account(token2, quota_remaining=100)
        
        # Agotar primera cuenta
        auth_model.mark_account_as_exhausted(token1)
        
        # Obtener token actual debe devolver la segunda cuenta
        current_token = controller.get_current_token()
        
        assert current_token == token2
    
    def test_returns_error_when_no_tokens_available(self):
        """Test: Debe retornar error cuando no hay tokens disponibles"""
        from src.controllers.proxy_controller import ProxyController
        
        controller = ProxyController()
        
        # No agregar ninguna cuenta
        token = controller.get_current_token()
        
        # Debe retornar None cuando no hay cuentas
        assert token is None
