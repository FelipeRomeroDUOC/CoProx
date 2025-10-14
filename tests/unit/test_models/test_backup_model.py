"""
Tests unitarios para BackupModel - CoProx

Tests siguiendo metodología TDD (Red-Green-Refactor)
"""

from datetime import datetime
from src.models.backup_model import BackupModel


class TestBackupModelInitialization:
    """Tests para inicialización del modelo de backup"""
    
    def test_initialize_backup_model_idle(self):
        """El modelo debe inicializarse en estado idle"""
        model = BackupModel()
        
        assert model.get_operation_type() == 'idle'
        assert abs(model.get_progress() - 0.0) < 0.001
        assert model.get_status() == 'idle'


class TestBackupOperations:
    """Tests para operaciones de backup/restore"""
    
    def test_start_export_operation(self):
        """Debe poder iniciar una operación de exportación"""
        model = BackupModel()
        
        model.start_operation('export')
        
        assert model.get_operation_type() == 'export'
        assert model.get_status() == 'in_progress'
        assert abs(model.get_progress() - 0.0) < 0.001
    
    def test_start_import_operation(self):
        """Debe poder iniciar una operación de importación"""
        model = BackupModel()
        
        model.start_operation('import')
        
        assert model.get_operation_type() == 'import'
        assert model.get_status() == 'in_progress'
        assert abs(model.get_progress() - 0.0) < 0.001
    
    def test_update_operation_progress(self):
        """Debe actualizar el progreso de la operación actual"""
        model = BackupModel()
        model.start_operation('export')
        
        model.update_progress(0.5)
        
        assert abs(model.get_progress() - 0.5) < 0.001
        
        model.update_progress(1.0)
        
        assert abs(model.get_progress() - 1.0) < 0.001
    
    def test_complete_operation_successfully(self):
        """Debe marcar operación como completada exitosamente"""
        model = BackupModel()
        model.start_operation('export')
        model.update_progress(0.5)
        
        model.complete_operation()
        
        assert model.get_status() == 'completed'
        assert model.get_operation_type() == 'idle'
        assert abs(model.get_progress() - 0.0) < 0.001
    
    def test_fail_operation_with_error(self):
        """Debe manejar fallos en operaciones con mensaje de error"""
        model = BackupModel()
        model.start_operation('import')
        
        model.fail_operation('Invalid backup file format')
        
        assert model.get_status() == 'failed'
        assert model.get_last_error() == 'Invalid backup file format'


class TestBackupMetadata:
    """Tests para generación y validación de metadatos"""
    
    def test_generate_backup_metadata(self):
        """Debe generar metadatos correctos para un backup"""
        model = BackupModel()
        account_tokens = ['token1', 'token2', 'token3']
        
        metadata = model.generate_metadata(account_tokens, has_password=False)
        
        assert 'version' in metadata
        assert 'created_at' in metadata
        assert metadata['accounts_count'] == 3
        assert len(metadata['accounts']) == 3
        assert metadata['has_password'] is False
        assert isinstance(metadata['created_at'], datetime)
    
    def test_validate_backup_metadata_valid(self):
        """Debe validar metadatos correctos sin errores"""
        model = BackupModel()
        valid_metadata = {
            'version': '1.0',
            'created_at': datetime.now(),
            'accounts_count': 2,
            'accounts': ['acc1', 'acc2'],
            'has_password': False
        }
        
        is_valid = model.validate_metadata(valid_metadata)
        
        assert is_valid is True
    
    def test_validate_backup_metadata_invalid_structure(self):
        """Debe rechazar metadatos con estructura incorrecta"""
        model = BackupModel()
        invalid_metadata = {
            'version': '1.0',
            # Falta 'created_at'
            'accounts_count': 2,
            'accounts': ['acc1', 'acc2']
        }
        
        is_valid = model.validate_metadata(invalid_metadata)
        
        assert is_valid is False


class TestBackupHistory:
    """Tests para historial de backups"""
    
    def test_add_to_backup_history(self):
        """Debe agregar entrada al historial de backups"""
        model = BackupModel()
        backup_info = {
            'filename': 'backup_2025_10_13.zip',
            'created_at': datetime.now(),
            'accounts_count': 5
        }
        
        model.add_to_history(backup_info)
        
        history = model.get_history()
        assert len(history) == 1
        assert history[0]['filename'] == 'backup_2025_10_13.zip'
    
    def test_get_backup_history(self):
        """Debe retornar historial completo de backups"""
        model = BackupModel()
        
        model.add_to_history({
            'filename': 'backup1.zip',
            'created_at': datetime.now(),
            'accounts_count': 2
        })
        model.add_to_history({
            'filename': 'backup2.zip',
            'created_at': datetime.now(),
            'accounts_count': 3
        })
        
        history = model.get_history()
        
        assert len(history) == 2
        assert history[0]['filename'] == 'backup1.zip'
        assert history[1]['filename'] == 'backup2.zip'
    
    def test_calculate_backup_statistics(self):
        """Debe calcular estadísticas agregadas de backups"""
        model = BackupModel()
        
        model.add_to_history({
            'filename': 'backup1.zip',
            'created_at': datetime.now(),
            'accounts_count': 2
        })
        model.add_to_history({
            'filename': 'backup2.zip',
            'created_at': datetime.now(),
            'accounts_count': 3
        })
        
        stats = model.get_statistics()
        
        assert stats['total_backups'] == 2
        assert stats['total_accounts_backed_up'] == 5
        assert 'last_backup_date' in stats
