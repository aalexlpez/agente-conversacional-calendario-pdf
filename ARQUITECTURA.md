# Arquitectura del Agente Conversacional

Este documento describe la arquitectura general del proyecto, incluyendo un diagrama visual (ASCII) y diagramas Mermaid para comprender la solución y sus conexiones.

## Diagrama Visual (ASCII) — Capas y Conexiones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   API Layer                                 │
│  FastAPI REST + WebSocket                                                   │
│  - auth.py (JWT login)                                                      │
│  - conversations.py (CRUD conversaciones)                                   │
│  - documents.py (upload/query PDF)                                          │
│  - websocket.py (chat streaming)                                            │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │ Depends / Inyección
┌───────────────▼─────────────────────────────────────────────────────────────┐
│                             Application Layer                               │
│  - SendMessageUseCase (orquestador)                                         │
│  - ConversationUseCase / DocumentUseCase / EventUseCase                     │
│  - AuthLoginUseCase                                                         │
│  - ConversationManager (concurrencia & estado activo)                       │
│  - NotificationManager (finalización de respuesta)                          │
└───────────┬──────────────────────────┬──────────────────────────────────────┘
            │                          │
            │                          │
┌───────────▼───────────┐  ┌───────────▼─────────────────────────────────────┐
│  Infrastructure Layer │  │                 Tools (Plugins)                 │
│  - InMemoryStore      │  │  - ToolRegistry                                 │
│  - AIService (LLM)    │  │  - PDFTool (pdfminer.six)                       │
│  - AuthService        │  │  - GoogleCalendarTool (Google API)              │
│  - JWT Service        │  │                                                 │
└───────────┬───────────┘  └───────────┬─────────────────────────────────────┘
            │                          │
            │                          │
┌───────────▼────────────────────────────────────────────────────────────────┐
│                               Domain Layer                                 │
│  - Entities (User, Conversation, Message, Event, Document)                 │
│  - Interfaces (Protocols)                                                  │
│  - Exceptions (DomainError, ResourceNotFound, etc.)                        │
└────────────────────────────────────────────────────────────────────────────┘
            │
            │ Integraciones externas
┌───────────▼────────────────────────────────────────────────────────────────┐
│  External Services                                                         │
│  - APIFreeLLM / Groq                                                       │
│  - Google Calendar API                                                     │
└────────────────────────────────────────────────────────────────────────────┘
```