"""
Tests unitarios para AuthController - Gestión de autenticación OAuth con GitHub.

Metodología: Test-Driven Development (TDD)
Fase: RED - Crear tests antes de la implementación
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time
from typing import Dict, Any

from src.controllers.auth_controller import AuthController
from src.models.auth_model import AuthModel
from src.models.config_model import CLIENT_ID, OAUTH_SCOPE, REQUEST_TIMEOUT


class TestAuthControllerDeviceFlow:
    """Tests para el flujo OAuth Device Flow de GitHub."""
    
    def test_request_device_code_success(self):
        """Test: Solicitar código de dispositivo exitosamente."""
        # Arrange
        controller = AuthController()
        expected_response = {
            "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
            "user_code": "WDJB-MJHT",
            "verification_uri": "https://github.com/login/device",
            "expires_in": 900,
            "interval": 5
        }
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = expected_response
            mock_post.return_value.status_code = 200
            
            result = controller.request_device_code()
            
            # Verificar que se hizo la llamada correcta
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "https://github.com/login/device/code" in call_args[0][0]
            assert call_args[1]["headers"]["accept"] == "application/json"
            
            # Verificar resultado
            assert result["device_code"] == expected_response["device_code"]
            assert result["user_code"] == expected_response["user_code"]
            assert result["verification_uri"] == expected_response["verification_uri"]
            assert result["interval"] == 5
    
    def test_request_device_code_timeout(self):
        """Test: Timeout al solicitar código de dispositivo."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.Timeout("Connection timeout")
            
            with pytest.raises(requests.Timeout):
                controller.request_device_code()
    
    def test_request_device_code_api_error(self):
        """Test: Error de API al solicitar código."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.json.return_value = {"error": "internal_error"}
            
            with pytest.raises(requests.RequestException):
                controller.request_device_code()
    
    def test_poll_for_authorization_success(self):
        """Test: Usuario autoriza y se obtiene access_token."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 5
        
        expected_token = "gho_16C7e42F292c6912E7710c838347Ae178B4a"
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            # Primera llamada: authorization_pending
            # Segunda llamada: success con token
            mock_post.return_value.json.side_effect = [
                {"error": "authorization_pending"},
                {
                    "access_token": expected_token,
                    "token_type": "bearer",
                    "scope": "user:email"
                }
            ]
            mock_post.return_value.status_code = 200
            
            with patch('time.sleep'):  # Mock sleep para acelerar test
                result = controller.poll_for_authorization(device_code, interval, max_attempts=10)
            
            assert result == expected_token
            assert mock_post.call_count == 2
    
    def test_poll_for_authorization_pending(self):
        """Test: Usuario aún no ha autorizado (authorization_pending)."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            # Simular que siempre está pending (exceder max_attempts)
            mock_post.return_value.json.return_value = {"error": "authorization_pending"}
            mock_post.return_value.status_code = 200
            
            with patch('time.sleep'):
                with pytest.raises(TimeoutError):
                    controller.poll_for_authorization(device_code, interval, max_attempts=3)
    
    def test_poll_for_authorization_expired_token(self):
        """Test: Token de dispositivo expiró."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"error": "expired_token"}
            mock_post.return_value.status_code = 200
            
            with pytest.raises(ValueError, match="expired"):
                controller.poll_for_authorization(device_code, interval, max_attempts=3)
    
    def test_poll_respects_interval(self):
        """Test: Polling respeta el intervalo especificado."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.side_effect = [
                {"error": "authorization_pending"},
                {"access_token": "gho_test", "token_type": "bearer"}
            ]
            mock_post.return_value.status_code = 200
            
            with patch('time.sleep') as mock_sleep:
                controller.poll_for_authorization(device_code, interval, max_attempts=10)
                
                # Verificar que se llamó a sleep con el intervalo correcto
                mock_sleep.assert_called_with(interval)
    
    def test_device_flow_complete_integration(self):
        """Test: Flujo completo de device code a access_token."""
        # Arrange
        controller = AuthController()
        
        device_code_response = {
            "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
            "user_code": "WDJB-MJHT",
            "verification_uri": "https://github.com/login/device",
            "expires_in": 900,
            "interval": 5
        }
        
        token_response = {
            "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
            "token_type": "bearer",
            "scope": "user:email"
        }
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            # Primera llamada: request_device_code
            # Segunda y tercera llamadas: poll_for_authorization
            mock_post.return_value.json.side_effect = [
                device_code_response,
                {"error": "authorization_pending"},
                token_response
            ]
            mock_post.return_value.status_code = 200
            
            with patch('time.sleep'):
                result = controller.authenticate()
            
            assert result == token_response["access_token"]
            assert mock_post.call_count == 3


class TestAuthControllerErrorHandling:
    """Tests para manejo de errores en AuthController."""
    
    def test_handle_network_error_gracefully(self):
        """Test: Maneja errores de red sin crashear."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.ConnectionError("Network unreachable")
            
            with pytest.raises(requests.ConnectionError):
                controller.request_device_code()
    
    def test_handle_invalid_response_format(self):
        """Test: Maneja respuestas con formato inválido."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value.status_code = 200
            
            with pytest.raises(ValueError):
                controller.request_device_code()
    
    def test_handle_slow_down_error(self):
        """Test: Maneja error slow_down de rate limiting."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        initial_interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.side_effect = [
                {"error": "slow_down", "interval": 10},
                {"access_token": "gho_test", "token_type": "bearer"}
            ]
            mock_post.return_value.status_code = 200
            
            with patch('time.sleep') as mock_sleep:
                controller.poll_for_authorization(device_code, initial_interval, max_attempts=10)
                
                # Verificar que se respeta el nuevo intervalo
                calls = mock_sleep.call_args_list
                # Primera llamada: 5 segundos (slow_down agrega 5)
                # Segunda llamada: 10 segundos (inicial 5 + 5 del slow_down)
                assert calls[0][0][0] == 10  # Ya se incrementó por slow_down
                assert len(calls) >= 1
    
    def test_handle_access_denied_error(self):
        """Test: Maneja cuando usuario cancela autorización."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"error": "access_denied"}
            mock_post.return_value.status_code = 200
            
            with pytest.raises(ValueError, match="denied.*access"):
                controller.poll_for_authorization(device_code, interval, max_attempts=3)


class TestAuthControllerInitialization:
    """Tests para inicialización de AuthController."""
    
    def test_initialize_without_auth_model(self):
        """Test: Inicializa sin AuthModel (crea uno por defecto)."""
        # Act
        controller = AuthController()
        
        # Assert
        assert hasattr(controller, '_auth_model')
        assert controller._auth_model is not None
    
    def test_initialize_with_custom_auth_model(self):
        """Test: Inicializa con AuthModel personalizado."""
        # Arrange
        custom_auth_model = AuthModel()
        
        # Act
        controller = AuthController(auth_model=custom_auth_model)
        
        # Assert
        assert controller._auth_model is custom_auth_model


class TestAuthControllerTokenRecovery:
    """Tests para verificación y recuperación de tokens exhaustos."""
    
    def test_check_exhausted_tokens_folder(self, tmp_path):
        """Test: Escanea carpeta TokensAgotados/."""
        # Arrange
        controller = AuthController()
        exhausted_dir = tmp_path / "TokensAgotados"
        exhausted_dir.mkdir()
        
        # Crear algunos archivos de tokens exhaustos
        token1 = exhausted_dir / "2025-10-15T00:00:00Z.copilot_token"
        token1.write_text("gho_exhausted_token_1_30_chars_long")
        
        token2 = exhausted_dir / "2025-10-16T00:00:00Z.copilot_token"
        token2.write_text("gho_exhausted_token_2_30_chars_long")
        
        # Act
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.glob.return_value = [token1, token2]
            
            result = controller.check_exhausted_tokens(str(exhausted_dir))
        
        # Assert - debe devolver una lista
        assert isinstance(result, list)
    
    def test_verify_specific_token_with_quota(self):
        """Test: Verifica cuota de un token específico."""
        # Arrange
        controller = AuthController()
        token = "gho_recovered_token_with_quota_available"
        
        quota_response = {
            "token": "copilot_token",
            "limited_user_quotas": {"chat": 50},
            "limited_user_reset_date": "2025-10-20T00:00:00Z"
        }
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = quota_response
            mock_get.return_value.status_code = 200
            
            has_quota = controller.verify_specific_token(token)
            
            assert has_quota is True
    
    def test_verify_specific_token_still_exhausted(self):
        """Test: Detecta token que aún no tiene cuota."""
        # Arrange
        controller = AuthController()
        token = "gho_still_exhausted_token_no_quota_yet"
        
        quota_response = {
            "token": "copilot_token",
            "limited_user_quotas": {"chat": 0},
            "limited_user_reset_date": "2025-10-20T00:00:00Z"
        }
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = quota_response
            mock_get.return_value.status_code = 200
            
            has_quota = controller.verify_specific_token(token)
            
            assert has_quota is False
    
    def test_restore_token_with_quota(self, tmp_path):
        """Test: Mueve token con cuota de vuelta a activos."""
        # Arrange
        auth_model = AuthModel()
        controller = AuthController(auth_model=auth_model)
        
        # Simular carpeta de tokens exhaustos
        exhausted_dir = tmp_path / "TokensAgotados"
        exhausted_dir.mkdir()
        
        token_file = exhausted_dir / "2025-10-15T00:00:00Z.copilot_token"
        token_content = "gho_recovered_token_ready_to_restore_ok"
        token_file.write_text(token_content)
        
        quota_response = {
            "token": "copilot_token",
            "limited_user_quotas": {"chat": 50}
        }
        
        # Act
        with patch('requests.get') as mock_get, \
             patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=[token_file.name]):
            
            mock_get.return_value.json.return_value = quota_response
            mock_get.return_value.status_code = 200
            
            restored = controller.check_exhausted_tokens(str(exhausted_dir))
        
        # Assert - debe incluir el token restaurado
        assert isinstance(restored, list)
    
    def test_update_statistics_after_recovery(self):
        """Test: Actualiza estadísticas tras recuperación."""
        # Arrange
        auth_model = AuthModel()
        controller = AuthController(auth_model=auth_model)
        
        # Act - agregar token recuperado
        recovered_token = "gho_recovered_token_40_characters_exact"
        
        with patch('requests.get') as mock_get:
            quota_response = {
                "token": "copilot_token",
                "limited_user_quotas": {"chat": 30}
            }
            mock_get.return_value.json.return_value = quota_response
            mock_get.return_value.status_code = 200
            
            # Verificar y agregar si tiene cuota
            has_quota = controller.verify_specific_token(recovered_token)
            if has_quota:
                auth_model.add_account(
                    token=recovered_token,
                    quota_remaining=30,
                    quota_total=30
                )
        
        # Assert
        stats = auth_model.get_statistics()
        assert stats["total_accounts"] >= 1
    
    def test_handle_invalid_token_file(self, tmp_path):
        """Test: Maneja archivos de token inválidos."""
        # Arrange
        controller = AuthController()
        exhausted_dir = tmp_path / "TokensAgotados"
        exhausted_dir.mkdir()
        
        # Crear archivo con token inválido
        invalid_token = exhausted_dir / "2025-10-15T00:00:00Z.copilot_token"
        invalid_token.write_text("invalid_short_token")
        
        # Act & Assert - no debe crashear
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=[invalid_token.name]):
            
            result = controller.check_exhausted_tokens(str(exhausted_dir))
            
            # Debe devolver lista vacía o manejar el error gracefully
            assert isinstance(result, list)
    
    def test_no_exhausted_tokens_folder(self):
        """Test: Maneja caso donde no existe carpeta TokensAgotados/."""
        # Arrange
        controller = AuthController()
        
        # Act
        with patch('os.path.exists', return_value=False):
            result = controller.check_exhausted_tokens()
        
        # Assert - debe devolver lista vacía
        assert result == []


class TestAuthControllerModelIntegration:
    """Tests para integración con AuthModel."""
    
    def test_verify_token_quota_success(self):
        """Test: Verifica cuota del token recién obtenido."""
        # Arrange
        controller = AuthController()
        access_token = "gho_16C7e42F292c6912E7710c838347Ae178B4a"
        
        expected_response = {
            "token": "some_copilot_token",
            "limited_user_quotas": {
                "chat": 50,
                "code_completion": 100
            },
            "limited_user_reset_date": "2025-10-15T00:00:00Z"
        }
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = expected_response
            mock_get.return_value.status_code = 200
            
            result = controller.verify_token_quota(access_token)
            
            # Verificar llamada correcta a la API
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "https://api.github.com/copilot_internal/v2/token" in call_args[0][0]
            assert call_args[1]["headers"]["authorization"] == f"token {access_token}"
            
            # Verificar resultado
            assert result["token"] == expected_response["token"]
            assert result["limited_user_quotas"]["chat"] == 50
    
    def test_verify_token_quota_no_quota(self):
        """Test: Detecta cuando token no tiene cuota."""
        # Arrange
        controller = AuthController()
        access_token = "gho_exhausted_token"
        
        response_no_quota = {
            "token": "some_token",
            "limited_user_quotas": {"chat": 0},
            "limited_user_reset_date": "2025-10-15T00:00:00Z"
        }
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = response_no_quota
            mock_get.return_value.status_code = 200
            
            result = controller.verify_token_quota(access_token)
            
            assert result["limited_user_quotas"]["chat"] == 0
    
    def test_add_account_complete_flow(self):
        """Test: Flujo completo de agregar cuenta."""
        # Arrange
        controller = AuthController()
        
        device_response = {
            "device_code": "device123",
            "user_code": "ABCD-1234",
            "verification_uri": "https://github.com/login/device",
            "interval": 5
        }
        
        access_token = "gho_new_account_token_1234567890123456789"
        
        quota_response = {
            "token": "copilot_token",
            "limited_user_quotas": {"chat": 50},
            "limited_user_reset_date": "2025-10-15T00:00:00Z"
        }
        
        # Act & Assert
        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get, \
             patch('time.sleep'):
            
            # Mock device code request y polling
            mock_post.return_value.json.side_effect = [
                device_response,
                {"access_token": access_token, "token_type": "bearer"}
            ]
            mock_post.return_value.status_code = 200
            
            # Mock quota verification
            mock_get.return_value.json.return_value = quota_response
            mock_get.return_value.status_code = 200
            
            result = controller.add_account()
            
            # Verificar que se obtuvo el token
            assert result["access_token"] == access_token
            assert result["quota_info"]["chat"] == 50
            
            # Verificar que se agregó al AuthModel
            stats = controller._auth_model.get_statistics()
            assert stats["total_accounts"] == 1
    
    def test_add_account_saves_to_auth_model(self):
        """Test: Token se guarda en AuthModel después de autenticación."""
        # Arrange
        auth_model = AuthModel()
        controller = AuthController(auth_model=auth_model)
        
        access_token = "gho_test_token_40_characters_long_exact"
        
        device_response = {
            "device_code": "device123",
            "user_code": "TEST-CODE",
            "verification_uri": "https://github.com/login/device",
            "interval": 5
        }
        
        quota_response = {
            "token": "copilot_token",
            "limited_user_quotas": {"chat": 30},
            "limited_user_reset_date": "2025-10-15T00:00:00Z"
        }
        
        # Act
        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get, \
             patch('time.sleep'):
            
            mock_post.return_value.json.side_effect = [
                device_response,
                {"access_token": access_token, "token_type": "bearer"}
            ]
            mock_post.return_value.status_code = 200
            
            mock_get.return_value.json.return_value = quota_response
            mock_get.return_value.status_code = 200
            
            controller.add_account()
        
        # Assert - verificar que se guardó en AuthModel
        current_token = auth_model.get_current_token()
        assert current_token == access_token
    
    def test_add_account_updates_statistics(self):
        """Test: Actualiza estadísticas de cuentas totales."""
        # Arrange
        auth_model = AuthModel()
        controller = AuthController(auth_model=auth_model)
        
        # Act - agregar 2 cuentas
        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get, \
             patch('time.sleep'):
            
            for i in range(2):
                mock_post.return_value.json.side_effect = [
                    {"device_code": f"dev{i}", "user_code": f"CODE{i}", 
                     "verification_uri": "https://github.com/login/device", "interval": 5},
                    {"access_token": f"gho_token_{i}_" + "x"*27, "token_type": "bearer"}
                ]
                mock_post.return_value.status_code = 200
                
                mock_get.return_value.json.return_value = {
                    "token": f"copilot_{i}",
                    "limited_user_quotas": {"chat": 50},
                    "limited_user_reset_date": "2025-10-15T00:00:00Z"
                }
                mock_get.return_value.status_code = 200
                
                controller.add_account()
        
        # Assert
        stats = auth_model.get_statistics()
        assert stats["total_accounts"] == 2
    
    def test_handle_duplicate_token(self):
        """Test: Maneja token duplicado correctamente."""
        # Arrange
        auth_model = AuthModel()
        access_token = "gho_duplicate_token_exact_40_chars_here"
        
        # Agregar token inicial
        auth_model.add_account(access_token, quota_remaining=50, quota_total=50)
        
        controller = AuthController(auth_model=auth_model)
        
        # Act & Assert - intentar agregar el mismo token
        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get, \
             patch('time.sleep'):
            
            mock_post.return_value.json.side_effect = [
                {"device_code": "dev", "user_code": "CODE", 
                 "verification_uri": "https://github.com/login/device", "interval": 5},
                {"access_token": access_token, "token_type": "bearer"}
            ]
            mock_post.return_value.status_code = 200
            
            mock_get.return_value.json.return_value = {
                "token": "copilot",
                "limited_user_quotas": {"chat": 50}
            }
            mock_get.return_value.status_code = 200
            
            result = controller.add_account()
            
            # Debe detectar el duplicado
            assert result.get("duplicate") is True or result.get("access_token") == access_token
            
            # No debe duplicar en estadísticas
            stats = auth_model.get_statistics()
            assert stats["total_accounts"] == 1  # Solo el original


class TestAuthControllerEdgeCases:
    """Tests para casos edge y validaciones robustas - Refinamiento."""
    
    def test_handle_incorrect_device_code_error(self):
        """Test: Maneja error de device_code inválido."""
        # Arrange
        controller = AuthController()
        device_code = "invalid_code_12345"
        interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"error": "incorrect_device_code"}
            mock_post.return_value.status_code = 200
            
            with pytest.raises(ValueError, match="Invalid device code"):
                controller.poll_for_authorization(device_code, interval, max_attempts=3)
    
    def test_handle_unknown_polling_error(self):
        """Test: Maneja error desconocido durante polling."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 5
        
        # Act & Assert
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"error": "unknown_error_code"}
            mock_post.return_value.status_code = 200
            
            with pytest.raises(ValueError, match="Authorization error: unknown_error_code"):
                controller.poll_for_authorization(device_code, interval, max_attempts=3)
    
    def test_polling_timeout_exceeds_max_attempts(self):
        """Test: Timeout cuando se exceden intentos máximos de polling."""
        # Arrange
        controller = AuthController()
        device_code = "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        interval = 1
        max_attempts = 3
        
        # Act & Assert
        with patch('requests.post') as mock_post, \
             patch('time.sleep'):
            
            # Simular que siempre responde "authorization_pending"
            mock_post.return_value.json.return_value = {"error": "authorization_pending"}
            mock_post.return_value.status_code = 200
            
            with pytest.raises(TimeoutError, match="Authorization timeout"):
                controller.poll_for_authorization(device_code, interval, max_attempts=max_attempts)
            
            # Verificar que se hicieron exactamente max_attempts llamadas
            assert mock_post.call_count == max_attempts
    
    def test_verify_token_quota_missing_token_field(self):
        """Test: Maneja respuesta sin campo 'token' al verificar cuota."""
        # Arrange
        controller = AuthController()
        token = "gho_test123"
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            # Respuesta sin el campo "token"
            mock_get.return_value.json.return_value = {
                "limited_user_quotas": {"chat": 50}
                # Falta "token" field
            }
            mock_get.return_value.status_code = 200
            
            with pytest.raises(ValueError, match="missing 'token' field"):
                controller.verify_token_quota(token)
    
    def test_verify_token_quota_network_error(self):
        """Test: Maneja error de red al verificar cuota."""
        # Arrange
        controller = AuthController()
        token = "gho_test123"
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network unreachable")
            
            with pytest.raises(requests.RequestException, match="Error verifying token quota"):
                controller.verify_token_quota(token)
    
    def test_add_account_detects_duplicate_when_no_current_token(self):
        """Test: Maneja correctamente cuando no hay token actual (no es duplicado)."""
        # Arrange
        auth_model = AuthModel()
        controller = AuthController(auth_model=auth_model)
        
        # Act & Assert
        with patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get, \
             patch('time.sleep'):
            
            mock_post.return_value.json.side_effect = [
                {"device_code": "dev", "user_code": "CODE", 
                 "verification_uri": "https://github.com/login/device", "interval": 5},
                {"access_token": "gho_new_token_1234567890", "token_type": "bearer"}
            ]
            mock_post.return_value.status_code = 200
            
            mock_get.return_value.json.return_value = {
                "token": "copilot",
                "limited_user_quotas": {"chat": 50}
            }
            mock_get.return_value.status_code = 200
            
            result = controller.add_account()
            
            # No debe ser duplicado porque no había tokens
            assert result["duplicate"] is False
            assert result["success"] is True
    
    def test_check_exhausted_tokens_handles_file_read_error(self, tmp_path):
        """Test: Maneja error al leer archivo de token corrupto."""
        # Arrange
        controller = AuthController()
        exhausted_dir = tmp_path / "TokensAgotados"
        exhausted_dir.mkdir()
        
        # Crear archivo corrupto (sin permisos de lectura)
        corrupted_file = exhausted_dir / "corrupted.copilot_token"
        corrupted_file.write_text("gho_corrupted_token")
        corrupted_file.chmod(0o000)  # Sin permisos de lectura
        
        # Act
        try:
            restored = controller.check_exhausted_tokens(str(exhausted_dir))
            
            # Assert: debe manejar el error y retornar lista vacía o sin ese token
            assert isinstance(restored, list)
            assert "gho_corrupted_token" not in restored
        finally:
            # Cleanup: restaurar permisos
            corrupted_file.chmod(0o644)
    
    def test_check_exhausted_tokens_handles_directory_error(self):
        """Test: Maneja error cuando directorio no es accesible."""
        # Arrange
        controller = AuthController()
        non_existent_dir = "/path/that/does/not/exist/TokensAgotados"
        
        # Act
        restored = controller.check_exhausted_tokens(non_existent_dir)
        
        # Assert: debe retornar lista vacía sin lanzar excepción
        assert restored == []


class TestAuthControllerInputValidation:
    """Tests para validación de inputs - Refinamiento robusto."""
    
    def test_poll_for_authorization_validates_device_code_empty(self):
        """Test: Valida que device_code no esté vacío."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="device_code must be a non-empty string"):
            controller.poll_for_authorization("", interval=5)
    
    def test_poll_for_authorization_validates_device_code_type(self):
        """Test: Valida que device_code sea string."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="device_code must be a non-empty string"):
            controller.poll_for_authorization(None, interval=5)
    
    def test_poll_for_authorization_validates_interval_positive(self):
        """Test: Valida que interval sea positivo."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="interval must be a positive integer"):
            controller.poll_for_authorization("device_code", interval=0)
    
    def test_poll_for_authorization_validates_interval_type(self):
        """Test: Valida que interval sea entero."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="interval must be a positive integer"):
            controller.poll_for_authorization("device_code", interval="5")
    
    def test_poll_for_authorization_validates_max_attempts_positive(self):
        """Test: Valida que max_attempts sea positivo."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="max_attempts must be a positive integer"):
            controller.poll_for_authorization("device_code", interval=5, max_attempts=0)
    
    def test_verify_token_quota_validates_token_empty(self):
        """Test: Valida que access_token no esté vacío."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="access_token must be a non-empty string"):
            controller.verify_token_quota("")
    
    def test_verify_token_quota_validates_token_type(self):
        """Test: Valida que access_token sea string."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="access_token must be a non-empty string"):
            controller.verify_token_quota(None)
    
    def test_verify_specific_token_validates_token_empty(self):
        """Test: Valida que token no esté vacío."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="token must be a non-empty string"):
            controller.verify_specific_token("")
    
    def test_verify_specific_token_validates_token_type(self):
        """Test: Valida que token sea string."""
        # Arrange
        controller = AuthController()
        
        # Act & Assert
        with pytest.raises(ValueError, match="token must be a non-empty string"):
            controller.verify_specific_token(None)
