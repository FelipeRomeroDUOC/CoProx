"""
Modelo del Proxy - CoProx

PROPÓSITO:
Este módulo mantiene el estado del servidor proxy HTTP y sus estadísticas de funcionamiento.
Rastrea si el proxy está activo, puerto en uso y métricas de solicitudes procesadas.

FUNCIONAMIENTO:
- Almacena el estado actual del servidor proxy (activo/inactivo)
- Mantiene estadísticas de solicitudes procesadas
- Rastrea errores y tiempo de actividad
- Proporciona información sobre el puerto y host del servidor

PARÁMETROS DE ENTRADA:
- server_status: Boolean indicando si el servidor está activo
- port: Entero con el puerto donde escucha el servidor
- host: String con la dirección IP del servidor
- request_count: Entero con número de solicitudes procesadas
- error_count: Entero con número de errores ocurridos
- uptime: Tiempo transcurrido desde el inicio del servidor

SALIDA ESPERADA:
- is_running: Boolean del estado actual del proxy
- server_info: Diccionario con host, puerto y configuración
- statistics: Diccionario con métricas de uso y rendimiento
- last_request_time: Timestamp de la última solicitud procesada
- health_status: String indicando el estado de salud del servidor

PROCESAMIENTO DE DATOS:
- Actualiza contadores de solicitudes en tiempo real
- Calcula estadísticas de rendimiento y uptime
- Determina estado de salud basándose en errores recientes
- Formatea métricas para mostrar en la interfaz

INTERACCIONES CON OTROS MÓDULOS:
- Actualizado por: proxy_controller.py (estadísticas del servidor)
- Leído por: proxy_view.py (mostrar estado del proxy)
- Consultado por: app_controller.py (estado general de la aplicación)
- Modificado por: android_service.py (notificaciones de estado)

INTERACCIONES CON MAIN:
- main.py consulta este modelo para determinar si iniciar el proxy
- Se actualiza cuando el usuario inicia/detiene el servidor
- Proporciona información para la notificación persistente de Android
"""

import threading
from typing import Optional
from datetime import datetime
from src.models.config_model import DEFAULT_HOST, DEFAULT_PORT


class ProxyModel:
    """
    Modelo del servidor proxy thread-safe para gestión de estado y estadísticas.
    
    Mantiene el estado del servidor, contadores de solicitudes y métricas
    de rendimiento con acceso thread-safe.
    """
    
    def __init__(self):
        """Inicializa el modelo del proxy en estado detenido"""
        self._running = False
        self._host = DEFAULT_HOST
        self._port = DEFAULT_PORT
        self._start_time: Optional[datetime] = None
        self._total_requests = 0
        self._failed_requests = 0
        self._last_request_time: Optional[datetime] = None
        self._lock = threading.Lock()
    
    def start_server(
        self, 
        host: str = DEFAULT_HOST, 
        port: int = DEFAULT_PORT
    ) -> None:
        """
        Marca el servidor como iniciado y registra configuración.
        
        Args:
            host: Host donde escucha el servidor
            port: Puerto donde escucha el servidor
        """
        with self._lock:
            self._running = True
            self._host = host
            self._port = port
            self._start_time = datetime.now()
    
    def stop_server(self) -> None:
        """Marca el servidor como detenido"""
        with self._lock:
            self._running = False
            self._start_time = None
    
    def is_running(self) -> bool:
        """
        Verifica si el servidor está activo.
        
        Returns:
            True si el servidor está ejecutándose
        """
        with self._lock:
            return self._running
    
    def get_host(self) -> str:
        """
        Obtiene el host del servidor.
        
        Returns:
            Host configurado
        """
        with self._lock:
            return self._host
    
    def get_port(self) -> int:
        """
        Obtiene el puerto del servidor.
        
        Returns:
            Puerto configurado
        """
        with self._lock:
            return self._port
    
    def increment_request_counter(self) -> None:
        """Incrementa el contador de solicitudes totales de forma thread-safe"""
        with self._lock:
            self._total_requests += 1
    
    def increment_error_counter(self) -> None:
        """Incrementa el contador de errores de forma thread-safe"""
        with self._lock:
            self._failed_requests += 1
    
    def get_total_requests(self) -> int:
        """
        Obtiene el número total de solicitudes procesadas.
        
        Returns:
            Contador de solicitudes totales
        """
        with self._lock:
            return self._total_requests
    
    def get_failed_requests(self) -> int:
        """
        Obtiene el número de solicitudes fallidas.
        
        Returns:
            Contador de solicitudes fallidas
        """
        with self._lock:
            return self._failed_requests
    
    def get_uptime_seconds(self) -> float:
        """
        Calcula el tiempo de actividad del servidor en segundos.
        
        Returns:
            Segundos transcurridos desde el inicio, 0 si está detenido
        """
        with self._lock:
            if not self._running or self._start_time is None:
                return 0.0
            
            uptime = (datetime.now() - self._start_time).total_seconds()
            return uptime
    
    def update_last_request_time(self) -> None:
        """Actualiza el timestamp de la última solicitud procesada"""
        with self._lock:
            self._last_request_time = datetime.now()
    
    def get_last_request_time(self) -> Optional[datetime]:
        """
        Obtiene el timestamp de la última solicitud.
        
        Returns:
            Datetime de última solicitud o None si no hay solicitudes
        """
        with self._lock:
            return self._last_request_time
    
    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas agregadas del servidor.
        
        Returns:
            Diccionario con métricas completas del servidor
        """
        with self._lock:
            successful = self._total_requests - self._failed_requests
            
            # Calcular tasa de éxito
            if self._total_requests > 0:
                success_rate = successful / self._total_requests
            else:
                success_rate = 1.0
            
            # Calcular uptime sin llamar a método que usa lock
            if self._running and self._start_time is not None:
                uptime = (datetime.now() - self._start_time).total_seconds()
            else:
                uptime = 0.0
            
            return {
                'total_requests': self._total_requests,
                'successful_requests': successful,
                'failed_requests': self._failed_requests,
                'uptime_seconds': uptime,
                'last_request_time': self._last_request_time,
                'success_rate': success_rate
            }
    
    def reset_statistics(self) -> None:
        """Resetea todos los contadores de estadísticas a cero"""
        with self._lock:
            self._total_requests = 0
            self._failed_requests = 0
            self._last_request_time = None
    
    def get_health_status(self) -> str:
        """
        Determina el estado de salud del servidor basado en tasa de errores.
        
        Returns:
            'healthy', 'degraded', o 'unhealthy'
        """
        with self._lock:
            if self._total_requests == 0:
                return 'healthy'
            
            error_rate = self._failed_requests / self._total_requests
            
            if error_rate < 0.1:  # Menos de 10% errores
                return 'healthy'
            elif error_rate < 0.5:  # Entre 10% y 50% errores
                return 'degraded'
            else:  # Más de 50% errores
                return 'unhealthy'
