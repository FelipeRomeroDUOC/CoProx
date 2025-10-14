"""
Modelo de Backup - CoProx

PROPÓSITO:
Este módulo gestiona el estado y metadatos del sistema de backup y restauración.
Mantiene información sobre backups creados, importaciones y operaciones en progreso.

FUNCIONAMIENTO:
- Almacena metadatos de backups exportados e importados
- Rastrea el progreso de operaciones de backup/restore
- Mantiene historial de operaciones realizadas
- Valida integridad de archivos de backup

PARÁMETROS DE ENTRADA:
- backup_metadata: Diccionario con información del backup (fecha, cuentas incluidas)
- export_progress: Float entre 0-1 indicando progreso de exportación
- import_progress: Float entre 0-1 indicando progreso de importación
- backup_history: Lista de backups creados anteriormente
- validation_results: Diccionario con resultados de validación de archivos

SALIDA ESPERADA:
- current_operation: String indicando operación actual (export/import/idle)
- operation_progress: Float con progreso de la operación actual
- backup_list: Lista de backups disponibles para importar
- last_backup_info: Diccionario con información del último backup creado
- validation_status: String indicando estado de validación

PROCESAMIENTO DE DATOS:
- Genera metadatos automáticamente durante exportación
- Valida estructura y contenido de archivos ZIP
- Calcula estadísticas de cuentas incluidas en backup
- Detecta duplicados durante importación

INTERACCIONES CON OTROS MÓDULOS:
- Actualizado por: backup_controller.py (operaciones de backup)
- Leído por: backup_view.py (mostrar progreso y estado)
- Consultado por: file_service.py (validación de archivos)
- Usado por: auth_controller.py (importar tokens)

INTERACCIONES CON MAIN:
- main.py puede inicializar con estado de backup previo
- Se actualiza durante operaciones de export/import
- Proporciona información para mostrar en la interfaz
"""

import threading
from typing import Optional
from datetime import datetime


class BackupModel:
    """
    Modelo de backup thread-safe para gestión de metadatos y operaciones.
    
    Mantiene el estado de operaciones de backup/restore, genera metadatos,
    valida estructura de archivos y mantiene historial de backups.
    """
    
    # Versión del formato de backup
    BACKUP_VERSION = "1.0"
    
    def __init__(self):
        """Inicializa el modelo de backup en estado idle"""
        self._operation_type = 'idle'
        self._operation_status = 'idle'
        self._progress = 0.0
        self._last_error: Optional[str] = None
        self._backup_history: list = []
        self._lock = threading.Lock()
    
    def start_operation(self, operation_type: str) -> None:
        """
        Inicia una operación de backup o importación.
        
        Args:
            operation_type: Tipo de operación ('export' o 'import')
        """
        with self._lock:
            self._operation_type = operation_type
            self._operation_status = 'in_progress'
            self._progress = 0.0
            self._last_error = None
    
    def update_progress(self, progress: float) -> None:
        """
        Actualiza el progreso de la operación actual.
        
        Args:
            progress: Valor entre 0.0 y 1.0 indicando progreso
        """
        with self._lock:
            self._progress = max(0.0, min(1.0, progress))
    
    def complete_operation(self) -> None:
        """Marca la operación actual como completada exitosamente"""
        with self._lock:
            self._operation_status = 'completed'
            self._operation_type = 'idle'
            self._progress = 0.0
            self._last_error = None
    
    def fail_operation(self, error_message: str) -> None:
        """
        Marca la operación actual como fallida con mensaje de error.
        
        Args:
            error_message: Descripción del error ocurrido
        """
        with self._lock:
            self._operation_status = 'failed'
            self._last_error = error_message
    
    def get_operation_type(self) -> str:
        """
        Obtiene el tipo de operación actual.
        
        Returns:
            Tipo de operación: 'export', 'import', o 'idle'
        """
        with self._lock:
            return self._operation_type
    
    def get_status(self) -> str:
        """
        Obtiene el estado de la operación actual.
        
        Returns:
            Estado: 'idle', 'in_progress', 'completed', o 'failed'
        """
        with self._lock:
            return self._operation_status
    
    def get_progress(self) -> float:
        """
        Obtiene el progreso de la operación actual.
        
        Returns:
            Valor entre 0.0 y 1.0 indicando progreso
        """
        with self._lock:
            return self._progress
    
    def get_last_error(self) -> Optional[str]:
        """
        Obtiene el mensaje del último error ocurrido.
        
        Returns:
            Mensaje de error o None si no hay errores
        """
        with self._lock:
            return self._last_error
    
    def generate_metadata(
        self, 
        account_tokens: list[str], 
        has_password: bool = False
    ) -> dict:
        """
        Genera metadatos para un backup.
        
        Args:
            account_tokens: Lista de tokens de cuentas a incluir
            has_password: Si el backup está protegido con contraseña
            
        Returns:
            Diccionario con metadatos del backup
        """
        return {
            'version': self.BACKUP_VERSION,
            'created_at': datetime.now(),
            'accounts_count': len(account_tokens),
            'accounts': [f'account_{i+1}' for i in range(len(account_tokens))],
            'has_password': has_password
        }
    
    def validate_metadata(self, metadata: dict) -> bool:
        """
        Valida la estructura de metadatos de un backup.
        
        Args:
            metadata: Diccionario con metadatos a validar
            
        Returns:
            True si los metadatos son válidos, False en caso contrario
        """
        required_keys = {
            'version', 
            'created_at', 
            'accounts_count', 
            'accounts', 
            'has_password'
        }
        
        # Verificar que existan todas las claves requeridas
        if not all(key in metadata for key in required_keys):
            return False
        
        # Validar tipos de datos
        if not isinstance(metadata['version'], str):
            return False
        
        if not isinstance(metadata['created_at'], datetime):
            return False
        
        if not isinstance(metadata['accounts_count'], int):
            return False
        
        if not isinstance(metadata['accounts'], list):
            return False
        
        if not isinstance(metadata['has_password'], bool):
            return False
        
        # Validar consistencia de datos
        if metadata['accounts_count'] != len(metadata['accounts']):
            return False
        
        return True
    
    def add_to_history(self, backup_info: dict) -> None:
        """
        Agrega una entrada al historial de backups.
        
        Args:
            backup_info: Diccionario con información del backup
        """
        with self._lock:
            self._backup_history.append(backup_info)
    
    def get_history(self) -> list[dict]:
        """
        Obtiene el historial completo de backups.
        
        Returns:
            Lista de diccionarios con información de backups
        """
        with self._lock:
            return self._backup_history.copy()
    
    def get_statistics(self) -> dict:
        """
        Calcula estadísticas agregadas de backups.
        
        Returns:
            Diccionario con estadísticas de backups
        """
        with self._lock:
            total_backups = len(self._backup_history)
            total_accounts = sum(
                backup['accounts_count'] 
                for backup in self._backup_history
            )
            
            last_backup_date = None
            if self._backup_history:
                last_backup_date = self._backup_history[-1]['created_at']
            
            return {
                'total_backups': total_backups,
                'total_accounts_backed_up': total_accounts,
                'last_backup_date': last_backup_date
            }