"""
PNMP Encryption Service
Handles encryption/decryption of sensitive credentials using Fernet (AES-128-CBC)
"""
import base64
import os
from cryptography.fernet import Fernet, InvalidToken
from ..core.config import settings


class CredentialEncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


class CredentialEncryption:
    """
    Encrypts and decrypts device credentials using Fernet (AES).
    The encryption key is loaded from PNMP_ENCRYPTION_KEY environment variable.
    
    IMPORTANT: 
    - User passwords use bcrypt HASHING (one-way, via security.py)
    - Device credentials use Fernet ENCRYPTION (two-way, needed for monitoring)
    """
    
    _instance = None
    _fernet = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_fernet()
        return cls._instance
    
    def _init_fernet(self):
        """Initialize Fernet with encryption key from environment"""
        key = settings.PNMP_ENCRYPTION_KEY
        
        if not key:
            # Generate a key for development if not set
            # WARNING: This means credentials won't survive restarts in dev!
            if settings.APP_ENV == "development":
                key = Fernet.generate_key().decode()
                # In production, this would be an error
            else:
                raise CredentialEncryptionError(
                    "PNMP_ENCRYPTION_KEY not set. "
                    "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
        
        # Ensure key is properly formatted for Fernet
        try:
            # If key is already a valid Fernet key, use it directly
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except (ValueError, Exception):
            # Try to derive a Fernet key from the provided key
            try:
                # Pad or hash the key to 32 bytes, then base64 encode
                key_bytes = key.encode() if isinstance(key, str) else key
                # Use first 32 bytes
                key_bytes = key_bytes[:32].ljust(32, b'\0')
                fernet_key = base64.urlsafe_b64encode(key_bytes)
                self._fernet = Fernet(fernet_key)
            except Exception as e:
                raise CredentialEncryptionError(f"Invalid encryption key: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        Returns base64-encoded encrypted string.
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            raise CredentialEncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.
        Returns the original plaintext.
        """
        if not encrypted_text:
            return ""
        
        try:
            decrypted = self._fernet.decrypt(encrypted_text.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise CredentialEncryptionError(
                "Decryption failed. The encryption key may have changed."
            )
        except Exception as e:
            raise CredentialEncryptionError(f"Decryption failed: {e}")
    
    def is_configured(self) -> bool:
        """Check if encryption is properly configured"""
        return self._fernet is not None


# Singleton instance
credential_encryption = CredentialEncryption()
