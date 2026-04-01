import pyotp
import secrets


def generate_otp_secret() -> str:
    return pyotp.random_base32()


def generate_otp(secret: str) -> str:
    totp = pyotp.TOTP(secret, interval=300)  # 5 minutos
    return totp.now()


def verify_otp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret, interval=300)
    return totp.verify(code, valid_window=1)  # Permite 1 janela de tolerância


def generate_numeric_otp(length: int = 6) -> str:
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
