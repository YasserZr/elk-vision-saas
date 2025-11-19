# High-Level Architecture: ELK Vision SaaS

This document outlines the high-level architecture for the ELK Vision SaaS platform, utilizing Django, the ELK Stack, MongoDB, Redis, Docker, and a React frontend.

## Architecture Diagram

```mermaid
graph TD
    %% Client Side
    subgraph Client_Layer [Client Layer]
        Browser[User Browser / React App]
        LogAgents[Log Agents / Beats]
    end

    %% Entry Point
    subgraph Entry_Layer [Entry & Load Balancing]
        LB[Nginx Load Balancer / Reverse Proxy]
    end

    %% Application Services
    subgraph App_Services [Application Services (Dockerized)]
        DjangoAPI[Django REST API]
        Celery[Celery Workers]
        Logstash[Logstash Ingestion]
    end

    %% Data & Messaging
    subgraph Data_Layer [Data & Storage]
        Redis[(Redis - Cache & Broker)]
        MongoDB[(MongoDB - Primary DB)]
        Elastic[(Elasticsearch - Log Store)]
    end

    %% Connections
    Browser -->|HTTPS / REST| LB
    LogAgents -->|TCP/UDP / Syslog| LB

    LB -->|API Traffic| DjangoAPI
    LB -->|Log Traffic| Logstash

    %% API Interactions
    DjangoAPI -->|Read/Write User Data| MongoDB
    DjangoAPI -->|Query Analytics| Elastic
    DjangoAPI -->|Cache / Session| Redis
    DjangoAPI -->|Async Tasks| Redis

    %% Async Processing
    Redis -->|Task Queue| Celery
    Celery -->|Update| MongoDB
    Celery -->|Alerting| DjangoAPI

    %% Log Pipeline
    Logstash -->|Buffer Logs| Redis
    Redis -->|Process Logs| Logstash
    Logstash -->|Index Logs| Elastic

    %% Styling
    classDef service fill:#f9f,stroke:#333,stroke-width:2px;
    classDef db fill:#ccf,stroke:#333,stroke-width:2px;
    classDef client fill:#ff9,stroke:#333,stroke-width:2px;
    
    class DjangoAPI,Celery,Logstash,LB service;
    class MongoDB,Elastic,Redis db;
    class Browser,LogAgents client;
```

## Component Breakdown

### 1. Client Layer
*   **Modern JS Frontend (React)**: A Single Page Application (SPA) that interacts with the backend via RESTful APIs. It handles data visualization (using libraries like Recharts or D3.js) and user interactions.
*   **Log Agents (Filebeat/Metricbeat)**: Lightweight shippers installed on client servers that forward logs to our ingestion endpoints.

### 2. Entry & Load Balancing
*   **Nginx**: Acts as the entry point, handling SSL termination, serving static assets (frontend build), and reverse proxying requests to the Django API or Logstash. It distributes traffic across multiple container instances for high availability.

### 3. Application Services (Docker Containers)
*   **Django REST API**: The core application logic.
    *   **Authentication**: Handles JWT generation and validation.
    *   **Tenant Management**: Logic to segregate user data.
    *   **Proxy**: Securely queries Elasticsearch to return analytics data to the frontend without exposing the ES cluster directly.
*   **Celery Workers**: Background processes for handling heavy tasks like generating reports, sending email alerts, or processing batch data updates.
*   **Logstash**: The processing pipeline. It receives logs, parses/enriches them (e.g., GeoIP lookup, Grok parsing), and indexes them into Elasticsearch.

### 4. Data & Storage Layer
*   **MongoDB**: The primary operational database.
    *   Stores User Profiles, Tenant Configurations, Saved Searches, Dashboard Layouts, and Alerting Rules.
    *   Chosen for its flexibility with JSON-like documents which maps well to frontend state.
*   **Elasticsearch**: The search and analytics engine.
    *   Stores the massive volume of ingested log data.
    *   Optimized for full-text search and time-series analytics.
*   **Redis**: Multi-purpose in-memory store.
    *   **Caching**: Caches frequent API responses and session data.
    *   **Message Broker**: Acts as the queue for Celery tasks.
    *   **Log Buffer**: Temporarily buffers incoming logs from Logstash to prevent data loss during spikes before they are indexed.

## Key Workflows

### Authentication Flow
1.  User logs in via React Frontend.
2.  Django validates credentials against MongoDB.
3.  Django issues a **JWT (JSON Web Token)**.
4.  Frontend stores the token and attaches it to subsequent API headers.

### Log Ingestion Pipeline
1.  **Collection**: Agents (Beats) send logs to the Nginx Load Balancer.
2.  **Buffering**: Logs are forwarded to Logstash, which pushes them into a **Redis List** (acting as a buffer).
3.  **Processing**: A separate Logstash pipeline consumes from Redis, parses the logs (extracting fields like timestamp, log level, service name), and filters noise.
4.  **Indexing**: Processed logs are sent to **Elasticsearch**.

### Search & Analytics Flow
1.  User executes a search on the Dashboard.
2.  React sends a request to Django API (e.g., `GET /api/logs?query=error`).
3.  Django validates the user's tenant permissions.
4.  Django constructs a secure Elasticsearch query (filtering by `tenant_id`).
5.  Elasticsearch returns aggregations and hits.
6.  Django formats the response and sends it back to the Frontend.

## Scalability & Infrastructure

*   **Docker & Orchestration**: All services are containerized. For production, **Kubernetes (K8s)** or **Docker Swarm** is used to manage replicas.
*   **Horizontal Scaling**:
    *   **Stateless Services**: Django API and Logstash instances can be scaled up/down based on CPU/Memory usage.
    *   **Database**: MongoDB can be deployed as a Replica Set for availability. Elasticsearch is deployed as a cluster with Master, Data, and Ingest nodes.
*   **Networking**:
    *   Services communicate over a private Docker network.
    *   Only Nginx ports (80/443) and Log ingestion ports are exposed publicly.

## Security Considerations

*   **Data Isolation**: Every log document in Elasticsearch is tagged with a `tenant_id`. API queries strictly enforce this filter.
*   **Encryption**: TLS/SSL for all data in transit (HTTPS for web, encrypted TCP for logs).
*   **Secrets Management**: Environment variables (via Docker Secrets or Vault) manage API keys and DB credentials.
