"""Configuración central de la aplicación.

Lee variables de entorno (o un archivo .env) para no exponer secretos en el
código. Incluye la configuración de Azure AI Foundry para el chatbot.
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Base de datos ---
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'tufinca.db'}"

    # --- API ---
    api_title: str = "TuFinca Pecuario API"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Azure AI Foundry (chatbot inteligente) ---
    # Si estas variables están vacías, el chatbot usa el motor de respaldo
    # basado en reglas (funciona sin credenciales de Azure).
    azure_openai_endpoint: str = ""       # https://<recurso>.openai.azure.com
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = ""     # nombre del despliegue del modelo
    azure_openai_api_version: str = "2024-10-21"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def azure_enabled(self) -> bool:
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_deployment
        )


settings = Settings()
