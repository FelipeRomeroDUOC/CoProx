"""
Tests unitarios para ConfigModel

Valida que todas las constantes del sistema estén correctamente definidas,
tipadas con Final, y contengan valores válidos.
"""

import re
from typing import get_type_hints, get_origin
from src.models import config_model


class TestConfigModelConstants:
    """Tests para validar la existencia y tipo de constantes"""

    def test_client_id_exists_and_is_string(self):
        """Verifica que CLIENT_ID existe y es un string válido"""
        assert hasattr(config_model, 'CLIENT_ID')
        assert isinstance(config_model.CLIENT_ID, str)
        assert len(config_model.CLIENT_ID) > 0

    def test_api_url_is_valid_url(self):
        """Verifica que API_URL es una URL válida de HTTPS"""
        assert hasattr(config_model, 'API_URL')
        assert isinstance(config_model.API_URL, str)
        # Validar formato de URL
        url_pattern = r'^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(url_pattern, config_model.API_URL), \
            f"API_URL debe ser una URL HTTPS válida: {config_model.API_URL}"

    def test_headers_base_contains_required_keys(self):
        """Verifica que HEADERS_BASE contiene todos los headers requeridos"""
        assert hasattr(config_model, 'HEADERS_BASE')
        assert isinstance(config_model.HEADERS_BASE, dict)
        
        # Headers obligatorios según proxy_original
        required_keys = [
            "copilot-integration-id",
            "editor-plugin-version",
            "editor-version",
            "user-agent",
            "x-github-api-version"
        ]
        
        for key in required_keys:
            assert key in config_model.HEADERS_BASE, \
                f"HEADERS_BASE debe contener '{key}'"
            assert isinstance(config_model.HEADERS_BASE[key], str)
            assert len(config_model.HEADERS_BASE[key]) > 0

    def test_oauth_scope_is_string(self):
        """Verifica que OAUTH_SCOPE es un string válido"""
        assert hasattr(config_model, 'OAUTH_SCOPE')
        assert isinstance(config_model.OAUTH_SCOPE, str)
        assert len(config_model.OAUTH_SCOPE) > 0

    def test_token_directory_is_valid_path(self):
        """Verifica que TOKEN_DIRECTORY es una ruta válida"""
        assert hasattr(config_model, 'TOKEN_DIRECTORY')
        assert isinstance(config_model.TOKEN_DIRECTORY, str)
        assert len(config_model.TOKEN_DIRECTORY) > 0

    def test_default_host_is_valid_ip_or_hostname(self):
        """Verifica que DEFAULT_HOST es una IP o hostname válido"""
        assert hasattr(config_model, 'DEFAULT_HOST')
        assert isinstance(config_model.DEFAULT_HOST, str)
        # Validar que es 0.0.0.0 o localhost o una IP válida
        valid_hosts = ['0.0.0.0', 'localhost', '127.0.0.1']
        assert config_model.DEFAULT_HOST in valid_hosts or \
               re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', config_model.DEFAULT_HOST)

    def test_default_port_is_valid_port_number(self):
        """Verifica que DEFAULT_PORT es un puerto válido (1-65535)"""
        assert hasattr(config_model, 'DEFAULT_PORT')
        assert isinstance(config_model.DEFAULT_PORT, int)
        assert 1 <= config_model.DEFAULT_PORT <= 65535

    def test_request_timeout_is_positive_integer(self):
        """Verifica que REQUEST_TIMEOUT es un entero positivo"""
        assert hasattr(config_model, 'REQUEST_TIMEOUT')
        assert isinstance(config_model.REQUEST_TIMEOUT, int)
        assert config_model.REQUEST_TIMEOUT > 0

    def test_constants_are_immutable(self):
        """Verifica que las constantes críticas están tipadas con Final"""
        # Obtener anotaciones del módulo
        annotations = config_model.__annotations__ if hasattr(config_model, '__annotations__') else {}
        
        # Constantes críticas que deben ser Final
        critical_constants = [
            'CLIENT_ID',
            'API_URL',
            'OAUTH_SCOPE',
            'DEFAULT_HOST',
            'DEFAULT_PORT',
            'REQUEST_TIMEOUT'
        ]
        
        for const in critical_constants:
            assert const in annotations, \
                f"{const} debe tener anotación de tipo"
            # Verificar que usa Final (el string de la anotación contiene 'Final')
            annotation_str = str(annotations[const])
            assert 'Final' in annotation_str, \
                f"{const} debe estar tipado con typing.Final"


class TestConfigModelAdditionalConstants:
    """Tests para constantes adicionales del proxy_original"""

    def test_content_type_json_is_string(self):
        """Verifica que CONTENT_TYPE_JSON es un string válido"""
        assert hasattr(config_model, 'CONTENT_TYPE_JSON')
        assert isinstance(config_model.CONTENT_TYPE_JSON, str)
        assert config_model.CONTENT_TYPE_JSON == "application/json"

    def test_token_file_prefix_is_valid_filename(self):
        """Verifica que TOKEN_FILE_PREFIX es un nombre de archivo válido"""
        assert hasattr(config_model, 'TOKEN_FILE_PREFIX')
        assert isinstance(config_model.TOKEN_FILE_PREFIX, str)
        assert len(config_model.TOKEN_FILE_PREFIX) > 0
        # No debe contener caracteres inválidos en nombres de archivo
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            assert char not in config_model.TOKEN_FILE_PREFIX

    def test_token_file_extension_is_valid_extension(self):
        """Verifica que TOKEN_FILE_EXTENSION es una extensión válida"""
        assert hasattr(config_model, 'TOKEN_FILE_EXTENSION')
        assert isinstance(config_model.TOKEN_FILE_EXTENSION, str)
        assert len(config_model.TOKEN_FILE_EXTENSION) > 0

    def test_tokens_exhausted_dir_is_valid_path(self):
        """Verifica que TOKENS_EXHAUSTED_DIR es una ruta de directorio válida"""
        assert hasattr(config_model, 'TOKENS_EXHAUSTED_DIR')
        assert isinstance(config_model.TOKENS_EXHAUSTED_DIR, str)
        assert len(config_model.TOKENS_EXHAUSTED_DIR) > 0


class TestConfigModelValues:
    """Tests para validar los valores específicos de las constantes"""

    def test_client_id_matches_original(self):
        """Verifica que CLIENT_ID coincide con el valor del proxy_original"""
        assert config_model.CLIENT_ID == "01ab8ac9400c4e429b23"

    def test_api_url_matches_original(self):
        """Verifica que API_URL coincide con el valor del proxy_original"""
        assert config_model.API_URL == "https://api.githubcopilot.com"

    def test_oauth_scope_matches_original(self):
        """Verifica que OAUTH_SCOPE coincide con el valor del proxy_original"""
        assert config_model.OAUTH_SCOPE == "user:email"

    def test_default_host_is_all_interfaces(self):
        """Verifica que DEFAULT_HOST está configurado para todas las interfaces"""
        assert config_model.DEFAULT_HOST == "0.0.0.0"

    def test_default_port_is_5000(self):
        """Verifica que DEFAULT_PORT es 5000"""
        assert config_model.DEFAULT_PORT == 5000

    def test_request_timeout_is_30_seconds(self):
        """Verifica que REQUEST_TIMEOUT es 30 segundos"""
        assert config_model.REQUEST_TIMEOUT == 30

    def test_headers_base_values_match_original(self):
        """Verifica que los valores de HEADERS_BASE coinciden con el original"""
        expected_headers = {
            "copilot-integration-id": "vscode-chat",
            "editor-plugin-version": "copilot-chat/0.23.2",
            "editor-version": "vscode/1.96.3",
            "user-agent": "GitHubCopilotChat/0.23.2",
            "x-github-api-version": "2024-12-15"
        }
        
        assert config_model.HEADERS_BASE == expected_headers
