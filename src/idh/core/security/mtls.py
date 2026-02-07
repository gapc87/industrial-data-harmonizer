"""
Extracción de identidad desde certificados mTLS.

Soporta tanto conexiones SSL directas como headers XFCC de proxies inversos.
"""

import re
from typing import Any

from fastapi import Request


def extract_certificate_identity(request: Request) -> str | None:
    """
    Extrae la identidad del gateway (CN) desde el certificado del cliente.
    Soporta tanto conexiones directas (SSL en transporte) como headers de proxy (XFCC).
    """
    xfcc = request.headers.get("x-forwarded-client-cert")
    if xfcc:
        match = re.search(r"CN\s*=\s*([^,;\"]+)", xfcc, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    ssl_object: Any = None

    if "extensions" in request.scope and "ssl" in request.scope["extensions"]:
        ssl_object = request.scope["extensions"]["ssl"]

    if not ssl_object and "transport" in request.scope:
        transport = request.scope["transport"]
        if hasattr(transport, "get_extra_info"):
            ssl_object = transport.get_extra_info("ssl_object")

    if ssl_object:
        try:
            cert = ssl_object.getpeercert()
            if cert:
                for section in cert.get("subject", ()):
                    for item in section:
                        if item[0] == "commonName":
                            return str(item[1])
        except (AttributeError, ValueError, IndexError, TypeError):
            pass

    return None
