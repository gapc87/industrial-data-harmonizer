# Industrial Data Harmonizer (IDH)

Bienvenido a la documentación técnica oficial. Este proyecto actúa como middleware empresarial para cerrar la brecha entre la **Planta (OT)** y los sistemas corporativos **(IT)**, garantizando la **Integridad Forense** de los datos y habilitando una operación **Cero Papel** basada en una arquitectura **Monolito Modular Híbrido (Core-Feature)**.



## ¿Qué estás buscando?

La documentación está organizada para responder a las necesidades de diferentes roles dentro del equipo.

<div class="grid cards" markdown>

-   :material-compass-outline: **Arquitectos de Software**

    Entiende las decisiones de diseño fundamentales, como el uso del modelo [Híbrido Core-Feature](architecture/concepts.md), la [Seguridad mTLS/OAuth2](architecture/security.md) y nuestra estrategia de [Persistencia Medallion](architecture/data-strategy.md).

-   :material-code-braces: **Desarrolladores**

    Accede a las guías prácticas. Consulta el [Stack Tecnológico](architecture/stack.md), nuestros [Patrones de Implementación](architecture/integration.md#4-comunicacion-en-tiempo-real-wss) y la [Estrategia de Datos](architecture/data-strategy.md).

-   :material-server-network: **Ingenieros DevOps**

    Encuentra los runbooks para operar. Revisa las guías de [Despliegue Outbound-Only](architecture/security.md#3-estrategia-de-red-zero-inbound), [Monitorización](operations/monitoring.md) y [Resolución de Problemas](operations/troubleshooting.md).

</div>

!!! tip "¿Buscas la API?"
    Si necesitas consultar los endpoints disponibles, ve directamente a la [Referencia API](api-reference.md).
