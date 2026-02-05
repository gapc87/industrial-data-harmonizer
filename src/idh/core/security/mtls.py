import re
from typing import Any

from fastapi import Request


def extract_certificate_identity(request: Request) -> str | None:
    """
    Extrae la identidad del gateway (CN) desde el certificado del cliente.
    Soporta tanto conexiones directas (SSL en transporte) como headers de proxy (XFCC).
    """
    # 1. Intentar desde Header X-Forwarded-Client-Cert (XFCC) - Común en Proxies/Ingress
    xfcc = request.headers.get("x-forwarded-client-cert")
    if xfcc:
        # Buscamos el CN en el Subject. El formato suele ser:
        # Subject="...CN=name..." o Subject=...CN=name...
        # Esta regex es más robusta para manejar delimitadores comunes (, o ;)
        # Permitimos espacios internos pero no delimitadores
        match = re.search(r"CN\s*=\s*([^,;\"]+)", xfcc, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # 2. Intentar desde el objeto SSL del transporte (Uvicorn directo)
    ssl_object: Any = None

    # Starlette/FastAPI Request.scope['extensions']['ssl'] es el estándar para ASGI TLS
    if "extensions" in request.scope and "ssl" in request.scope["extensions"]:
        ssl_object = request.scope["extensions"]["ssl"]

    # Fallback: Algunos servidores ASGI exponen el transport directamente en el scope
    if not ssl_object and "transport" in request.scope:
        transport = request.scope["transport"]
        if hasattr(transport, "get_extra_info"):
            ssl_object = transport.get_extra_info("ssl_object")

    if ssl_object:
        try:
            cert = ssl_object.getpeercert()
            if cert:
                # El formato de getpeercert() es una estructura de tuplas anidadas
                # ( ( ('commonName', 'gateway-001'), ), )
                for section in cert.get("subject", ()):
                    for item in section:
                        if item[0] == "commonName":
                            return str(item[1])
        except (AttributeError, ValueError, IndexError, TypeError):
            pass

    return None
