# Estrategia de Testing

En este proyecto seguimos la filosofía **"Test-First"**. No consideramos una tarea terminada hasta que tiene pruebas que demuestren su funcionamiento y protejan contra regresiones.

## 1. Ejecución de Pruebas

La suite completa se ejecuta con un solo comando. Asegúrate de tener Docker corriendo, ya que es necesario para los tests de integración.

```bash
just test
```

Esto lanzará `pytest` con la configuración de cobertura y verbosidad adecuada.

## 2. Niveles de Testing (La Pirámide)

### A. Tests Unitarios (Dominio)

- **Dónde:** `tests/unit/`
- **Velocidad:** < 10ms.
- **Regla:** Prohibido tocar I/O (Base de datos, Red, Disco). Aquí verificamos la lógica pura de negocio (ej: cálculo de mermas). Se pueden usar _Fakes_ o _Stubs_, pero evitamos el exceso de Mocks.

### B. Tests de Integración (Infraestructura)

- **Dónde:** `tests/integration/`
- **Tecnología Clave: Testcontainers.**
- **Filosofía:** **No mockeamos la base de datos.** Cada vez que lanzas estos tests, el sistema levanta un contenedor Docker efímero con una instancia real de PostgreSQL 15, ejecuta las migraciones, corre el test y destruye el contenedor.
- **Por qué:** Garantiza que las _queries_ SQL complejas y los tipos `JSONB` funcionan en el motor real de producción.

## 3. Cobertura (Code Coverage)

No nos obsesionamos con el 100%, pero exigimos un mínimo de **80% de cobertura en la Capa de Dominio**. Si tu PR baja la cobertura global significativamente, será rechazado automáticamente.

```bash
just test-cov
```
