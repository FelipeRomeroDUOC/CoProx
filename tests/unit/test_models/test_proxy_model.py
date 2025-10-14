"""
Tests unitarios para ProxyModel

Valida la gestión de estado del servidor, estadísticas, uptime y health check.
Incluye validación de contadores thread-safe y cálculos precisos.
"""

import pytest
import time
from datetime import datetime
from src.models.proxy_model import ProxyModel


class TestProxyModelInitialization:
    """Tests para la inicialización del ProxyModel"""

    def test_initialize_proxy_model_stopped(self):
        """Verifica que ProxyModel se inicializa en estado stopped"""
        proxy_model = ProxyModel()
        
        assert proxy_model is not None
        assert not proxy_model.is_running()
        assert proxy_model.get_total_requests() == 0
        assert proxy_model.get_failed_requests() == 0


class TestProxyModelServerState:
    """Tests para gestión del estado del servidor"""

    def test_start_server_updates_state(self):
        """Verifica que start_server actualiza el estado correctamente"""
        proxy_model = ProxyModel()
        
        proxy_model.start_server(host="0.0.0.0", port=5000)
        
        assert proxy_model.is_running()
        assert proxy_model.get_host() == "0.0.0.0"
        assert proxy_model.get_port() == 5000

    def test_stop_server_updates_state(self):
        """Verifica que stop_server actualiza el estado correctamente"""
        proxy_model = ProxyModel()
        
        proxy_model.start_server(host="0.0.0.0", port=5000)
        assert proxy_model.is_running()
        
        proxy_model.stop_server()
        assert not proxy_model.is_running()


class TestProxyModelRequestCounters:
    """Tests para contadores de solicitudes"""

    def test_increment_request_counter(self):
        """Verifica que se puede incrementar el contador de solicitudes"""
        proxy_model = ProxyModel()
        
        proxy_model.increment_request_counter()
        proxy_model.increment_request_counter()
        proxy_model.increment_request_counter()
        
        assert proxy_model.get_total_requests() == 3

    def test_increment_error_counter(self):
        """Verifica que se puede incrementar el contador de errores"""
        proxy_model = ProxyModel()
        
        proxy_model.increment_error_counter()
        proxy_model.increment_error_counter()
        
        assert proxy_model.get_failed_requests() == 2


class TestProxyModelUptime:
    """Tests para cálculo de uptime"""

    def test_calculate_uptime_when_running(self):
        """Verifica que calcula uptime correctamente cuando está activo"""
        proxy_model = ProxyModel()
        
        proxy_model.start_server()
        time.sleep(0.1)  # Esperar 100ms
        
        uptime = proxy_model.get_uptime_seconds()
        assert uptime >= 0.1
        assert uptime < 1.0  # Debe ser menor a 1 segundo

    def test_calculate_uptime_when_stopped(self):
        """Verifica que uptime es 0 cuando está detenido"""
        proxy_model = ProxyModel()
        
        uptime = proxy_model.get_uptime_seconds()
        assert uptime == 0


class TestProxyModelStatistics:
    """Tests para estadísticas agregadas"""

    def test_get_statistics_returns_correct_data(self):
        """Verifica que get_statistics devuelve datos correctos"""
        proxy_model = ProxyModel()
        
        proxy_model.start_server(host="127.0.0.1", port=8080)
        proxy_model.increment_request_counter()
        proxy_model.increment_request_counter()
        proxy_model.increment_error_counter()
        
        stats = proxy_model.get_statistics()
        
        assert stats['total_requests'] == 2
        assert stats['successful_requests'] == 1
        assert stats['failed_requests'] == 1
        assert 'uptime_seconds' in stats
        assert 'success_rate' in stats

    def test_calculate_success_rate(self):
        """Verifica que calcula la tasa de éxito correctamente"""
        proxy_model = ProxyModel()
        
        # 8 exitosas, 2 fallidas = 80% éxito
        for _ in range(10):
            proxy_model.increment_request_counter()
        for _ in range(2):
            proxy_model.increment_error_counter()
        
        stats = proxy_model.get_statistics()
        assert stats['success_rate'] == 0.8  # 80%

    def test_calculate_success_rate_with_no_requests(self):
        """Verifica que success_rate es 1.0 cuando no hay solicitudes"""
        proxy_model = ProxyModel()
        
        stats = proxy_model.get_statistics()
        assert stats['success_rate'] == 1.0


class TestProxyModelReset:
    """Tests para reseteo de estadísticas"""

    def test_reset_statistics(self):
        """Verifica que reset_statistics limpia todos los contadores"""
        proxy_model = ProxyModel()
        
        proxy_model.start_server()
        proxy_model.increment_request_counter()
        proxy_model.increment_request_counter()
        proxy_model.increment_error_counter()
        
        proxy_model.reset_statistics()
        
        assert proxy_model.get_total_requests() == 0
        assert proxy_model.get_failed_requests() == 0


class TestProxyModelLastRequest:
    """Tests para registro de última solicitud"""

    def test_update_last_request_time(self):
        """Verifica que actualiza el timestamp de última solicitud"""
        proxy_model = ProxyModel()
        
        before = datetime.now()
        proxy_model.update_last_request_time()
        after = datetime.now()
        
        last_request = proxy_model.get_last_request_time()
        
        assert last_request is not None
        assert before <= last_request <= after


class TestProxyModelHealthCheck:
    """Tests para health check del servidor"""

    def test_health_status_returns_healthy_when_low_errors(self):
        """Verifica que devuelve 'healthy' con baja tasa de errores"""
        proxy_model = ProxyModel()
        
        # 95 exitosas, 5 errores = 95% éxito
        for _ in range(100):
            proxy_model.increment_request_counter()
        for _ in range(5):
            proxy_model.increment_error_counter()
        
        health = proxy_model.get_health_status()
        assert health == 'healthy'

    def test_health_status_returns_unhealthy_when_high_errors(self):
        """Verifica que devuelve 'unhealthy' con alta tasa de errores"""
        proxy_model = ProxyModel()
        
        # 40 exitosas, 60 errores = 40% éxito
        for _ in range(100):
            proxy_model.increment_request_counter()
        for _ in range(60):
            proxy_model.increment_error_counter()
        
        health = proxy_model.get_health_status()
        assert health == 'unhealthy'

    def test_health_status_returns_degraded_when_moderate_errors(self):
        """Verifica que devuelve 'degraded' con tasa moderada de errores"""
        proxy_model = ProxyModel()
        
        # 75 exitosas, 25 errores = 75% éxito
        for _ in range(100):
            proxy_model.increment_request_counter()
        for _ in range(25):
            proxy_model.increment_error_counter()
        
        health = proxy_model.get_health_status()
        assert health == 'degraded'


class TestProxyModelThreadSafety:
    """Tests para verificar thread-safety"""

    def test_concurrent_request_increments(self):
        """Verifica que los incrementos concurrentes son seguros"""
        import threading
        
        proxy_model = ProxyModel()
        
        def increment_requests():
            for _ in range(100):
                proxy_model.increment_request_counter()
        
        threads = [threading.Thread(target=increment_requests) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 10 threads × 100 incrementos = 1000 total
        assert proxy_model.get_total_requests() == 1000
