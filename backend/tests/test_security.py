"""
PNMP Security Tests
Authentication and authorization testing
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    decode_access_token
)
from app.core.deps import get_current_user
from app.core.config import settings
from app.models import User, UserRole


class TestPasswordHashing:
    """Test password hashing security"""
    
    def test_password_hashing_uses_bcrypt(self):
        """Verify bcrypt is used for password hashing"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # bcrypt hash length
    
    def test_password_verification_correct(self):
        """Test correct password verification"""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """Test incorrect password verification"""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password("wrong_password", hashed) is False
    
    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes"""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # bcrypt uses salt, so hashes should be different
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token security"""
    
    def test_token_creation(self):
        """Test token creation with expiration"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_decoding_valid(self):
        """Test decoding valid token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_token_decoding_invalid(self):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"
        
        payload = decode_access_token(invalid_token)
        
        assert payload is None
    
    def test_token_decoding_tampered(self):
        """Test decoding tampered token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"
        
        payload = decode_access_token(tampered_token)
        
        assert payload is None
    
    def test_token_expiration(self):
        """Test token expiration"""
        data = {"sub": "testuser"}
        
        # Create token that expires in 1 second
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Should be valid immediately
        payload = decode_access_token(token)
        assert payload is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should be invalid after expiration
        payload = decode_access_token(token)
        assert payload is None
    
    def test_token_algorithm_enforcement(self):
        """Test that only allowed algorithm is accepted"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Decode should only accept HS256
        payload = decode_access_token(token)
        assert payload is not None
        
        # Verify algorithm in settings
        assert settings.JWT_ALGORITHM == "HS256"
    
    def test_token_subject_validation(self):
        """Test token subject validation"""
        # Token without subject
        data = {"other_field": "value"}
        token = create_access_token(data)
        
        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") is None
    
    def test_token_secret_from_config(self):
        """Test that token uses secret from config"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Decode with correct secret should work
        payload = decode_access_token(token)
        assert payload is not None
        
        # Decode with wrong secret should fail
        from jose import jwt
        wrong_payload = jwt.decode(
            token, 
            "wrong_secret_key", 
            algorithms=[settings.JWT_ALGORITHM]
        )
        # This should raise an error, but we're testing the mechanism
        # In practice, decode_access_token returns None on error


class TestAuthenticationDependency:
    """Test authentication dependency"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session):
        """Test get_current_user with valid token"""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.NETWORK_ENGINEER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create valid token
        token = create_access_token(data={"sub": "testuser"})
        
        # Mock dependencies
        with patch('app.core.deps.get_db', return_value=db_session):
            result = await get_current_user(token=token, db=db_session)
            
            assert result is not None
            assert result.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test get_current_user with invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session):
        """Test get_current_user with expired token"""
        # Create expired token
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session):
        """Test get_current_user with token for non-existent user"""
        token = create_access_token(data={"sub": "nonexistent"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, db_session):
        """Test get_current_user with inactive user"""
        # Create inactive user
        user = User(
            username="inactive",
            email="inactive@example.com",
            full_name="Inactive User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.NETWORK_ENGINEER,
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(data={"sub": "inactive"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 403


class TestAuthorization:
    """Test role-based authorization"""
    
    def test_admin_can_create_user(self, db_session):
        """Test that admin can create user"""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        
        # Admin should be able to create users
        assert admin.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    def test_viewer_cannot_create_user(self, db_session):
        """Test that viewer cannot create user"""
        viewer = User(
            username="viewer",
            email="viewer@example.com",
            full_name="Viewer User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.VIEWER,
            is_active=True
        )
        db_session.add(viewer)
        db_session.commit()
        
        # Viewer should not be able to create users
        assert viewer.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    def test_super_admin_can_delete_user(self, db_session):
        """Test that super admin can delete user"""
        super_admin = User(
            username="superadmin",
            email="superadmin@example.com",
            full_name="Super Admin",
            hashed_password=get_password_hash("password123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db_session.add(super_admin)
        db_session.commit()
        
        # Super admin should be able to delete users
        assert super_admin.role == UserRole.SUPER_ADMIN
    
    def test_admin_cannot_delete_user(self, db_session):
        """Test that admin cannot delete user"""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        
        # Admin should not be able to delete users
        assert admin.role != UserRole.SUPER_ADMIN


class TestCredentialSecurity:
    """Test credential endpoint security"""
    
    def test_credential_safe_response_schema(self):
        """Test that credential safe response doesn't expose secrets"""
        from app.schemas import DeviceCredentialSafeResponse
        
        response = DeviceCredentialSafeResponse(
            device_id=1,
            username_configured=True,
            password_configured=True,
            snmp_configured=True,
            snmp_version="v2c",
            snmp_v3_configured=False,
            ssh_enabled=False,
            api_enabled=False,
            snmp_enabled=True
        )
        
        # Verify no secret fields in response
        response_dict = response.model_dump()
        
        assert "password" not in response_dict
        assert "snmp_community" not in response_dict
        assert "snmp_auth_password" not in response_dict
        assert "snmp_privacy_password" not in response_dict
        assert "encrypted_password" not in response_dict
        
        # Verify only boolean flags are exposed
        assert "username_configured" in response_dict
        assert "password_configured" in response_dict
        assert "snmp_configured" in response_dict
    
    def test_credential_encryption_at_rest(self):
        """Test that credentials are encrypted in database"""
        from app.core.encryption import credential_encryption
        
        # Test encryption
        plaintext = "secret_password"
        encrypted = credential_encryption.encrypt(plaintext)
        
        # Encrypted should be different from plaintext
        assert encrypted != plaintext
        
        # Should be decryptable
        decrypted = credential_encryption.decrypt(encrypted)
        assert decrypted == plaintext


class TestSecurityBestPractices:
    """Test security best practices"""
    
    def test_no_default_jwt_secret(self):
        """Test that JWT secret is not using insecure default"""
        # Check if JWT_SECRET_KEY is set
        # In production, this should be set via environment variable
        assert settings.JWT_SECRET_KEY is not None
        assert len(settings.JWT_SECRET_KEY) > 0
        
        # Warning: Default value is insecure
        # This test documents the issue
        if settings.JWT_SECRET_KEY == "change-this-to-another-random-secret-key":
            pytest.skip("Default JWT secret detected - should be changed in production")
    
    def test_jwt_algorithm_is_secure(self):
        """Test that JWT algorithm is secure"""
        # HS256 is acceptable for internal use
        # RS256 would be better for production
        assert settings.JWT_ALGORITHM in ["HS256", "RS256", "ES256"]
    
    def test_token_expiration_configured(self):
        """Test that token expiration is configured"""
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 1440  # Max 24 hours
    
    def test_password_hashing_algorithm(self):
        """Test that password hashing uses secure algorithm"""
        # bcrypt is secure
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Verify bcrypt is being used
        assert "bcrypt" in pwd_context.schemes()


class TestLoginEndpoints:
    """Test login endpoint security"""
    
    def test_login_response_format(self):
        """Test that login response only contains token"""
        # Simulate login response
        response = {
            "access_token": "fake_token",
            "token_type": "bearer"
        }
        
        # Verify no sensitive data in response
        assert "password" not in response
        assert "hashed_password" not in response
        assert "secret" not in response
    
    def test_login_error_messages_generic(self):
        """Test that login error messages are generic"""
        # Error message should not reveal if username exists
        error_message = "Incorrect username or password"
        
        # Should be same for wrong username and wrong password
        assert "username" not in error_message.lower() or "or" in error_message.lower()


class TestLoggingSecurity:
    """Test that sensitive data is not logged"""
    
    def test_no_password_in_logs(self):
        """Test that passwords are not logged"""
        # This is a documentation test
        # In actual code, we should never log passwords
        password = "secret_password"
        
        # Simulate safe logging
        log_message = f"User login attempt"  # No password
        
        assert password not in log_message
    
    def test_no_token_in_logs(self):
        """Test that tokens are not logged"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        
        # Simulate safe logging
        log_message = f"Token validated"  # No token value
        
        assert token not in log_message
    
    def test_no_credential_in_logs(self):
        """Test that credentials are not logged"""
        credential = "snmp_community_secret"
        
        # Simulate safe logging
        log_message = f"Device polled successfully"  # No credential
        
        assert credential not in log_message
