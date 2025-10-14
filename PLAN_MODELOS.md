# Plan de Implementación - Modelos CoProx

**Fecha de creación:** 13 de octubre de 2025  
**Estado:** 📋 PLANIFICADO  
**Metodología:** Test-Driven Development (TDD)

---

## 🎯 Objetivo

Implementar los 4 modelos de datos del sistema CoProx siguiendo la arquitectura MVC correctamente, comenzando por los modelos antes de continuar con más controladores.

---

## 📊 Estado Actual

### ✅ Completado
- **ProxyController**: Implementado y funcionando (35 tests, 69% coverage)
  - Servidor Waitress con multiprocessing
  - Graceful shutdown implementado
  - Compatible con Flet UI

### ⏳ Pendiente
- **ConfigModel**: Solo documentación, sin implementación
- **AuthModel**: Solo documentación, sin implementación
- **ProxyModel**: Solo documentación, sin implementación
- **BackupModel**: Solo documentación, sin implementación

---

## 🗺️ Roadmap de Implementación

```
FASE 1: MODELOS BASE
│
├── Ticket 1: ConfigModel (1-2h) 🔴 CRÍTICA
│   ├── 9 tests unitarios
│   ├── Dependencias: Ninguna
│   └── Base para todos los demás módulos
│
├── Ticket 2: AuthModel (3-4h) 🔴 CRÍTICA
│   ├── 12 tests unitarios
│   ├── Dependencias: ConfigModel
│   └── Gestión de tokens y cuentas
│
├── Ticket 3: ProxyModel (2-3h) 🟡 ALTA
│   ├── 13 tests unitarios
│   ├── Dependencias: ConfigModel
│   └── Estadísticas del servidor
│
└── Ticket 4: BackupModel (2-3h) 🟢 MEDIA
    ├── 12 tests unitarios
    ├── Dependencias: AuthModel
    └── Gestión de backups

FASE 2: INTEGRACIÓN
│
└── Ticket 5: Refactor ProxyController (2-3h) 🟡 ALTA
    ├── 6 tests adicionales
    ├── Dependencias: ConfigModel, AuthModel, ProxyModel
    └── Integración con modelos implementados
```

---

## 📋 Checklist de Tickets

### Ticket 1: ConfigModel
- [ ] RED: Escribir 9 tests (todos fallando)
- [ ] GREEN: Implementar constantes y configuración
- [ ] REFACTOR: Optimizar y documentar
- [ ] Validar con SonarQube
- [ ] Actualizar documentación

### Ticket 2: AuthModel
- [ ] RED: Escribir 12 tests (todos fallando)
- [ ] GREEN: Implementar gestión de cuentas y tokens
- [ ] REFACTOR: Optimizar rotación y validación
- [ ] Validar con SonarQube
- [ ] Actualizar documentación

### Ticket 3: ProxyModel
- [ ] RED: Escribir 13 tests (todos fallando)
- [ ] GREEN: Implementar estadísticas y métricas
- [ ] REFACTOR: Optimizar cálculos y thread-safety
- [ ] Validar con SonarQube
- [ ] Actualizar documentación

### Ticket 4: BackupModel
- [ ] RED: Escribir 12 tests (todos fallando)
- [ ] GREEN: Implementar metadatos y progreso
- [ ] REFACTOR: Optimizar validación
- [ ] Validar con SonarQube
- [ ] Actualizar documentación

### Ticket 5: Refactor ProxyController
- [ ] RED: Escribir 6 tests adicionales (todos fallando)
- [ ] GREEN: Integrar con modelos
- [ ] REFACTOR: Limpiar código legacy
- [ ] Validar que todos los 41 tests pasen
- [ ] Actualizar documentación

---

## 📈 Métricas Objetivo

| Modelo | Tests | Cobertura | Prioridad |
|--------|-------|-----------|-----------|
| ConfigModel | 9 | 100% | 🔴 CRÍTICA |
| AuthModel | 12 | 80%+ | 🔴 CRÍTICA |
| ProxyModel | 13 | 80%+ | 🟡 ALTA |
| BackupModel | 12 | 75%+ | 🟢 MEDIA |
| **TOTAL** | **46** | **80%+** | - |

**Tests adicionales para refactor:** 6  
**Total de tests al finalizar Fase 1:** 35 + 6 = **41 tests** en ProxyController

---

## 🔄 Dependencias entre Modelos

```
ConfigModel (base)
    ├── AuthModel
    │   └── BackupModel
    └── ProxyModel

ProxyController
    ├── ConfigModel
    ├── AuthModel
    └── ProxyModel
```

---

## 📝 Orden de Implementación (CRÍTICO)

**⚠️ IMPORTANTE:** Seguir este orden estrictamente para evitar dependencias circulares.

1. **ConfigModel** primero (sin dependencias)
2. **AuthModel** y **ProxyModel** en paralelo (ambos dependen solo de ConfigModel)
3. **BackupModel** después (depende de AuthModel)
4. **Refactor ProxyController** al final (depende de ConfigModel, AuthModel, ProxyModel)

---

## ⏱️ Estimación Total

| Fase | Tiempo Estimado | Tests |
|------|-----------------|-------|
| ConfigModel | 1-2 horas | 9 |
| AuthModel | 3-4 horas | 12 |
| ProxyModel | 2-3 horas | 13 |
| BackupModel | 2-3 horas | 12 |
| Refactor ProxyController | 2-3 horas | +6 |
| **TOTAL** | **10-15 horas** | **52 tests** |

---

## 🎓 Metodología TDD por Ticket

Para cada modelo:

1. **FASE RED (30%):**
   - Escribir todos los tests primero
   - Ejecutar pytest (deben fallar todos)
   - Confirmar que fallan por la razón correcta

2. **FASE GREEN (50%):**
   - Implementar código mínimo para pasar tests
   - Ejecutar pytest hasta que todos pasen
   - No optimizar aún, solo hacer que funcione

3. **FASE REFACTOR (20%):**
   - Optimizar código manteniendo tests verdes
   - Mejorar nombres, extraer funciones, etc.
   - Ejecutar pytest después de cada cambio
   - Validar con SonarQube

---

## 📚 Recursos y Referencias

- **Registro de tickets completo:** `Registro de tickets.md`
- **Documentación de ProxyController:** `IMPLEMENTACION_PROXY_CONTROLLER.md`
- **Blueprint del sistema:** `blueprint.yaml`
- **Configuración de tests:** `pytest.ini`

---

## 🚀 Próximos Pasos Inmediatos

1. ✅ Crear estructura de directorios para tests (COMPLETADO)
2. ⏳ Implementar Ticket 1: ConfigModel
3. ⏳ Implementar Ticket 2: AuthModel
4. ⏳ Implementar Ticket 3: ProxyModel
5. ⏳ Implementar Ticket 4: BackupModel
6. ⏳ Implementar Ticket 5: Refactor ProxyController

---

## 📌 Notas Importantes

- **ProxyController actual funciona** pero usa datos hardcodeados (`"fake_token"`)
- **No romper funcionalidad existente** al refactorizar
- **Mantener 35 tests de ProxyController pasando** durante refactorización
- **SonarQube debe aprobar** cada modelo antes de continuar
- **Documentación técnica** debe crearse para cada modelo

---

**Última actualización:** 13 de octubre de 2025
