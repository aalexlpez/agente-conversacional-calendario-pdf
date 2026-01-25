"""FastAPI app principal para el agente conversacional."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, conversations, events, documents, websocket

app = FastAPI(title="Agente Conversacional IA")

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(events.router)
app.include_router(documents.router)
app.include_router(websocket.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
