import os
import ssl
import sys
from typing import Any

import uvicorn

from idh.infrastructure.config import get_settings


def run_server():
    settings = get_settings()

    config_params = {
        "app": "idh.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
    }

    if settings.mtls_enabled:
        print("🚀 Starting server with mTLS enabled...")

        # Verificar que los archivos existen
        mtls_paths = [
            settings.mtls_ca_path,
            settings.mtls_cert_path,
            settings.mtls_key_path,
        ]
        for path in mtls_paths:
            if not path or not os.path.exists(path):
                print(f"❌ Error: El archivo {path} no existe.")
                sys.exit(1)

        update_params: dict[str, Any] = {
            "ssl_keyfile": settings.mtls_key_path,
            "ssl_certfile": settings.mtls_cert_path,
            "ssl_ca_certs": settings.mtls_ca_path,
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
        }
        config_params.update(update_params)
    else:
        print("🚀 Starting server in standard HTTP mode...")

    uvicorn.run(**config_params)


if __name__ == "__main__":
    run_server()
