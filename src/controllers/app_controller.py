"""
Controlador Principal de Aplicación - CoProx

PROPÓSITO:
Este es el controlador maestro que coordina todos los demás controladores y
gestiona el ciclo de vida completo de la aplicación incluyendo eventos Android.

FUNCIONAMIENTO:
- Inicializa y coordina todos los controladores específicos
- Maneja eventos de ciclo de vida (minimize, resume, close)
- Coordina comunicación entre modelos, vistas y controladores
- Implementa lógica de estado global de la aplicación

PARÁMETROS DE ENTRADA:
- app_lifecycle_event: String indicando evento de ciclo de vida
- initialization_config: Diccionario con configuración inicial
- shutdown_request: Boolean para iniciar cierre controlado
- state_save_trigger: Evento para guardar estado actual

SALIDA ESPERADA:
- app_status: String indicando estado general de la aplicación
- lifecycle_response: Diccionario con respuesta a evento de ciclo de vida
- initialization_result: Boolean indicando éxito de inicialización
- shutdown_status: String indicando progreso de cierre

PROCESAMIENTO DE DATOS:
- Coordina inicialización de todos los modelos y servicios
- Maneja transiciones de estado de la aplicación
- Implementa persistencia de estado entre sesiones
- Gestiona recursos y cleanup durante cierre
- Coordina sincronización entre componentes

INTERACCIONES CON OTROS MÓDULOS:
- Coordina: auth_controller.py, proxy_controller.py, backup_controller.py
- Utiliza: android_service.py (eventos de plataforma)
- Actualiza: todos los modelos según sea necesario
- Notifica a: flet_app.py (cambios de estado global)

INTERACCIONES CON MAIN:
- main.py instancia y usa este controlador como punto de entrada principal
- Recibe control total de la aplicación después de main.py
- Maneja toda la lógica de aplicación mientras main.py gestiona UI
"""