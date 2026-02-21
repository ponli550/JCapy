# SPDX-License-Identifier: Apache-2.0
import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Use project-local cert directory instead of ~/.jcapy/certs due to permission issues on some systems
CERT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.jcapy_certs"))

def ensure_cert_dir():
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR, mode=0o700, exist_ok=True)

def generate_ca():
    """Generates a local Certificate Authority (CA)."""
    ensure_cert_dir()
    ca_key_path = os.path.join(CERT_DIR, "ca.key")
    ca_cert_path = os.path.join(CERT_DIR, "ca.crt")

    if os.path.exists(ca_key_path) and os.path.exists(ca_cert_path):
        return ca_key_path, ca_cert_path

    # Generate Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Generate CA Certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "JCapy Local CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "jcapy-ca"),
    ])

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # Write Private Key
    with open(ca_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Write Certificate
    with open(ca_cert_path, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    return ca_key_path, ca_cert_path

def generate_cert(name: str):
    """Generates and signs a certificate for a specific component (server/client)."""
    ensure_cert_dir()
    ca_key_path, ca_cert_path = generate_ca()

    key_path = os.path.join(CERT_DIR, f"{name}.key")
    cert_path = os.path.join(CERT_DIR, f"{name}.crt")

    if os.path.exists(key_path) and os.path.exists(cert_path):
        return key_path, cert_path

    # Load CA
    with open(ca_key_path, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    with open(ca_cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    # Generate Component Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Generate CSR/Certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"jcapy-{name}"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.DNSName("127.0.0.1")]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    # Write Key
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Write Certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return key_path, cert_path

def get_grpc_credentials(is_server: bool = False):
    """Returns gRPC SSL credentials for mTLS."""
    ca_path = os.path.join(CERT_DIR, "ca.crt")

    if is_server:
        key_path, cert_path = generate_cert("server")
        with open(ca_path, "rb") as f: ca_data = f.read()
        with open(key_path, "rb") as f: key_data = f.read()
        with open(cert_path, "rb") as f: cert_data = f.read()

        import grpc
        return grpc.ssl_server_credentials(
            [(key_data, cert_data)],
            root_certificates=ca_data,
            require_client_auth=True
        )
    else:
        key_path, cert_path = generate_cert("client")
        with open(ca_path, "rb") as f: ca_data = f.read()
        with open(key_path, "rb") as f: key_data = f.read()
        with open(cert_path, "rb") as f: cert_data = f.read()

        import grpc
        return grpc.ssl_channel_credentials(
            root_certificates=ca_data,
            private_key=key_data,
            certificate_chain=cert_data
        )
