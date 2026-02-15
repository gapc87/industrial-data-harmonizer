"""Tests unitarios para extracción de identidad mTLS."""

from typing import Any, MutableMapping
from unittest.mock import MagicMock

from fastapi import Request

from idh.core.security.mtls import extract_certificate_identity


def test_extract_certificate_identity_from_header() -> None:
    """Verifica la extracción de identidad desde el header X-Forwarded-Client-Cert."""
    request = MagicMock(spec=Request)
    xfcc = 'Hash=xyz;Subject="CN=gateway-001";URI=...'
    request.headers = {"x-forwarded-client-cert": xfcc}

    identity = extract_certificate_identity(request)
    assert identity == "gateway-001"


def test_extract_certificate_identity_from_transport() -> None:
    """Verifica la extracción de identidad desde el objeto SSL del transporte."""
    scope: MutableMapping[str, Any] = {"type": "http", "headers": [], "extensions": {}}
    request = MagicMock(spec=Request)
    request.scope = scope
    request.headers = {}

    ssl_object = MagicMock()
    ssl_object.getpeercert.return_value = {
        "subject": ((("commonName", "gateway-002"),),)
    }

    scope["extensions"]["ssl"] = ssl_object

    identity = extract_certificate_identity(request)
    assert identity == "gateway-002"

    del scope["extensions"]["ssl"]
    transport = MagicMock()
    transport.get_extra_info.return_value = ssl_object
    scope["transport"] = transport

    identity = extract_certificate_identity(request)
    assert identity == "gateway-002"


def test_extract_certificate_identity_no_cert() -> None:
    """Verifica que devuelve None si no hay certificado."""
    request = MagicMock(spec=Request)
    request.headers = {}
    request.scope = {"type": "http", "extensions": {}}

    identity = extract_certificate_identity(request)
    assert identity is None
