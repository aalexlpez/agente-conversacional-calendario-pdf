
"""
Archivo principal de la aplicación FastAPI para el agente conversacional.

Inicializa la instancia de FastAPI, configura CORS y registra todos los routers de la API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, conversations, events, documents, websocket


# Instancia principal de la aplicación FastAPI.
app = FastAPI(title="Agente Conversacional IA")


# Registro de routers para los diferentes módulos de la API.
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(events.router)
app.include_router(documents.router)
app.include_router(websocket.router)


# Configuración de CORS para permitir acceso desde cualquier origen (útil para desarrollo y pruebas).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
