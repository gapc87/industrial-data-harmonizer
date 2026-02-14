"""
Generador de certificados de prueba para mTLS.

Crea una CA y certificados cliente/servidor para tests locales.
"""

import os
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from idh.infrastructure.config import get_settings


def generate_certs(output_dir: str | None = None) -> None:
    settings = get_settings()
    if output_dir is None:
        if settings.mtls_cert_path:
            output_dir = os.path.dirname(settings.mtls_cert_path)
        else:
            output_dir = "./certs"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "IDH Test CA"),
        ]
    )
    now = datetime.now(timezone.utc)
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    ee_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ee_name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "gateway-001"),
        ]
    )
    ee_cert = (
        x509.CertificateBuilder()
        .subject_name(ee_name)
        .issuer_name(ca_name)
        .public_key(ee_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    with open(os.path.join(output_dir, "ca.crt"), "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    with open(os.path.join(output_dir, "client.crt"), "wb") as f:
        f.write(ee_cert.public_bytes(serialization.Encoding.PEM))

    with open(os.path.join(output_dir, "client.key"), "wb") as f:
        f.write(
            ee_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(os.path.join(output_dir, "server.crt"), "wb") as f:
        f.write(ee_cert.public_bytes(serialization.Encoding.PEM))

    with open(os.path.join(output_dir, "server.key"), "wb") as f:
        f.write(
            ee_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    print(f"Certificados generados en {output_dir}")


if __name__ == "__main__":
    generate_certs()
