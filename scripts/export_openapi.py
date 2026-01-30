"""
Script para exportar el esquema OpenAPI a un archivo JSON.
Uso: uv run scripts/export_openapi.py
Requiere que las variables de entorno de configuración estén establecidas
(aunque sean dummies).
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from idh.main import app


def export_openapi():
    """Genera y guarda el archivo openapi.json en docs/."""
    try:
        print("Generando esquema OpenAPI...")
        openapi_content = app.openapi()

        output_path = Path("docs/openapi.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(openapi_content, f, indent=2)

        print(f"✅ Esquema exportado a: {output_path}")

    except Exception as e:
        print(f"❌ Error al exportar OpenAPI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    export_openapi()
