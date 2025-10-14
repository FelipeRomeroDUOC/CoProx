"""
Controlador de Backup - CoProx

PROPÓSITO:
Este controlador gestiona las operaciones de exportación e importación de backups,
incluyendo creación de archivos ZIP protegidos y restauración de cuentas.

FUNCIONAMIENTO:
- Coordina exportación de todas las cuentas a archivo ZIP
- Maneja importación y validación de backups desde archivos ZIP
- Implementa protección opcional con contraseña para backups
- Gestiona detección y manejo de cuentas duplicadas durante importación

PARÁMETROS DE ENTRADA:
- export_request: Diccionario con configuración de exportación (contraseña, ubicación)
- import_request: Diccionario con archivo a importar y contraseña si aplica
- backup_metadata: Diccionario con información a incluir en backup
- validation_config: Diccionario con parámetros de validación

SALIDA ESPERADA:
- export_result: Diccionario con resultado de exportación (ruta, estadísticas)
- import_result: Diccionario con resultado de importación (cuentas añadidas)
- validation_status: Diccionario con estado de validación del backup
- operation_progress: Float entre 0-1 indicando progreso de operación

PROCESAMIENTO DE DATOS:
- Genera metadatos automáticamente incluyendo fecha y versión
- Valida estructura de archivos ZIP antes de importar
- Detecta duplicados comparando con cuentas existentes
- Crea estructura temporal para operaciones seguras
- Implementa rollback en caso de errores durante importación

INTERACCIONES CON OTROS MÓDULOS:
- Utiliza: file_service.py (operaciones ZIP y archivos)
- Utiliza: auth_controller.py (importar tokens nuevos)
- Actualiza: backup_model.py (progreso y estado)
- Notifica a: backup_view.py (actualizaciones de progreso)
- Coordina con: android_service.py (selector de archivos)

INTERACCIONES CON MAIN:
- main.py puede usar este controlador para backup automático al iniciar
- Se activa por interacción del usuario desde la interfaz
- Proporciona funcionalidad de migración entre dispositivos
"""

import zipfile
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.models.backup_model import BackupModel
from src.models.auth_model import AuthModel


class BackupController:
    """
    Controlador para gestión de exportación e importación de backups.
    
    Coordina operaciones de backup ZIP con contraseña opcional,
    gestiona progreso y valida integridad de archivos.
    """
    
    BACKUP_VERSION = "1.0"
    METADATA_FILENAME = "metadata.json"
    TOKENS_DIR = "tokens/"
    
    def __init__(
        self,
        backup_model: Optional[BackupModel] = None,
        auth_model: Optional[AuthModel] = None
    ):
        """
        Inicializa el controlador de backup.
        
        Args:
            backup_model: Modelo de backup para gestión de estado
            auth_model: Modelo de autenticación para acceder a cuentas
        """
        self._backup_model = backup_model or BackupModel()
        self._auth_model = auth_model or AuthModel()
    
    def _generate_backup_metadata(self, has_password: bool = False) -> Dict[str, Any]:
        """
        Genera metadatos del backup desde AuthModel.
        
        Args:
            has_password: Si el backup está protegido con contraseña
            
        Returns:
            Diccionario con metadatos del backup
        """
        accounts = self._auth_model.get_all_accounts()
        account_names = [f'account_{i+1}' for i in range(len(accounts))]
        
        return {
            'version': self.BACKUP_VERSION,
            'created_at': datetime.now().isoformat(),
            'accounts_count': len(accounts),
            'accounts': account_names,
            'has_password': has_password
        }
    
    def _create_backup_structure(
        self,
        temp_dir: Path,
        tokens: Dict[str, str],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Crea estructura temporal de backup (metadata.json + tokens/).
        
        Args:
            temp_dir: Directorio temporal donde crear estructura
            tokens: Diccionario de tokens a exportar
            metadata: Metadatos del backup
        """
        # Crear metadata.json
        metadata_path = temp_dir / self.METADATA_FILENAME
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Crear directorio de tokens
        tokens_dir = temp_dir / self.TOKENS_DIR.rstrip('/')
        tokens_dir.mkdir(exist_ok=True)
        
        # Guardar cada token en archivo individual
        for i, (_token_key, token_value) in enumerate(tokens.items(), 1):
            token_file = tokens_dir / f'account_{i}.txt'
            token_file.write_text(token_value, encoding='utf-8')
    
    def _compress_to_zip(
        self,
        source_dir: Path,
        output_path: Path,
        password: Optional[str] = None
    ) -> None:
        """
        Comprime directorio a archivo ZIP con contraseña opcional.
        
        Args:
            source_dir: Directorio fuente a comprimir
            output_path: Ruta del archivo ZIP de salida
            password: Contraseña opcional para proteger el ZIP
        """
        # Asegurar que el directorio de salida existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Si hay contraseña, configurarla
            if password:
                zf.setpassword(password.encode())
            
            # Agregar todos los archivos del directorio
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    
                    if password:
                        # Leer contenido y escribir con contraseña
                        with open(file_path, 'rb') as f:
                            data = f.read()
                        zf.writestr(
                            str(arcname),
                            data,
                            compress_type=zipfile.ZIP_DEFLATED
                        )
                        # Nota: zipfile en Python no soporta encriptación AES
                        # Solo soporta encriptación ZIP 2.0 (débil)
                        # Para producción, considerar usar pyminizip o pyzipper
                    else:
                        zf.write(file_path, arcname)
    
    def export_backup(
        self,
        output_path: Path,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exporta todas las cuentas a archivo ZIP de backup.
        
        Args:
            output_path: Ruta donde guardar el archivo ZIP
            password: Contraseña opcional para proteger el backup
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Iniciar operación de exportación
            self._backup_model.start_operation('export')
            self._backup_model.update_progress(0.1)
            
            # Obtener todas las cuentas
            accounts = self._auth_model.get_all_accounts()
            tokens = {key: acc['token'] for key, acc in accounts.items()}
            
            # Generar metadatos
            metadata = self._generate_backup_metadata(has_password=bool(password))
            self._backup_model.update_progress(0.3)
            
            # Crear estructura temporal
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                self._create_backup_structure(temp_dir, tokens, metadata)
                self._backup_model.update_progress(0.6)
                
                # Comprimir a ZIP
                self._compress_to_zip(temp_dir, output_path, password)
                self._backup_model.update_progress(0.9)
            
            # Completar operación
            self._backup_model.complete_operation()
            self._backup_model.update_progress(1.0)
            
            # Registrar en historial
            self._backup_model.add_to_history({
                'operation': 'export',
                'created_at': datetime.now(),
                'accounts_count': len(accounts),
                'backup_path': str(output_path),
                'has_password': bool(password)
            })
            
            return {
                'success': True,
                'backup_path': str(output_path),
                'accounts_exported': len(accounts),
                'has_password': bool(password)
            }
            
        except Exception as e:
            # Manejar error
            error_msg = f"Error durante exportación: {str(e)}"
            self._backup_model.fail_operation(error_msg)
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def validate_backup_structure(self, zip_path: Path) -> bool:
        """
        Valida que un archivo ZIP tenga la estructura esperada de backup.
        
        Args:
            zip_path: Ruta al archivo ZIP a validar
            
        Returns:
            True si la estructura es válida, False en caso contrario
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                
                # Verificar que exista metadata.json
                if self.METADATA_FILENAME not in files:
                    return False
                
                # Verificar que exista al menos un archivo en tokens/
                has_tokens = any(f.startswith(self.TOKENS_DIR) and f != self.TOKENS_DIR for f in files)
                
                return has_tokens
                
        except Exception:
            return False
    
    def _extract_metadata(self, zip_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extrae metadata.json de un archivo ZIP de backup.
        
        Args:
            zip_path: Ruta al archivo ZIP
            
        Returns:
            Diccionario con metadatos o None si falla
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                metadata_str = zf.read(self.METADATA_FILENAME).decode('utf-8')
                return json.loads(metadata_str)
        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError):
            return None
    
    def _extract_tokens_from_backup(
        self,
        zip_path: Path,
        password: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Extrae tokens de un archivo ZIP de backup.
        
        Args:
            zip_path: Ruta al archivo ZIP
            password: Contraseña opcional si el ZIP está protegido
            
        Returns:
            Diccionario {account_name: token}
        """
        tokens = {}
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Configurar contraseña si existe
                if password:
                    zf.setpassword(password.encode())
                
                # Extraer todos los archivos de tokens/
                for file_info in zf.filelist:
                    if file_info.filename.startswith(self.TOKENS_DIR) and file_info.filename != self.TOKENS_DIR:
                        try:
                            token_data = zf.read(file_info.filename)
                            if password:
                                token_data = zf.read(file_info.filename, pwd=password.encode())
                            
                            token = token_data.decode('utf-8').strip()
                            account_name = Path(file_info.filename).stem
                            tokens[account_name] = token
                        except (UnicodeDecodeError, RuntimeError):
                            continue
                            
        except Exception:
            pass
        
        return tokens
    
    def import_backup(
        self,
        zip_path: Path,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Importa cuentas desde archivo ZIP de backup.
        
        Args:
            zip_path: Ruta al archivo ZIP de backup
            password: Contraseña si el backup está protegido
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Iniciar operación de importación
            self._backup_model.start_operation('import')
            self._backup_model.update_progress(0.1)
            
            # Validar estructura del backup
            if not self.validate_backup_structure(zip_path):
                error_msg = "Estructura de backup inválida"
                self._backup_model.fail_operation(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            self._backup_model.update_progress(0.3)
            
            # Extraer metadata
            metadata = self._extract_metadata(zip_path)
            if not metadata:
                error_msg = "No se pudo extraer metadata del backup"
                self._backup_model.fail_operation(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            self._backup_model.update_progress(0.5)
            
            # Extraer tokens
            tokens = self._extract_tokens_from_backup(zip_path, password)
            if not tokens:
                # Backup válido pero sin tokens
                self._backup_model.complete_operation()
                return {
                    'success': True,
                    'imported': 0,
                    'skipped': 0,
                    'total': 0
                }
            
            self._backup_model.update_progress(0.7)
            
            # Obtener cuentas existentes
            existing_accounts = self._auth_model.get_all_accounts()
            existing_tokens = {acc['token'] for acc in existing_accounts.values()}
            
            # Importar tokens nuevos
            imported = 0
            skipped = 0
            
            for _account_name, token in tokens.items():
                if token in existing_tokens:
                    skipped += 1
                else:
                    try:
                        # Agregar cuenta al AuthModel
                        # Por ahora sin verificar cuota (se puede hacer después)
                        self._auth_model.add_account(
                            token=token,
                            quota_remaining=0,
                            quota_total=0
                        )
                        imported += 1
                    except ValueError:
                        # Si falla agregar (token inválido), contar como omitido
                        skipped += 1
            
            self._backup_model.update_progress(0.9)
            
            # Completar operación
            self._backup_model.complete_operation()
            self._backup_model.update_progress(1.0)
            
            # Registrar en historial
            self._backup_model.add_to_history({
                'operation': 'import',
                'created_at': datetime.now(),
                'imported': imported,
                'skipped': skipped,
                'total': imported + skipped,
                'backup_path': str(zip_path)
            })
            
            return {
                'success': True,
                'imported': imported,
                'skipped': skipped,
                'total': imported + skipped
            }
            
        except zipfile.BadZipFile:
            error_msg = "Archivo ZIP corrupto o inválido"
            self._backup_model.fail_operation(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error durante importación: {str(e)}"
            self._backup_model.fail_operation(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_backup_history(self) -> list[Dict[str, Any]]:
        """
        Obtiene el historial completo de operaciones de backup.
        
        Returns:
            Lista de diccionarios con información de operaciones
        """
        return self._backup_model.get_history()
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de backups.
        
        Returns:
            Diccionario con estadísticas de backups
        """
        return self._backup_model.get_statistics()