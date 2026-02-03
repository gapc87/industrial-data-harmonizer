# Conceptos Arquitectónicos y Visión

**Versión:** 2.0.0
**Enfoque:** Monolito Modular, Hexagonal & DDD con Edge Computing.

## 1. Visión General

El proyecto **Industrial Data Harmonizer (IDH)** es una plataforma de middleware diseñada para cerrar la brecha tecnológica entre la planta de producción (OT) y los sistemas de gestión corporativa (IT).

Su misión es orquestar la convergencia de datos industriales, recolectando telemetría de maquinaria en tiempo real de forma segura, normalizando dicha información mediante reglas de negocio complejas, y exponiéndola a los departamentos de Producción, Calidad y Logística.

## 2. Estilo Arquitectónico: Monolito Modular

Se ha optado por un **Monolito Modular** en lugar de microservicios distribuidos.

* **Definición (Híbrido Core-Feature):** El sistema se despliega como una única unidad, pero se organiza en un **Core** (lógica transversal y seguridad) y múltiples **Features** aisladas (`ingestion`, `production`, `quality`).

* **Justificación:** Maximiza la productividad de un equipo pequeño al evitar la latencia de red entre servicios, pero garantiza un aislamiento físico que permite la futura extracción de una *Feature* (ej: Ingestión distribuida) con mínimo esfuerzo de refactorización.

## 3. Patrón Estructural: Arquitectura Hexagonal

Para desacoplar la lógica de negocio de las tecnologías externas, se implementa estrictamente la Arquitectura Hexagonal (Ports & Adapters).

* **Núcleo (Dominio):** Contiene la lógica pura de negocio (Reglas DDD). No tiene dependencias externas.

* **Puertos y Adaptadores:** La comunicación con el mundo exterior (Base de datos PostgreSQL, API REST, SAP) se realiza a través de interfaces (Puertos) e implementaciones (Adaptadores).

## 4. Metodologías y Stack Tecnológico

Para mantener esta visión clara, hemos extraído los detalles técnicos a documentos específicos:

*   **[Metodología de Diseño (DDD, TDD, CQRS)](methodology.md):** Profundiza en nuestros patrones tácticos, lenguaje ubicuo y estrategia de pruebas.
*   **[Stack Tecnológico](stack.md):** Detalle de lenguajes, frameworks y herramientas (Python 3.12+, FastAPI, Rust-based tooling).

## 5. Diagramas de Arquitectura

### A. Diagrama Físico: Topología de Red y Edge Computing

Este esquema ilustra cómo aislamos la red de fábrica (OT) de la red corporativa (IT).

```mermaid
graph TD
    %% Estilos
    classDef ot fill:#ffccbc,stroke:#bf360c,stroke-width:2px,color:black;
    classDef edge fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,stroke-dasharray: 5 5,color:black;
    classDef it fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:black;
    classDef db fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:black;

    %% ZONA 1: PLANTA (OT)
    subgraph Factory_Floor ["ZONA OT: Planta (Sin Internet)"]
        PLC1["PLC Maquinaria Principal <br/>(Modbus TCP)"]:::ot
        PLC2["PLC Maquinaria Auxiliar <br/>(Siemens S7)"]:::ot
    end

    %% ZONA 2: EDGE (Frontera)
    subgraph Edge_Zone ["ZONA EDGE: Gateway"]
        Collector["Edge Collector (Script) <br/> Cliente OAuth2"]:::edge
        Buffer["Buffer Local SQLite <br/> (Respaldo)"]:::edge
    end

    %% ZONA 3: IT (Servidor)
    subgraph Corporate_IT ["ZONA IT: Servidor Central"]

        Firewall("Firewall Corporativo <br/> Puerto 443 Abierto"):::it

        %% El Monolito IDH
        subgraph IDH_Server ["Contenedor Docker (IDH)"]
            API["IDH API (Infrastructure/API)"]:::it
            Security["Core Security (mTLS/OAuth2)"]:::it
            Worker["Features Worker (Background)"]:::it
        end

        %% Base de Datos
        subgraph Data_Layer ["PostgreSQL 15.15+"]
            RawDB[("Schema: raw_data <br/> (Forensic JSONB)")]:::db
            DomainDB[("Schema: public <br/> (Relacional)")]:::db
        end
    end

    %% FLUJO
    PLC1 -->|"Red Local (Insegura)"| Collector
    PLC2 -->|"Red Local (Insegura)"| Collector
    Collector -.->|"Offline"| Buffer

    %% Interconexión Clave
    Collector ==>|"HTTPS (Solo Salida)"| Firewall
    Firewall ==> API

    API -->|"Ingesta"| RawDB
    API -.->|"Trigger"| Worker
    Worker -->|"Proceso"| DomainDB
    Worker -->|"Lectura"| RawDB

    linkStyle 3,4,5 stroke:#bf360c,stroke-width:2px;
    linkStyle 7,8 stroke:#0277bd,stroke-width:4px;

```

### B. Diagrama Lógico: Flujo de Software y Capas

```mermaid
graph TD
    %% ESTILOS
    classDef external fill:#f9f9f9,stroke:#333,stroke-width:2px,color:black;
    classDef infra fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:black;
    classDef app fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:black;
    classDef domain fill:#fce4ec,stroke:#880e4f,stroke-width:3px,color:black;
    classDef db fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,stroke-dasharray: 5 5,color:black;

    %% 1. FUENTES EXTERNAS (Driving Side)
    subgraph Sources ["Fuentes de Datos"]
        Edge["Edge Gateway <br/>(JSON Push)"]:::external
        SAP_BTP["SAP Integration Suite <br/>(JSON Push)"]:::external
        SAP_Legacy["SAP ERP IDoc <br/>(XML Push)"]:::external
        SAP_OData["SAP S/4 OData <br/>(Pull Request)"]:::external
    end

    %% 2. EL SISTEMA (Monolito IDH)
    subgraph IDH ["Industrial Data Harmonizer - Monolito"]

        %% CAPA DE INFRAESTRUCTURA (ENTRADA)
        subgraph Infra_In ["Capa: Infrastructure"]
            API["FastAPI setup <br/>(Global Routers)"]:::infra
            Persistence["Persistence <br/>(DB Session management)"]:::infra
        end

        %% CAPA DE CORE Y FEATURES
        subgraph Business_Logic ["Capa: Core & Features"]
            Core["Core Domain <br/>(Transversal/Security)"]:::domain
            Feature_Ing["Feature: Ingestion <br/>(OT Capture)"]:::app
            Feature_Prod["Feature: Production <br/>(SAP Sync)"]:::app
        end

    end

    %% 3. PERSISTENCIA
    subgraph Database ["PostgreSQL 15"]
        RawDB[("Schema: raw_data <br/> (Todo es JSONB)")]:::db
        DomainDB[("Schema: public")]:::db
    end

    %% --- FLUJOS DE ENTRADA ---

    %% Flujo 1: JSON Nativo (Edge & SAP BTP)
    Edge --> API
    SAP_BTP --> API
    API -->|"#1: Insertar JSON"| RawDB

    %% Flujo 2: XML Legacy (IDocs)
    SAP_Legacy --> API_XML
    API_XML --> XML_Adapter
    XML_Adapter -->|"#1: Insertar (Convertido a JSON)"| RawDB

    %% Flujo 3: OData Pull
    Scheduler -->|"Trigger"| ODataClient
    ODataClient -->|"GET /Data"| SAP_OData
    SAP_OData -->|"Respuesta JSON"| ODataClient
    ODataClient -->|"#1: Insertar JSON"| RawDB

    %% --- FLUJO INTERNO COMÚN ---
    RawDB -.->|"#2: Notificar Nuevo Evento"| Queue
    Queue --> ETL
    ETL -->|"#3: Leer Raw"| RawDB
    ETL -->|"#4: Validar DDD"| Model
    ETL -->|"#5: Persistir Limpio"| DomainDB
```

## 6. Alcance y Restricciones del MVP

Para garantizar el éxito del piloto y la seguridad operativa, se definen límites estrictos:

*   **Solo Lectura ("Read-Only"):** El sistema NO enviará comandos de escritura a los PLCs (no Start/Stop).
*   **Sin IA/ML:** En esta fase no se implementan modelos predictivos; el foco es la ingeniería de datos determinista.
*   **Sin WMS:** No se gestiona inventario físico ni ubicaciones de almacén.
*   **Web Responsive:** No hay App nativa, solo PWA accesible vía navegador.

## 7. Gestión de Configuración (12-Factor App)

Siguiendo la metodología **12-Factor App**, la configuración del entorno se desacopla estrictamente del código fuente.

* **Herramienta: Pydantic Settings**
    * **Enfoque:** Centralización de todas las variables de entorno (`.env`) en clases de configuración estrictamente tipadas.
    * **Fail Fast:** El sistema valida la existencia y el formato correcto de las credenciales al arranque. Si algo falla, aborta inmediatamente.
