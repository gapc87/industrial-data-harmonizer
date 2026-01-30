# Estándares de Código y Calidad

En este proyecto, la calidad no es opcional ni postergable. El código "sucio" rompe la producción.

## 1. Principios de Ingeniería

Para mantener el estándar de calidad, nos regimos por los siguientes pilares:

- **Clean Code & Tipado Estricto:** Python es nuestro lenguaje, pero lo escribimos con el rigor de un lenguaje estático. `MyPy` en modo estricto es nuestro guardián. No dejamos `Any` sueltos.

- **Domain-Driven Design (DDD):** El código debe hablar el idioma de la fábrica. Si el experto de planta dice "Lote", el código dice `Batch`, no `data_array`. Protegemos el Dominio en el centro de nuestra Arquitectura Hexagonal.

- **Testing como Documentación:** No escribimos tests solo para buscar bugs; los escribimos para documentar cómo debe comportarse el sistema.

- **Entorno Determinista:** Odiamos el _"en mi máquina funciona"_. Usamos `uv` y `Docker`.


## 2. Herramientas de Calidad

Usamos herramientas de análisis estático para detectar errores antes de que ocurran.

### 2.1. Linting y Formateo (Ruff)

Usamos **Ruff**, una herramienta extremadamente rápida escrita en Rust que reemplaza a _Black_, _Isort_ y _Flake8_.

- **Regla de Oro:** Si el linter se queja, no puedes hacer merge.

- **Cómo arreglarlo:** La mayoría de errores se corrigen solos ejecutando:

    ```bash
    just lint
    ```


### 2.2. Tipado Estático (MyPy Strict)

Python es dinámico, pero nuestro Dominio no. Usamos **MyPy** en modo `--strict`.

- **Requisito:** Todas las funciones deben tener _Type Hints_ en argumentos y retorno.

- **Prohibido:** Evita el uso de `Any`. Si no sabes qué tipo es, probablemente tu diseño necesita una revisión.

    ```python
    # ❌ Mal
    def procesar(dato): ...

    # ✅ Bien
    def procesar(dato: ProductionOrder) -> ProcessingResult: ...
    ```
