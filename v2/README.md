# Zookout AI v2 Architecture

This repository folder contains the Version 2 architecture for Zookout AI. It is designed to support production-ready Clean Architecture, with clear separation of concerns and channel-specific adapters.

## Folder structure

- `agents/` - high-level orchestration agents and conversational actors
- `api/` - REST and HTTP API adapters for external integrations
- `auth/` - authentication, authorization, and identity management
- `database/` - persistence adapters, repositories, and database infrastructure
- `formatter/` - presentation adapters and response formatting utilities
- `parser/` - raw data ingestion and structured data parsing
- `search/` - search, ranking, and relevance engine components
- `services/` - business use cases, application services, and orchestration logic
- `telegram/` - Telegram bot adapter and channel-specific integration
- `instagram/` - Instagram channel adapter and automation integration
- `whatsapp/` - WhatsApp channel adapter and messaging integration
- `dashboard/` - admin dashboard and UI integration components
- `analytics/` - telemetry, reporting, and analytics instrumentation
- `models/` - domain entities, data transfer objects, and value objects
- `tests/` - unit, integration, and contract test skeletons
- `utils/` - shared utilities, helpers, and cross-cutting tools
- `config/` - environment configuration and settings loading
- `logs/` - logging configuration and log routing

## Design principles

- Clean Architecture: adapters and frameworks are separated from business rules.
- Dependency inversion: core domain and use cases depend on abstractions, not on external systems.
- Single responsibility: each folder owns a distinct slice of the application.
- Channel-first integration: Telegram, Instagram, and WhatsApp are isolated so new channels can be added without changing core logic.
- Production-readiness: configuration, logging, and environment patterns are scaffolding-ready.
