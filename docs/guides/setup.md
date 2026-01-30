# Guía de Instalación y Configuración (Getting Started)

Sigue estos pasos para levantar tu entorno de desarrollo local en menos de 5 minutos.

## 1. Prerrequisitos Técnicos

Antes de clonar el repositorio, asegúrate de tener instaladas las siguientes herramientas en tu sistema (Windows, Mac o Linux):

|**Herramienta**|**Versión Mínima**|**Uso**|**Instalación Recomendada**|
|---|---|---|---|
|**Python**|`3.12+`|Lenguaje base|[python.org](https://www.python.org/)|
|**Docker**|`24.0+`|Infraestructura (DB)|Docker Desktop / OrbStack|
|**uv**|`Latest`|Gestor de Paquetes|`curl -LsSf https://astral.sh/uv/install.sh`|
|**Just**|`Latest`|Ejecutor de Comandos|[Ver guía](https://github.com/casey/just) (ej: `brew install just`)|

## 2. Configuración del Entorno

1. **Clonar el Repositorio:**

    ```bash
    git clone https://github.com/gapc87/industrial-data-harmonizer.git
    cd industrial-data-harmonizer
    ```

2. **Configurar Variables de Entorno:**

    El proyecto sigue la metodología _12-Factor App_. Copia el archivo de ejemplo para crear tu configuración local.

    ```bash
    cp .env.example .env
    ```

    > **Nota:** El archivo `.env` ya viene preconfigurado para funcionar con el entorno Docker local. No necesitas cambiar nada para empezar.

3. **Instalar Dependencias (La Magia de `uv`):**

    En lugar de crear venvs manualmente y esperar minutos con pip, ejecuta:

    ```bash
    just install
    # Equivale a: uv sync
    ```

    Esto creará el entorno virtual (`.venv`) e instalará todas las dependencias (prod + dev) en segundos.


## 3. Tu Primer Despliegue Local

Utilizamos **Just** para abstraer la complejidad de Docker. Levanta la infraestructura (PostgreSQL) y la API con un solo comando:

```bash
just up
```

Verás los logs de la API indicando que el servidor está listo.

Puedes verificar que todo funciona accediendo a la documentación interactiva:

**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

Para detener el entorno:

```bash
just down
```
