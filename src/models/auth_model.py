"""
Modelo de Autenticación - CoProx

PROPÓSITO:
Este módulo gestiona el estado de la autenticación y tokens de GitHub Copilot.
Mantiene información sobre cuentas activas, cuotas disponibles y tokens válidos.

FUNCIONAMIENTO:
- Almacena el estado actual de autenticación de todas las cuentas
- Rastrea cuotas disponibles y límites de uso por cuenta
- Mantiene contadores de cuentas activas y agotadas
- Proporciona información sobre el token actualmente en uso

PARÁMETROS DE ENTRADA:
- token_data: Diccionario con información del token actual
- quota_info: Diccionario con límites de cuota por cuenta
- account_count: Entero con número total de cuentas disponibles
- exhausted_tokens: Lista de tokens que han agotado su cuota

SALIDA ESPERADA:
- current_token: String con el token activo actual
- current_quota: Diccionario con cuota restante del token activo
- total_accounts: Entero con número total de cuentas configuradas
- available_accounts: Entero con número de cuentas con cuota disponible
- account_status: Diccionario con estado de cada cuenta

PROCESAMIENTO DE DATOS:
- Valida formato de tokens antes de almacenarlos
- Calcula estadísticas agregadas de cuotas
- Determina qué cuenta usar basándose en cuota disponible
- Actualiza contadores cuando se agotan cuentas

INTERACCIONES CON OTROS MÓDULOS:
- Actualizado por: auth_controller.py (nuevos tokens, cuotas)
- Leído por: proxy_controller.py (token actual para solicitudes)
- Consultado por: auth_view.py (mostrar estado de cuentas)
- Modificado por: oauth_service.py (nuevos tokens autenticados)

INTERACCIONES CON MAIN:
- main.py inicializa este modelo al arrancar la aplicación
- Se actualiza continuamente durante la ejecución
- Proporciona estado para la interfaz de usuario
"""

import threading
from typing import Optional
from datetime import datetime


class AuthModel:
    """
    Modelo de autenticación thread-safe para gestión de tokens de GitHub Copilot.
    
    Gestiona múltiples cuentas, rastrea cuotas y proporciona rotación automática
    de tokens cuando se agotan.
    """
    
    def __init__(self):
        """Inicializa el modelo de autenticación vacío"""
        self._accounts: dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def add_account(
        self, 
        token: str, 
        quota_remaining: int = 0, 
        quota_total: int = 0
    ) -> None:
        """
        Agrega una nueva cuenta o actualiza una existente.
        
        Args:
            token: Token de autenticación de GitHub
            quota_remaining: Cuota restante de la cuenta
            quota_total: Cuota total de la cuenta
            
        Raises:
            ValueError: Si el token no tiene un formato válido
        """
        self._validate_token(token)
        
        with self._lock:
            self._accounts[token] = {
                'token': token,
                'quota_remaining': quota_remaining,
                'quota_total': quota_total,
                'is_exhausted': quota_remaining <= 0,
                'last_used': None
            }
    
    def mark_account_as_exhausted(self, token: str) -> None:
        """
        Marca una cuenta como agotada.
        
        Args:
            token: Token de la cuenta a marcar como agotada
            
        Raises:
            KeyError: Si el token no existe
        """
        with self._lock:
            if token not in self._accounts:
                raise KeyError(f"Token no encontrado: {token}")
            
            self._accounts[token]['is_exhausted'] = True
            self._accounts[token]['quota_remaining'] = 0
    
    def update_account_quota(
        self, 
        token: str, 
        quota_remaining: int, 
        quota_total: Optional[int] = None
    ) -> None:
        """
        Actualiza la cuota de una cuenta existente.
        
        Args:
            token: Token de la cuenta a actualizar
            quota_remaining: Nueva cuota restante
            quota_total: Nueva cuota total (opcional)
            
        Raises:
            KeyError: Si el token no existe
        """
        with self._lock:
            if token not in self._accounts:
                raise KeyError(f"Token no encontrado: {token}")
            
            self._accounts[token]['quota_remaining'] = quota_remaining
            if quota_total is not None:
                self._accounts[token]['quota_total'] = quota_total
            
            # Actualizar estado de agotamiento
            self._accounts[token]['is_exhausted'] = quota_remaining <= 0
    
    def get_current_token(self) -> Optional[str]:
        """
        Obtiene el primer token disponible (no agotado).
        
        Returns:
            Token disponible o None si todos están agotados
        """
        with self._lock:
            for token, account in self._accounts.items():
                if not account['is_exhausted']:
                    account['last_used'] = datetime.now()
                    return token
            return None
    
    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas agregadas de las cuentas.
        
        Returns:
            Diccionario con estadísticas de cuentas
        """
        with self._lock:
            total = len(self._accounts)
            available = sum(
                1 for acc in self._accounts.values() 
                if not acc['is_exhausted']
            )
            exhausted = total - available
            
            return {
                'total_accounts': total,
                'available_accounts': available,
                'exhausted_accounts': exhausted
            }
    
    def get_available_accounts_count(self) -> int:
        """
        Obtiene el número de cuentas disponibles (no agotadas).
        
        Returns:
            Número de cuentas con cuota disponible
        """
        with self._lock:
            return sum(
                1 for acc in self._accounts.values() 
                if not acc['is_exhausted']
            )
    
    def get_total_accounts_count(self) -> int:
        """
        Obtiene el número total de cuentas.
        
        Returns:
            Número total de cuentas registradas
        """
        with self._lock:
            return len(self._accounts)
    
    def get_all_accounts(self) -> dict[str, dict]:
        """
        Obtiene una copia de todas las cuentas registradas.
        
        Returns:
            Diccionario con todas las cuentas {token: account_info}
        """
        with self._lock:
            return self._accounts.copy()
    
    def _validate_token(self, token: str) -> None:
        """
        Valida el formato de un token de GitHub.
        
        Args:
            token: Token a validar
            
        Raises:
            ValueError: Si el token no tiene un formato válido
        """
        if not token or not isinstance(token, str):
            raise ValueError("Token inválido: debe ser un string no vacío")
        
        if len(token) < 20:
            raise ValueError("Token inválido: longitud mínima 20 caracteres")
        
        # Validar que contenga solo caracteres alfanuméricos y guiones bajos
        if not token.replace('_', '').isalnum():
            raise ValueError("Token inválido: solo puede contener letras, números y guiones bajos")
