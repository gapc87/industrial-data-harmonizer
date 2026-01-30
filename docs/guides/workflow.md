# Flujo de Trabajo y Herramientas (Workflow)

Hemos automatizado las tareas repetitivas para que te centres en programar.

## 1. El Catálogo de Comandos (`Justfile`)

Olvídate de memorizar comandos largos de Docker o argumentos de Pytest. Ejecuta `just --list` para ver el menú disponible.

### Desarrollo Local

| Comando | Descripción |
|---------|-------------|
| `just setup-env` | Crea `.env` desde `.env.example` con `SECRET_KEY` aleatoria |
| `just install` | Sincroniza dependencias con `uv` (ejecutar tras `git pull`) |
| `just run` | Servidor en modo desarrollo con _hot-reload_ |

### Docker

| Comando | Descripción |
|---------|-------------|
| `just up` | Levanta infraestructura (DB + API) en segundo plano |
| `just up-dev` | Igual que `up` pero incluye pgAdmin |
| `just down` | Detiene todos los servicios |
| `just restart` | Reinicia servicios (útil tras cambios en `.env`) |
| `just logs` | Ver logs de todos los contenedores |

### Calidad y Testing

| Comando | Descripción |
|---------|-------------|
| `just lint` | Audita y formatea código automáticamente (Ruff) |
| `just check` | Ejecuta `lint-check` + `typecheck` |
| `just test` | Ejecuta suite completa de pruebas |

## 2. Gestión de Dependencias (con `uv`)

No uses `pip install`. Usamos **uv** para mantener el archivo `pyproject.toml` y `uv.lock` siempre sincronizados.

- **Añadir una librería:** `uv add requests`
- **Añadir una librería de dev:** `uv add --dev pytest`
- **Actualizar todo:** `uv sync --upgrade`

## 3. Gestión de Versiones y Git

Mantenemos un historial de Git limpio y semántico.

### 3.1. Estrategia de Ramas (GitFlow Simplificado)

Hemos implementado un flujo estricto para garantizar la estabilidad en producción.

**Ramas Principales:**

-   **`main` (Producción):** Contiene código listo para desplegar.
    -   🔴 **Protegida:** No se puede hacer push directo.
    -   🛡️ **Restringida:** Solo acepta Pull Requests desde `dev` o `hotfix/*`.
    -   🚀 **CD:** Despliega automáticamente documentación y aplicación (template).

-   **`dev` (Integración):** Rama de desarrollo activa donde convergen las features.
    -   🔴 **Protegida:** No se puede hacer push directo (bloqueado localmente por `pre-commit`).
    -   🛡️ **CI:** Ejecuta tests unitarios de integración en cada PR.

**Ramas de Trabajo (Feature Branches):**

Todo trabajo debe realizarse en ramas temporales creadas desde `dev`:

-   `feat/nombre-funcionalidad`: Nuevas características.
-   `fix/nombre-bug`: Corrección de errores.
-   `chore/mantenimiento`: Tareas técnicas, librerías, limpieza.
-   `docs/nombre-doc`: Cambios en documentación.
-   `test/nombre-test`: Añadir o corregir tests.
-   `refactor/nombre`: Mejoras de código sin cambiar comportamiento.
-   `ci/nombre`: Cambios en GitHub Actions.

**Regla de Oro:** Tu flujo diario es `feat/x` -> PR -> `dev`.

### 3.2. Convención de Commits

Nuestros mensajes de commit siguen una estructura estricta: `tipo(ámbito): descripción breve`.

|**Tipo**|**Ejemplo**|
|---|---|
|`feat`|`feat(ingesta): añadir soporte para IDocs XML`|
|`fix`|`fix(calculo): corregir error de redondeo`|
|`docs`|`docs(api): actualizar swagger`|
|`chore`|`chore(deps): actualizar uv`|

### 3.3. Automatización (Git Hooks)

Para evitar accidentes, recomendamos instalar los _hooks_ de pre-commit.

```bash
just pre-commit-install
```

Esto ejecutará los tests y el linter automáticamente cada vez que hagas un `git commit`.

## 4. Proceso de Pull Request (PR)

### Checklist del Desarrollador (Self-Review)

Antes de pedir revisión a un compañero, asegúrate de cumplir esto:

- [ ] **Funciona:** He probado la funcionalidad manualmente en local (`just run`).
- [ ] **Testado:** He añadido tests unitarios y de integración (`just test` pasa en verde).
- [ ] **Limpio:** He ejecutado el linter (`just lint`) y no hay errores de MyPy.
- [ ] **Documentado:** Si he cambiado un endpoint, he verificado que Swagger se actualiza.
- [ ] **Atómico:** El PR aborda una sola funcionalidad.

### Criterios de Revisión

Tus compañeros revisarán:
1. **Legibilidad:** ¿Se entiende el código sin explicarlo?
2. **Arquitectura:** ¿Se respeta la separación de capas (Dominio vs Infra)?
3. **Seguridad:** ¿Hay datos sensibles logueados? ¿Se validan los inputs?

## 5. Pipeline de CI/CD (Automatización)

Nuestro repositorio cuenta con una serie de guardianes automáticos:

### En tu máquina (Local)
- **Pre-commit:** Al hacer commit, se ejecuta `ruff` (linter/format) y se verifica el nombre de tu rama.
- **Bloqueo:** No te permitirá hacer commits en `dev` o `main` directamente.

### En GitHub (Remoto)
- **CI Quality Gate (`ci.yml`):** Se dispara al abrir un Pull Request hacia `dev` o `main`.
    1. Instala dependencias con `uv`.
    2. Genera el esquema OpenAPI para validar `main.py`.
    3. **Ejecuta Tests:** Corre `pytest` (unitarios e integración).
    4. **Verifica Docs:** Construye MkDocs en modo estricto para detectar enlaces rotos.
    5. **GitFlow Guardrail:** Si el PR va a `main`, verifica que venga de `dev` (bloquea `feat` -> `main`).

- **Deploy Documentation (`docs.yml`):**
    - Se ejecuta solo al fusionar en `main`.
    - Publica la web en GitHub Pages.

- **CD Production (`cd.yml`):**
    - Se ejecuta solo al fusionar en `main`.
    - (Template) Despliega la aplicación en el entorno de producción (ej. Koyeb).
