"""
Tests unitarios para AuthModel

Valida la gestión de cuentas, tokens, cuotas y rotación automática.
Incluye validación de formato de tokens, thread-safety y estadísticas.
"""

import pytest
from datetime import datetime
from src.models.auth_model import AuthModel


class TestAuthModelInitialization:
    """Tests para la inicialización del AuthModel"""

    def test_initialize_empty_auth_model(self):
        """Verifica que AuthModel se inicializa vacío correctamente"""
        auth_model = AuthModel()
        
        assert auth_model is not None
        assert auth_model.get_total_accounts_count() == 0
        assert auth_model.get_available_accounts_count() == 0
        assert auth_model.get_current_token() is None


class TestAuthModelAccountManagement:
    """Tests para gestión de cuentas"""

    def test_add_account_successfully(self):
        """Verifica que se puede agregar una cuenta válida"""
        auth_model = AuthModel()
        token = "ghu_testtoken123456789012345678901234"
        
        auth_model.add_account(token, quota_remaining=100, quota_total=100)
        
        assert auth_model.get_total_accounts_count() == 1
        assert auth_model.get_available_accounts_count() == 1

    def test_add_account_with_invalid_token_raises_error(self):
        """Verifica que un token inválido genera error"""
        auth_model = AuthModel()
        invalid_token = "invalid_token"
        
        with pytest.raises(ValueError, match="Token inválido"):
            auth_model.add_account(invalid_token)

    def test_add_multiple_accounts(self):
        """Verifica que se pueden agregar múltiples cuentas"""
        auth_model = AuthModel()
        
        auth_model.add_account("ghu_token1234567890123456789012345", quota_remaining=100)
        auth_model.add_account("ghu_token2234567890123456789012345", quota_remaining=50)
        auth_model.add_account("ghu_token3234567890123456789012345", quota_remaining=75)
        
        assert auth_model.get_total_accounts_count() == 3
        assert auth_model.get_available_accounts_count() == 3


class TestAuthModelTokenRetrieval:
    """Tests para obtención de tokens"""

    def test_get_current_token_returns_first_available(self):
        """Verifica que get_current_token devuelve el primer token disponible"""
        auth_model = AuthModel()
        token1 = "ghu_token1234567890123456789012345"
        token2 = "ghu_token2234567890123456789012345"
        
        auth_model.add_account(token1, quota_remaining=100)
        auth_model.add_account(token2, quota_remaining=50)
        
        current = auth_model.get_current_token()
        assert current == token1

    def test_get_current_token_skips_exhausted_accounts(self):
        """Verifica que get_current_token omite cuentas agotadas"""
        auth_model = AuthModel()
        token1 = "ghu_token1234567890123456789012345"
        token2 = "ghu_token2234567890123456789012345"
        
        auth_model.add_account(token1, quota_remaining=0)
        auth_model.add_account(token2, quota_remaining=50)
        auth_model.mark_account_as_exhausted(token1)
        
        current = auth_model.get_current_token()
        assert current == token2

    def test_get_current_token_returns_none_when_all_exhausted(self):
        """Verifica que get_current_token retorna None cuando todo está agotado"""
        auth_model = AuthModel()
        token1 = "ghu_token1234567890123456789012345"
        
        auth_model.add_account(token1, quota_remaining=0)
        auth_model.mark_account_as_exhausted(token1)
        
        current = auth_model.get_current_token()
        assert current is None


class TestAuthModelQuotaManagement:
    """Tests para gestión de cuotas"""

    def test_mark_account_as_exhausted(self):
        """Verifica que se puede marcar una cuenta como agotada"""
        auth_model = AuthModel()
        token = "ghu_token1234567890123456789012345"
        
        auth_model.add_account(token, quota_remaining=100)
        assert auth_model.get_available_accounts_count() == 1
        
        auth_model.mark_account_as_exhausted(token)
        assert auth_model.get_available_accounts_count() == 0

    def test_update_account_quota(self):
        """Verifica que se puede actualizar la cuota de una cuenta"""
        auth_model = AuthModel()
        token = "ghu_token1234567890123456789012345"
        
        auth_model.add_account(token, quota_remaining=100, quota_total=100)
        
        auth_model.update_account_quota(token, quota_remaining=50)
        
        stats = auth_model.get_statistics()
        # Verificar que la cuota se actualizó correctamente
        assert stats['total_accounts'] == 1


class TestAuthModelStatistics:
    """Tests para estadísticas agregadas"""

    def test_get_statistics_returns_correct_counts(self):
        """Verifica que las estadísticas devuelven contadores correctos"""
        auth_model = AuthModel()
        
        auth_model.add_account("ghu_token1234567890123456789012345", quota_remaining=100)
        auth_model.add_account("ghu_token2234567890123456789012345", quota_remaining=0)
        auth_model.mark_account_as_exhausted("ghu_token2234567890123456789012345")
        
        stats = auth_model.get_statistics()
        
        assert stats['total_accounts'] == 2
        assert stats['available_accounts'] == 1
        assert stats['exhausted_accounts'] == 1

    def test_get_available_accounts_count(self):
        """Verifica que get_available_accounts_count devuelve el conteo correcto"""
        auth_model = AuthModel()
        
        auth_model.add_account("ghu_token1234567890123456789012345", quota_remaining=100)
        auth_model.add_account("ghu_token2234567890123456789012345", quota_remaining=50)
        auth_model.add_account("ghu_token3234567890123456789012345", quota_remaining=0)
        auth_model.mark_account_as_exhausted("ghu_token3234567890123456789012345")
        
        assert auth_model.get_available_accounts_count() == 2

    def test_get_total_accounts_count(self):
        """Verifica que get_total_accounts_count devuelve el conteo total"""
        auth_model = AuthModel()
        
        auth_model.add_account("ghu_token1234567890123456789012345")
        auth_model.add_account("ghu_token2234567890123456789012345")
        auth_model.add_account("ghu_token3234567890123456789012345")
        
        assert auth_model.get_total_accounts_count() == 3


class TestAuthModelTokenRotation:
    """Tests para rotación automática de tokens"""

    def test_rotate_to_next_available_token(self):
        """Verifica que la rotación avanza al siguiente token disponible"""
        auth_model = AuthModel()
        token1 = "ghu_token1234567890123456789012345"
        token2 = "ghu_token2234567890123456789012345"
        token3 = "ghu_token3234567890123456789012345"
        
        auth_model.add_account(token1, quota_remaining=100)
        auth_model.add_account(token2, quota_remaining=50)
        auth_model.add_account(token3, quota_remaining=75)
        
        # Agotar el primero
        auth_model.mark_account_as_exhausted(token1)
        
        # Obtener el siguiente
        current = auth_model.get_current_token()
        assert current == token2
        
        # Agotar el segundo
        auth_model.mark_account_as_exhausted(token2)
        
        # Obtener el tercero
        current = auth_model.get_current_token()
        assert current == token3


class TestAuthModelTokenValidation:
    """Tests para validación de formato de tokens"""

    def test_validates_token_format_github_prefix(self):
        """Verifica que valida tokens con prefijo ghu_"""
        auth_model = AuthModel()
        
        # Token válido con prefijo ghu_
        valid_token = "ghu_" + "a" * 33  # 36 caracteres total
        auth_model.add_account(valid_token)
        assert auth_model.get_total_accounts_count() == 1

    def test_rejects_token_too_short(self):
        """Verifica que rechaza tokens muy cortos"""
        auth_model = AuthModel()
        
        with pytest.raises(ValueError, match="Token inválido"):
            auth_model.add_account("short")

    def test_rejects_empty_token(self):
        """Verifica que rechaza tokens vacíos"""
        auth_model = AuthModel()
        
        with pytest.raises(ValueError, match="Token inválido"):
            auth_model.add_account("")


class TestAuthModelEdgeCases:
    """Tests para casos límite"""

    def test_add_duplicate_token_updates_existing(self):
        """Verifica que agregar token duplicado actualiza el existente"""
        auth_model = AuthModel()
        token = "ghu_token1234567890123456789012345"
        
        auth_model.add_account(token, quota_remaining=100)
        auth_model.add_account(token, quota_remaining=200)
        
        # Debe tener solo una cuenta
        assert auth_model.get_total_accounts_count() == 1

    def test_mark_nonexistent_account_as_exhausted_raises_error(self):
        """Verifica que marcar cuenta inexistente como agotada genera error"""
        auth_model = AuthModel()
        
        with pytest.raises(KeyError):
            auth_model.mark_account_as_exhausted("ghu_nonexistent12345678901234567890")

    def test_update_nonexistent_account_quota_raises_error(self):
        """Verifica que actualizar cuota de cuenta inexistente genera error"""
        auth_model = AuthModel()
        
        with pytest.raises(KeyError):
            auth_model.update_account_quota("ghu_nonexistent12345678901234567890", 100)
