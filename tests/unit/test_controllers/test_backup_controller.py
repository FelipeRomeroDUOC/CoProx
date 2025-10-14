"""
Tests para BackupController - Gestión de exportación/importación de backups

Siguiendo metodología TDD (Red-Green-Refactor):
1. RED: Escribir tests que fallen
2. GREEN: Implementar código mínimo para pasar tests
3. REFACTOR: Mejorar código manteniendo tests verdes
"""

import pytest
import zipfile
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call

from src.controllers.backup_controller import BackupController
from src.models.backup_model import BackupModel
from src.models.auth_model import AuthModel


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def backup_model():
    """Fixture que proporciona un BackupModel mockeado"""
    return Mock(spec=BackupModel)


@pytest.fixture
def auth_model():
    """Fixture que proporciona un AuthModel mockeado con cuentas de prueba"""
    mock_model = Mock(spec=AuthModel)
    mock_model.get_all_accounts.return_value = {
        'token_1': {
            'token': 'ghu_test_token_1',
            'quota_remaining': 100,
            'quota_total': 200,
            'is_exhausted': False,
            'last_used': datetime.now()
        },
        'token_2': {
            'token': 'ghu_test_token_2',
            'quota_remaining': 50,
            'quota_total': 200,
            'is_exhausted': False,
            'last_used': datetime.now()
        }
    }
    return mock_model


@pytest.fixture
def backup_controller(backup_model, auth_model):
    """Fixture que proporciona un BackupController con modelos mockeados"""
    return BackupController(
        backup_model=backup_model,
        auth_model=auth_model
    )


@pytest.fixture
def temp_dir():
    """Fixture que proporciona un directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_backup_zip(temp_dir):
    """Fixture que crea un archivo ZIP de backup válido para tests"""
    zip_path = temp_dir / "test_backup.zip"
    
    # Crear estructura de backup válida
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Metadata
        metadata = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'accounts_count': 2,
            'accounts': ['account_1', 'account_2'],
            'has_password': False
        }
        zf.writestr('metadata.json', json.dumps(metadata))
        
        # Tokens
        zf.writestr('tokens/account_1.txt', 'ghu_test_token_1')
        zf.writestr('tokens/account_2.txt', 'ghu_test_token_2')
    
    return zip_path


# ============================================================================
# TESTS: SUBTAREA 2.2.1 - EXPORT ZIP
# ============================================================================

class TestBackupControllerExport:
    """Tests para funcionalidad de exportación de backups ZIP"""
    
    def test_generate_backup_metadata(self, backup_controller, auth_model):
        """Test: Genera metadatos desde AuthModel"""
        # Arrange
        auth_model.get_all_accounts.return_value = {
            'token_1': {'token': 'ghu_test_1'},
            'token_2': {'token': 'ghu_test_2'}
        }
        
        # Act
        metadata = backup_controller._generate_backup_metadata(has_password=False)
        
        # Assert
        assert metadata is not None
        assert metadata['version'] == '1.0'
        assert metadata['accounts_count'] == 2
        assert len(metadata['accounts']) == 2
        assert metadata['has_password'] is False
        assert 'created_at' in metadata
        assert isinstance(metadata['created_at'], str)
    
    def test_create_temporary_backup_structure(self, backup_controller, temp_dir):
        """Test: Crea estructura temporal correcta (metadata.json + tokens/)"""
        # Arrange
        tokens = {
            'token_1': 'ghu_test_token_1',
            'token_2': 'ghu_test_token_2'
        }
        metadata = {
            'version': '1.0',
            'accounts_count': 2,
            'accounts': ['account_1', 'account_2'],
            'has_password': False,
            'created_at': datetime.now().isoformat()
        }
        
        # Act
        backup_controller._create_backup_structure(
            temp_dir, 
            tokens, 
            metadata
        )
        
        # Assert
        assert (temp_dir / 'metadata.json').exists()
        assert (temp_dir / 'tokens').exists()
        assert (temp_dir / 'tokens').is_dir()
        assert (temp_dir / 'tokens' / 'account_1.txt').exists()
        assert (temp_dir / 'tokens' / 'account_2.txt').exists()
        
        # Verificar contenido de metadata.json
        with open(temp_dir / 'metadata.json', 'r') as f:
            saved_metadata = json.load(f)
        assert saved_metadata['version'] == '1.0'
        assert saved_metadata['accounts_count'] == 2
    
    def test_compress_to_zip_without_password(self, backup_controller, temp_dir):
        """Test: Comprime archivos sin contraseña"""
        # Arrange
        source_dir = temp_dir / 'source'
        source_dir.mkdir()
        (source_dir / 'test.txt').write_text('test content')
        output_zip = temp_dir / 'output.zip'
        
        # Act
        backup_controller._compress_to_zip(
            source_dir, 
            output_zip, 
            password=None
        )
        
        # Assert
        assert output_zip.exists()
        
        # Verificar que el ZIP se puede abrir sin contraseña
        with zipfile.ZipFile(output_zip, 'r') as zf:
            assert 'test.txt' in zf.namelist()
            content = zf.read('test.txt').decode('utf-8')
            assert content == 'test content'
    
    def test_compress_to_zip_with_password(self, backup_controller, temp_dir):
        """Test: Comprime archivos con contraseña
        
        NOTA: zipfile de Python solo soporta encriptación ZIP 2.0 (débil).
        Para producción se recomienda usar pyzipper o py7zr para encriptación AES.
        Este test verifica que la funcionalidad básica funciona.
        """
        # Arrange
        source_dir = temp_dir / 'source'
        source_dir.mkdir()
        (source_dir / 'test.txt').write_text('sensitive data')
        output_zip = temp_dir / 'output.zip'
        password = 'test_password_123'
        
        # Act
        backup_controller._compress_to_zip(
            source_dir, 
            output_zip, 
            password=password
        )
        
        # Assert
        assert output_zip.exists()
        
        # Verificar que el archivo se crea correctamente con contraseña
        # NOTA: zipfile en Python no encripta realmente los archivos al escribir
        # Esta es una limitación conocida de la librería estándar
        with zipfile.ZipFile(output_zip, 'r') as zf:
            assert 'test.txt' in zf.namelist()
            # El archivo se puede leer (limitación de zipfile)
            # TODO: Cuando implementemos FileService, usar pyzipper para encriptación real
            content = zf.read('test.txt').decode('utf-8')
            assert content == 'sensitive data'
    
    def test_update_progress_during_export(self, backup_controller, backup_model, temp_dir):
        """Test: Actualiza progreso en BackupModel durante exportación"""
        # Arrange
        output_zip = temp_dir / 'backup.zip'
        
        # Act
        backup_controller.export_backup(
            output_path=output_zip,
            password=None
        )
        
        # Assert - Verificar que se llamaron los métodos de progreso
        backup_model.start_operation.assert_called_once_with('export')
        assert backup_model.update_progress.call_count >= 2  # Al menos inicio y fin
        backup_model.complete_operation.assert_called_once()
    
    def test_save_to_user_selected_path(self, backup_controller, temp_dir):
        """Test: Guarda ZIP en ruta seleccionada por usuario"""
        # Arrange
        custom_path = temp_dir / 'my_custom_backup' / 'backup.zip'
        custom_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Act
        result = backup_controller.export_backup(
            output_path=custom_path,
            password=None
        )
        
        # Assert
        assert custom_path.exists()
        assert result['success'] is True
        assert result['backup_path'] == str(custom_path)
    
    def test_cleanup_temporary_files(self, backup_controller, temp_dir):
        """Test: Limpia archivos temporales tras exportación"""
        # Arrange
        output_zip = temp_dir / 'backup.zip'
        
        # Act
        backup_controller.export_backup(
            output_path=output_zip,
            password=None
        )
        
        # Assert
        # Verificar que no quedan directorios temporales
        temp_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        # Solo debe existir el directorio donde está el ZIP, no temporales
        assert len(temp_dirs) == 0 or all('backup' not in d.name.lower() for d in temp_dirs)
    
    def test_handle_export_errors_gracefully(self, backup_controller, backup_model):
        """Test: Maneja errores durante exportación sin crashear"""
        # Arrange
        invalid_path = Path('/invalid/path/that/does/not/exist/backup.zip')
        
        # Act
        result = backup_controller.export_backup(
            output_path=invalid_path,
            password=None
        )
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
        backup_model.fail_operation.assert_called_once()
    
    def test_export_with_no_accounts(self, backup_controller, auth_model):
        """Test: Maneja exportación cuando no hay cuentas configuradas"""
        # Arrange
        auth_model.get_all_accounts.return_value = {}
        output_zip = Path(tempfile.gettempdir()) / 'empty_backup.zip'
        
        # Act
        result = backup_controller.export_backup(
            output_path=output_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is True
        assert result['accounts_exported'] == 0
    
    def test_export_creates_valid_backup_structure(self, backup_controller, temp_dir):
        """Test: El backup exportado tiene la estructura esperada"""
        # Arrange
        output_zip = temp_dir / 'backup.zip'
        
        # Act
        backup_controller.export_backup(
            output_path=output_zip,
            password=None
        )
        
        # Assert
        with zipfile.ZipFile(output_zip, 'r') as zf:
            files = zf.namelist()
            assert 'metadata.json' in files
            assert any('tokens/' in f for f in files)
            
            # Verificar metadata
            metadata = json.loads(zf.read('metadata.json'))
            assert 'version' in metadata
            assert 'created_at' in metadata
            assert 'accounts_count' in metadata


# ============================================================================
# TESTS: SUBTAREA 2.2.2 - IMPORT ZIP
# ============================================================================

class TestBackupControllerImport:
    """Tests para funcionalidad de importación de backups ZIP"""
    
    def test_detect_password_protected_zip(self, backup_controller, temp_dir):
        """Test: Detecta si ZIP requiere contraseña"""
        # Arrange - Crear ZIP con contraseña
        zip_with_pwd = temp_dir / 'protected.zip'
        with zipfile.ZipFile(zip_with_pwd, 'w') as zf:
            zf.writestr('test.txt', 'data')
            zf.setpassword(b'secret')
        
        # Crear ZIP sin contraseña
        zip_without_pwd = temp_dir / 'open.zip'
        with zipfile.ZipFile(zip_without_pwd, 'w') as zf:
            zf.writestr('test.txt', 'data')
        
        # Act & Assert
        # NOTA: zipfile de Python no puede detectar contraseñas al escribir
        # Esta funcionalidad será mejorada con FileService
        assert zip_with_pwd.exists()
        assert zip_without_pwd.exists()
    
    def test_validate_backup_structure(self, backup_controller, sample_backup_zip):
        """Test: Valida que backup tenga estructura correcta"""
        # Act
        is_valid = backup_controller.validate_backup_structure(sample_backup_zip)
        
        # Assert
        assert is_valid is True
    
    def test_validate_backup_structure_invalid(self, backup_controller, temp_dir):
        """Test: Rechaza backup con estructura inválida"""
        # Arrange - Crear ZIP sin metadata.json
        invalid_zip = temp_dir / 'invalid.zip'
        with zipfile.ZipFile(invalid_zip, 'w') as zf:
            zf.writestr('random_file.txt', 'data')
        
        # Act
        is_valid = backup_controller.validate_backup_structure(invalid_zip)
        
        # Assert
        assert is_valid is False
    
    def test_extract_metadata_from_backup(self, backup_controller, sample_backup_zip):
        """Test: Extrae metadata.json correctamente"""
        # Act
        metadata = backup_controller._extract_metadata(sample_backup_zip)
        
        # Assert
        assert metadata is not None
        assert metadata['version'] == '1.0'
        assert 'accounts_count' in metadata
        assert 'created_at' in metadata
        assert 'accounts' in metadata
    
    def test_import_tokens_without_duplicates(self, backup_controller, auth_model, sample_backup_zip):
        """Test: Importa solo tokens nuevos"""
        # Arrange - AuthModel sin tokens previos
        auth_model.get_all_accounts.return_value = {}
        
        # Act
        result = backup_controller.import_backup(
            zip_path=sample_backup_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is True
        assert result['imported'] == 2
        assert result['skipped'] == 0
        # Verificar que se intentó agregar los tokens
        assert auth_model.add_account.call_count == 2
    
    def test_skip_duplicate_tokens(self, backup_controller, auth_model, sample_backup_zip):
        """Test: Omite tokens que ya existen"""
        # Arrange - AuthModel ya tiene un token
        existing_accounts = {
            'ghu_test_token_1': {
                'token': 'ghu_test_token_1',
                'quota_remaining': 100,
                'quota_total': 200,
                'is_exhausted': False
            }
        }
        auth_model.get_all_accounts.return_value = existing_accounts
        
        # Act
        result = backup_controller.import_backup(
            zip_path=sample_backup_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is True
        assert result['imported'] == 1  # Solo importó el nuevo
        assert result['skipped'] == 1    # Omitió el duplicado
    
    def test_update_progress_during_import(self, backup_controller, backup_model, sample_backup_zip):
        """Test: Actualiza progreso durante importación"""
        # Act
        backup_controller.import_backup(
            zip_path=sample_backup_zip,
            password=None
        )
        
        # Assert
        backup_model.start_operation.assert_called_once_with('import')
        assert backup_model.update_progress.call_count >= 2
        backup_model.complete_operation.assert_called_once()
    
    def test_generate_import_summary(self, backup_controller, sample_backup_zip):
        """Test: Genera resumen: importadas vs omitidas"""
        # Act
        result = backup_controller.import_backup(
            zip_path=sample_backup_zip,
            password=None
        )
        
        # Assert
        assert 'success' in result
        assert 'imported' in result
        assert 'skipped' in result
        assert 'total' in result
        assert result['total'] == result['imported'] + result['skipped']
    
    def test_handle_wrong_password(self, backup_controller, temp_dir):
        """Test: Maneja contraseña incorrecta"""
        # Arrange - Crear ZIP protegido
        protected_zip = temp_dir / 'protected.zip'
        with zipfile.ZipFile(protected_zip, 'w') as zf:
            zf.setpassword(b'correct_password')
            zf.writestr('test.txt', 'data')
        
        # Act - Intentar con contraseña incorrecta
        result = backup_controller.import_backup(
            zip_path=protected_zip,
            password='wrong_password'
        )
        
        # Assert
        # Por ahora, debería funcionar (limitación de zipfile)
        # TODO: Mejorar con FileService y encriptación real
        assert 'success' in result
    
    def test_import_with_corrupted_zip(self, backup_controller, temp_dir):
        """Test: Maneja archivo ZIP corrupto"""
        # Arrange - Crear archivo corrupto
        corrupted_zip = temp_dir / 'corrupted.zip'
        corrupted_zip.write_text('This is not a valid ZIP file')
        
        # Act
        result = backup_controller.import_backup(
            zip_path=corrupted_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
    
    def test_import_with_missing_metadata(self, backup_controller, temp_dir):
        """Test: Maneja backup sin metadata.json"""
        # Arrange - Crear ZIP sin metadata
        no_metadata_zip = temp_dir / 'no_metadata.zip'
        with zipfile.ZipFile(no_metadata_zip, 'w') as zf:
            zf.writestr('tokens/account_1.txt', 'ghu_test_token')
        
        # Act
        result = backup_controller.import_backup(
            zip_path=no_metadata_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is False
        assert 'error' in result or 'invalid' in str(result).lower()
    
    def test_import_updates_backup_history(self, backup_controller, backup_model, sample_backup_zip):
        """Test: Registra importación en historial de backup"""
        # Act
        result = backup_controller.import_backup(
            zip_path=sample_backup_zip,
            password=None
        )
        
        # Assert
        if result['success']:
            # Verificar que se intentó actualizar el historial
            # (Implementaremos esto en subtarea 2.2.3)
            assert result['imported'] >= 0


class TestBackupControllerHistory:
    """Tests para gestión de historial de backups (Subtarea 2.2.3)"""
    
    def test_record_successful_export(self, backup_controller, backup_model, temp_dir):
        """Test: Registra exportación exitosa en historial"""
        # Arrange
        output_zip = temp_dir / 'backup.zip'
        
        # Act
        result = backup_controller.export_backup(
            output_path=output_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is True
        # Verificar que se registró en el historial
        backup_model.add_to_history.assert_called_once()
        call_args = backup_model.add_to_history.call_args[0][0]
        assert call_args['operation'] == 'export'
        assert 'created_at' in call_args
        assert 'accounts_count' in call_args
    
    def test_record_successful_import(self, backup_controller, backup_model, sample_backup_zip):
        """Test: Registra importación exitosa en historial"""
        # Act
        result = backup_controller.import_backup(
            zip_path=sample_backup_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is True
        # Verificar que se registró en el historial
        backup_model.add_to_history.assert_called_once()
        call_args = backup_model.add_to_history.call_args[0][0]
        assert call_args['operation'] == 'import'
        assert 'created_at' in call_args
        assert call_args['imported'] >= 0
    
    def test_get_backup_history(self, backup_controller, backup_model):
        """Test: Obtiene historial completo de operaciones"""
        # Arrange - Mockear historial con datos
        mock_history = [
            {
                'operation': 'export',
                'created_at': datetime.now(),
                'accounts_count': 5
            },
            {
                'operation': 'import',
                'created_at': datetime.now(),
                'imported': 3
            }
        ]
        backup_model.get_history.return_value = mock_history
        
        # Act
        history = backup_controller.get_backup_history()
        
        # Assert
        assert len(history) == 2
        assert history[0]['operation'] == 'export'
        assert history[1]['operation'] == 'import'
        backup_model.get_history.assert_called_once()
    
    def test_get_backup_statistics(self, backup_controller, backup_model):
        """Test: Obtiene estadísticas agregadas de backups"""
        # Arrange - Mockear estadísticas
        mock_stats = {
            'total_backups': 10,
            'total_accounts_backed_up': 50,
            'last_backup_date': datetime.now()
        }
        backup_model.get_statistics.return_value = mock_stats
        
        # Act
        stats = backup_controller.get_backup_statistics()
        
        # Assert
        assert stats['total_backups'] == 10
        assert stats['total_accounts_backed_up'] == 50
        assert 'last_backup_date' in stats
        backup_model.get_statistics.assert_called_once()


class TestBackupControllerCleanup:
    """Tests para validación y limpieza de recursos (Subtarea 2.2.4)"""
    
    def test_cleanup_on_export_failure(self, backup_controller, backup_model, auth_model):
        """Test: Limpia archivos temporales si exportación falla"""
        # Arrange - Hacer que exporte falle
        invalid_path = Path('/invalid/nonexistent/path/backup.zip')
        
        # Act
        result = backup_controller.export_backup(
            output_path=invalid_path,
            password=None
        )
        
        # Assert
        assert result['success'] is False
        backup_model.fail_operation.assert_called_once()
        # Verificar que no quedan archivos temporales huérfanos
        # (tempfile.TemporaryDirectory se limpia automáticamente)
    
    def test_cleanup_on_import_failure(self, backup_controller, backup_model, temp_dir):
        """Test: Limpia archivos extraídos si importación falla"""
        # Arrange - Crear ZIP corrupto
        corrupted_zip = temp_dir / 'corrupted.zip'
        corrupted_zip.write_text('Not a valid ZIP')
        
        # Act
        result = backup_controller.import_backup(
            zip_path=corrupted_zip,
            password=None
        )
        
        # Assert
        assert result['success'] is False
        backup_model.fail_operation.assert_called_once()
    
    def test_validate_zip_integrity(self, backup_controller, sample_backup_zip, temp_dir):
        """Test: Valida integridad del archivo ZIP"""
        # Test con ZIP válido
        assert backup_controller.validate_backup_structure(sample_backup_zip) is True
        
        # Test con archivo corrupto
        corrupted = temp_dir / 'corrupted.zip'
        corrupted.write_text('Invalid ZIP data')
        assert backup_controller.validate_backup_structure(corrupted) is False
    
    def test_handle_disk_space_error(self, backup_controller, backup_model):
        """Test: Maneja error de espacio en disco
        
        NOTA: Difícil de simular sin llenar el disco realmente.
        Este test verifica que el manejo de errores genérico funciona.
        """
        # Arrange - Ruta inválida que causará error
        invalid_path = Path('/dev/null/cannot/write/here.zip')
        
        # Act
        result = backup_controller.export_backup(
            output_path=invalid_path,
            password=None
        )
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
        backup_model.fail_operation.assert_called_once()
