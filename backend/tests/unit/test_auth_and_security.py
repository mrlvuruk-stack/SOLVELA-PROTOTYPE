import pytest
from datetime import timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing_and_verification():
    """
    Test that bcrypt securely hashes passwords and verifies valid/invalid inputs.
    """
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 20
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_lifecycle():
    """
    Test JWT creation, claim encoding, and safe decoding.
    """
    user_payload = {"sub": "user-uuid-123", "email": "student@sovela.ai", "role": "student"}
    token = create_access_token(user_payload, expires_delta=timedelta(hours=1))
    
    assert isinstance(token, str)
    assert len(token) > 10
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-uuid-123"
    assert decoded["email"] == "student@sovela.ai"
    assert decoded["role"] == "student"

def test_invalid_jwt_token_handling():
    """
    Test that tampered or invalid JWT tokens return None safely without unhandled exception.
    """
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature"
    decoded = decode_access_token(invalid_token)
    assert decoded is None
