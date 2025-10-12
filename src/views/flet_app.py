"""
Aplicación Principal Flet - CoProx

PROPÓSITO:
Esta es la vista principal de la aplicación que coordina todos los componentes
de interfaz de usuario y maneja la integración con la plataforma Android.

FUNCIONAMIENTO:
- Inicializa la aplicación Flet con configuración para Android
- Coordina todos los componentes de vista (proxy, auth, backup)
- Maneja eventos de interfaz de usuario y los reenvía a controladores
- Implementa navegación entre diferentes pantallas de la aplicación

PARÁMETROS DE ENTRADA:
- page: Objeto Page de Flet para la aplicación
- initial_route: String con pantalla inicial a mostrar
- app_configuration: Diccionario con configuración de la aplicación
- platform_info: Diccionario con información de la plataforma

SALIDA ESPERADA:
- ui_components: Lista de componentes UI inicializados
- navigation_state: String indicando pantalla actual
- user_interaction_events: Lista de eventos de usuario capturados
- view_update_status: Boolean indicando éxito de actualización

PROCESAMIENTO DE DATOS:
- Inicializa componentes UI basándose en estado de modelos
- Maneja routing entre diferentes pantallas
- Procesa eventos de usuario y los traduce a acciones de controlador
- Actualiza interfaz en respuesta a cambios de estado
- Implementa validación de entrada de usuario

INTERACCIONES CON OTROS MÓDULOS:
- Utiliza: proxy_view.py, auth_view.py, backup_view.py (componentes)
- Utiliza: notification_view.py (interfaz Android)
- Recibe actualizaciones de: app_controller.py (cambios de estado)
- Coordina con: android_service.py (eventos de plataforma)

INTERACCIONES CON MAIN:
- main.py inicializa esta aplicación como punto de entrada UI
- Funciona como interfaz principal para toda la interacción del usuario
- Coordina con main.py para manejo de argumentos de línea de comandos
"""