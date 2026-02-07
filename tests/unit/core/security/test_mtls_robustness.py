"""
Tests de robustez para extracción de identidad mTLS.
"""

from typing import Any, MutableMapping

import pytest
from fastapi import Request

from idh.core.security.mtls import extract_certificate_identity


def create_mock_request(xfcc_header: str | None = None) -> Request:
    """Crea un objeto Request mock con un header XFCC opcional."""
    scope: MutableMapping[str, Any] = {"type": "http", "headers": [], "extensions": {}}
    if xfcc_header:
        scope["headers"].append((b"x-forwarded-client-cert", xfcc_header.encode()))
    return Request(scope=scope)


@pytest.mark.parametrize(
    "header, expected_cn",
    [
        ('By=...;Hash=...;Subject="CN=gateway-001";URI=...', "gateway-001"),
        ('By=...;Subject="CN=Gateway 001";URI=...', "Gateway 001"),
        ("Subject=CN=no-quotes;URI=...", "no-quotes"),
        ('Subject="C=HU,CN=gateway-test,O=IDH";URI=...', "gateway-test"),
        ('Subject="CN=gateway-test;O=IDH";URI=...', "gateway-test"),
        ('Subject="CN=multiple.dots.test";URI=...', "multiple.dots.test"),
        ('Subject="cn=lowercase-cn";URI=...', "lowercase-cn"),
        ('Subject="CN = spaced-equals";URI=...', "spaced-equals"),
    ],
)
def test_extract_certificate_identity_xfcc_robustness(
    header: str, expected_cn: str
) -> None:
    """
    Verifica que la regex de XFCC sea robusta ante diferentes formatos de proxy. [P1]
    """
    request = create_mock_request(header)
    assert extract_certificate_identity(request) == expected_cn


def test_extract_certificate_identity_xfcc_no_cn() -> None:
    """Verifica que devuelve None si no hay CN en el header XFCC. [P2]"""
    header = 'By=...;Hash=...;Subject="O=IDH,C=HU";URI=...'
    request = create_mock_request(header)
    assert extract_certificate_identity(request) is None
