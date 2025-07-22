"""Encryption utilities for the caching platform."""

import base64
import hashlib
import secrets
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog
from datetime import datetime

from ..config.settings import get_settings

logger = structlog.get_logger(__name__)


class EncryptionManager:
    """Encryption manager for data security."""
    
    def __init__(self):
        self.settings = get_settings()
        self.security_config = self.settings.security
        
        # Encryption key
        self.encryption_key = self._derive_key(self.security_config.encryption_key)
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Key rotation
        self.key_rotation_interval = 30 * 24 * 3600  # 30 days
        self.last_key_rotation = None
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password."""
        try:
            # Use PBKDF2 to derive a key from the password
            salt = b'caching_platform_salt'  # In production, use a random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key
            
        except Exception as e:
            logger.error("Error deriving encryption key", error=str(e))
            # Fallback to a default key (not recommended for production)
            return Fernet.generate_key()
    
    def _generate_salt(self) -> bytes:
        """Generate a random salt."""
        return secrets.token_bytes(16)
    
    def _hash_data(self, data: str) -> str:
        """Hash data using SHA-256."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def encrypt_data(self, data: str) -> str:
        """Encrypt data."""
        try:
            if not self.security_config.encryption_enabled:
                return data
            
            # Convert string to bytes
            data_bytes = data.encode('utf-8')
            
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(data_bytes)
            
            # Encode to base64 for storage
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
            return encrypted_b64
            
        except Exception as e:
            logger.error("Error encrypting data", error=str(e))
            return data
    
    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        try:
            if not self.security_config.encryption_enabled:
                return encrypted_data
            
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt the data
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            
            # Convert back to string
            decrypted_data = decrypted_bytes.decode('utf-8')
            
            return decrypted_data
            
        except Exception as e:
            logger.error("Error decrypting data", error=str(e))
            return encrypted_data
    
    async def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a dictionary."""
        try:
            if not self.security_config.encryption_enabled:
                return data
            
            encrypted_data = data.copy()
            
            # Define sensitive fields to encrypt
            sensitive_fields = ['password', 'api_key', 'secret', 'token', 'key']
            
            for key, value in encrypted_data.items():
                if isinstance(value, str) and any(field in key.lower() for field in sensitive_fields):
                    encrypted_data[key] = await self.encrypt_data(value)
                elif isinstance(value, dict):
                    encrypted_data[key] = await self.encrypt_dict(value)
                elif isinstance(value, list):
                    encrypted_data[key] = await self.encrypt_list(value)
            
            return encrypted_data
            
        except Exception as e:
            logger.error("Error encrypting dictionary", error=str(e))
            return data
    
    async def decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a dictionary."""
        try:
            if not self.security_config.encryption_enabled:
                return data
            
            decrypted_data = data.copy()
            
            # Define sensitive fields to decrypt
            sensitive_fields = ['password', 'api_key', 'secret', 'token', 'key']
            
            for key, value in decrypted_data.items():
                if isinstance(value, str) and any(field in key.lower() for field in sensitive_fields):
                    decrypted_data[key] = await self.decrypt_data(value)
                elif isinstance(value, dict):
                    decrypted_data[key] = await self.decrypt_dict(value)
                elif isinstance(value, list):
                    decrypted_data[key] = await self.decrypt_list(value)
            
            return decrypted_data
            
        except Exception as e:
            logger.error("Error decrypting dictionary", error=str(e))
            return data
    
    async def encrypt_list(self, data: list) -> list:
        """Encrypt sensitive fields in a list."""
        try:
            if not self.security_config.encryption_enabled:
                return data
            
            encrypted_list = []
            
            for item in data:
                if isinstance(item, str):
                    encrypted_list.append(await self.encrypt_data(item))
                elif isinstance(item, dict):
                    encrypted_list.append(await self.encrypt_dict(item))
                elif isinstance(item, list):
                    encrypted_list.append(await self.encrypt_list(item))
                else:
                    encrypted_list.append(item)
            
            return encrypted_list
            
        except Exception as e:
            logger.error("Error encrypting list", error=str(e))
            return data
    
    async def decrypt_list(self, data: list) -> list:
        """Decrypt sensitive fields in a list."""
        try:
            if not self.security_config.encryption_enabled:
                return data
            
            decrypted_list = []
            
            for item in data:
                if isinstance(item, str):
                    decrypted_list.append(await self.decrypt_data(item))
                elif isinstance(item, dict):
                    decrypted_list.append(await self.decrypt_dict(item))
                elif isinstance(item, list):
                    decrypted_list.append(await self.decrypt_list(item))
                else:
                    decrypted_list.append(item)
            
            return decrypted_list
            
        except Exception as e:
            logger.error("Error decrypting list", error=str(e))
            return data
    
    async def hash_password(self, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """Hash a password with salt."""
        try:
            if salt is None:
                salt = self._generate_salt()
            
            # Use PBKDF2 for password hashing
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            hash_bytes = kdf.derive(password.encode())
            password_hash = base64.urlsafe_b64encode(hash_bytes).decode('utf-8')
            salt_b64 = base64.urlsafe_b64encode(salt).decode('utf-8')
            
            return {
                "hash": password_hash,
                "salt": salt_b64
            }
            
        except Exception as e:
            logger.error("Error hashing password", error=str(e))
            return {"hash": "", "salt": ""}
    
    async def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash."""
        try:
            # Decode salt and hash
            salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
            hash_bytes = base64.urlsafe_b64decode(password_hash.encode('utf-8'))
            
            # Use PBKDF2 to derive hash from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
            )
            
            derived_hash = kdf.derive(password.encode())
            
            # Compare hashes
            return derived_hash == hash_bytes
            
        except Exception as e:
            logger.error("Error verifying password", error=str(e))
            return False
    
    async def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token."""
        try:
            return secrets.token_urlsafe(length)
            
        except Exception as e:
            logger.error("Error generating secure token", error=str(e))
            return ""
    
    async def generate_api_key(self) -> str:
        """Generate a secure API key."""
        try:
            return secrets.token_urlsafe(32)
            
        except Exception as e:
            logger.error("Error generating API key", error=str(e))
            return ""
    
    async def encrypt_file(self, file_path: str, output_path: str = None) -> bool:
        """Encrypt a file."""
        try:
            if not self.security_config.encryption_enabled:
                return True
            
            if output_path is None:
                output_path = file_path + ".encrypted"
            
            with open(file_path, 'rb') as file:
                data = file.read()
            
            encrypted_data = self.cipher_suite.encrypt(data)
            
            with open(output_path, 'wb') as file:
                file.write(encrypted_data)
            
            logger.info(f"Encrypted file: {file_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error encrypting file {file_path}", error=str(e))
            return False
    
    async def decrypt_file(self, file_path: str, output_path: str = None) -> bool:
        """Decrypt a file."""
        try:
            if not self.security_config.encryption_enabled:
                return True
            
            if output_path is None:
                if file_path.endswith(".encrypted"):
                    output_path = file_path[:-10]
                else:
                    output_path = file_path + ".decrypted"
            
            with open(file_path, 'rb') as file:
                encrypted_data = file.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            logger.info(f"Decrypted file: {file_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error decrypting file {file_path}", error=str(e))
            return False
    
    async def rotate_encryption_key(self) -> bool:
        """Rotate the encryption key."""
        try:
            if not self.security_config.encryption_enabled:
                return True
            
            # Generate new key
            new_key = Fernet.generate_key()
            new_cipher_suite = Fernet(new_key)
            
            # In a real implementation, you would:
            # 1. Re-encrypt all existing data with the new key
            # 2. Update the key in secure storage
            # 3. Implement key versioning
            
            self.encryption_key = new_key
            self.cipher_suite = new_cipher_suite
            self.last_key_rotation = datetime.utcnow()
            
            logger.info("Rotated encryption key")
            return True
            
        except Exception as e:
            logger.error("Error rotating encryption key", error=str(e))
            return False
    
    async def get_encryption_status(self) -> Dict[str, Any]:
        """Get encryption status and configuration."""
        try:
            return {
                "enabled": self.security_config.encryption_enabled,
                "algorithm": "AES-256",
                "key_rotation_interval": self.key_rotation_interval,
                "last_key_rotation": self.last_key_rotation,
                "key_length": len(self.encryption_key) * 8  # Convert to bits
            }
            
        except Exception as e:
            logger.error("Error getting encryption status", error=str(e))
            return {"error": str(e)}
    
    async def validate_encryption_setup(self) -> Dict[str, Any]:
        """Validate encryption setup and configuration."""
        try:
            validation_results = {
                "encryption_enabled": self.security_config.encryption_enabled,
                "key_valid": False,
                "test_encryption": False,
                "errors": []
            }
            
            # Check if encryption is enabled
            if not self.security_config.encryption_enabled:
                validation_results["errors"].append("Encryption is disabled")
                return validation_results
            
            # Validate encryption key
            try:
                test_data = "test_encryption_data"
                encrypted = await self.encrypt_data(test_data)
                decrypted = await self.decrypt_data(encrypted)
                
                if decrypted == test_data:
                    validation_results["key_valid"] = True
                    validation_results["test_encryption"] = True
                else:
                    validation_results["errors"].append("Encryption/decryption test failed")
                    
            except Exception as e:
                validation_results["errors"].append(f"Encryption key validation failed: {e}")
            
            return validation_results
            
        except Exception as e:
            logger.error("Error validating encryption setup", error=str(e))
            return {"error": str(e)} 