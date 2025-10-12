"""
Punto de Entrada Principal - CoProx

PROPÓSITO:
Este es el punto de entrada principal de la aplicación CoProx. Coordina la inicialización
de toda la arquitectura MVC, maneja argumentos de línea de comandos y lanza la interfaz Flet.

FUNCIONAMIENTO:
- Analiza argumentos de línea de comandos (especialmente --add-account)
- Inicializa el controlador principal de la aplicación (app_controller)
- Detecta la plataforma de ejecución (Android vs Desktop)
- Configura y lanza la aplicación Flet con la vista principal
- Maneja el ciclo de vida inicial de la aplicación

PARÁMETROS DE ENTRADA:
- sys.argv: Lista de argumentos de línea de comandos
- page: Objeto Page de Flet proporcionado por el framework
- platform_detection: Información automática de la plataforma
- environment_variables: Variables de entorno del sistema

SALIDA ESPERADA:
- application_instance: Instancia de la aplicación Flet ejecutándose
- initialization_status: Boolean indicando éxito de inicialización
- error_messages: Lista de errores si la inicialización falla
- exit_code: Entero con código de salida de la aplicación

PROCESAMIENTO DE DATOS:
- Parsea argumentos de línea de comandos para determinar modo de operación
- Inicializa modelos con configuración por defecto
- Crea instancias de todos los controladores necesarios
- Configura la aplicación Flet según la plataforma detectada
- Establece manejadores de eventos globales para ciclo de vida

INTERACCIONES CON OTROS MÓDULOS:
- Inicializa: app_controller.py (controlador maestro)
- Utiliza: flet_app.py (vista principal de la aplicación)
- Configura: config_model.py (configuración inicial)
- Detecta: android_service.py (si está en Android)
- Coordina: Todos los módulos MVC a través del app_controller

COMPORTAMIENTO ESPECIAL:
- Modo --add-account: Ejecuta flujo de autenticación directamente
- Modo normal: Lanza interfaz Flet completa
- Modo Android: Configura notificaciones persistentes
- Manejo de errores: Captura y reporta errores de inicialización

FLUJO DE EJECUCIÓN:
1. Verificar argumentos de línea de comandos
2. Detectar plataforma (Android/Desktop)
3. Inicializar configuración global
4. Crear controlador principal de aplicación
5. Si --add-account: ejecutar auth_controller.add_account()
6. Si modo normal: inicializar flet_app y ejecutar ft.app()
7. Mantener aplicación corriendo hasta cierre del usuario
"""

import flet as ft


def main(page: ft.Page):
    counter = ft.Text("0", size=50, data=0)

    def increment_click(e):
        counter.data += 1
        counter.value = str(counter.data)
        counter.update()

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, on_click=increment_click
    )
    page.add(
        ft.SafeArea(
            ft.Container(
                counter,
                alignment=ft.alignment.center,
            ),
            expand=True,
        )
    )


ft.app(main)
