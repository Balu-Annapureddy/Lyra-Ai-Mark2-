"""
Secure Secrets Manager
Handles API keys and sensitive data using OS keyring
Never stores secrets in plaintext
"""

import logging
import os
from typing import Optional, Dict, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import keyring (optional dependency)
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring not available, using encrypted fallback")

from cryptography.fernet import Fernet
from core.paths import get_config_dir
from core.errors import StateError


class SecretsManager:
    """
    Manages sensitive data (API keys, tokens) securely
    - Uses OS keyring when available (Windows Credential Manager, macOS Keychain, Linux Secret Service)
    - Falls back to encrypted local storage
    - Never stores plaintext secrets
    """
    
    SERVICE_NAME = "LyraAI"
    
    def __init__(self):
        """Initialize secrets manager"""
        self.use_keyring = KEYRING_AVAILABLE
        self._encryption_key_file = get_config_dir() / ".secret_key"
        self._secrets_file = get_config_dir() / "secrets.enc"
        
        # Initialize encryption key for fallback
        if not self.use_keyring:
            self._ensure_encryption_key()
        
        logger.info(f"SecretsManager initialized (keyring={'available' if self.use_keyring else 'unavailable'})")
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists for fallback mode"""
        if not self._encryption_key_file.exists():
            # Generate new key
            key = Fernet.generate_key()
            
            # Save with restricted permissions
            self._encryption_key_file.write_bytes(key)
            
            # Set file permissions (owner read/write only)
            if os.name != 'nt':  # Unix-like systems
                os.chmod(self._encryption_key_file, 0o600)
            
            logger.info("Generated new encryption key")
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key for fallback mode"""
        if not self._encryption_key_file.exists():
            self._ensure_encryption_key()
        
        return self._encryption_key_file.read_bytes()
    
    def set_secret(self, key: str, value: str):
        """
        Store secret securely
        
        Args:
            key: Secret identifier (e.g., "openai_api_key")
            value: Secret value
        """
        if self.use_keyring:
            # Use OS keyring
            try:
                keyring.set_password(self.SERVICE_NAME, key, value)
                logger.info(f"Secret stored in keyring: {key}")
            except Exception as e:
                logger.error(f"Failed to store in keyring: {e}")
                self._set_secret_encrypted(key, value)
        else:
            # Use encrypted file
            self._set_secret_encrypted(key, value)
    
    def _set_secret_encrypted(self, key: str, value: str):
        """Store secret in encrypted file (fallback)"""
        # Load existing secrets
        secrets = self._load_encrypted_secrets()
        
        # Add/update secret
        secrets[key] = value
        
        # Encrypt and save
        encryption_key = self._get_encryption_key()
        fernet = Fernet(encryption_key)
        
        encrypted_data = fernet.encrypt(json.dumps(secrets).encode())
        self._secrets_file.write_bytes(encrypted_data)
        
        # Set file permissions
        if os.name != 'nt':
            os.chmod(self._secrets_file, 0o600)
        
        logger.info(f"Secret stored encrypted: {key}")
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieve secret
        
        Args:
            key: Secret identifier
        
        Returns:
            Secret value or None if not found
        """
        if self.use_keyring:
            # Try OS keyring first
            try:
                value = keyring.get_password(self.SERVICE_NAME, key)
                if value:
                    return value
            except Exception as e:
                logger.error(f"Failed to retrieve from keyring: {e}")
            
            # Fallback to encrypted file
            return self._get_secret_encrypted(key)
        else:
            # Use encrypted file
            return self._get_secret_encrypted(key)
    
    def _get_secret_encrypted(self, key: str) -> Optional[str]:
        """Retrieve secret from encrypted file (fallback)"""
        secrets = self._load_encrypted_secrets()
        return secrets.get(key)
    
    def _load_encrypted_secrets(self) -> Dict[str, str]:
        """Load all secrets from encrypted file"""
        if not self._secrets_file.exists():
            return {}
        
        try:
            encryption_key = self._get_encryption_key()
            fernet = Fernet(encryption_key)
            
            encrypted_data = self._secrets_file.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load encrypted secrets: {e}")
            return {}
    
    def delete_secret(self, key: str):
        """
        Delete secret
        
        Args:
            key: Secret identifier
        """
        if self.use_keyring:
            try:
                keyring.delete_password(self.SERVICE_NAME, key)
                logger.info(f"Secret deleted from keyring: {key}")
            except Exception as e:
                logger.debug(f"Failed to delete from keyring: {e}")
            
            # Also delete from encrypted file
            self._delete_secret_encrypted(key)
        else:
            self._delete_secret_encrypted(key)
    
    def _delete_secret_encrypted(self, key: str):
        """Delete secret from encrypted file"""
        secrets = self._load_encrypted_secrets()
        
        if key in secrets:
            del secrets[key]
            
            # Re-encrypt and save
            encryption_key = self._get_encryption_key()
            fernet = Fernet(encryption_key)
            
            encrypted_data = fernet.encrypt(json.dumps(secrets).encode())
            self._secrets_file.write_bytes(encrypted_data)
            
            logger.info(f"Secret deleted from encrypted file: {key}")
    
    def list_secrets(self) -> list[str]:
        """
        List all secret keys (not values)
        
        Returns:
            List of secret identifiers
        """
        secrets = self._load_encrypted_secrets()
        return list(secrets.keys())
    
    def rotate_secret(self, key: str, new_value: str):
        """
        Rotate secret (update with new value)
        
        Args:
            key: Secret identifier
            new_value: New secret value
        """
        self.set_secret(key, new_value)
        logger.info(f"Secret rotated: {key}")
    
    def clear_all_secrets(self):
        """
        Clear all secrets (use with caution!)
        Useful for logout or reset
        """
        # Clear keyring
        if self.use_keyring:
            for key in self.list_secrets():
                try:
                    keyring.delete_password(self.SERVICE_NAME, key)
                except:
                    pass
        
        # Clear encrypted file
        if self._secrets_file.exists():
            self._secrets_file.unlink()
        
        logger.warning("All secrets cleared")


# Global secrets manager instance
_global_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _global_secrets_manager
    if _global_secrets_manager is None:
        _global_secrets_manager = SecretsManager()
    return _global_secrets_manager


if __name__ == "__main__":
    # Test secrets manager
    print("Testing Secrets Manager")
    print("=" * 50)
    
    mgr = SecretsManager()
    
    # Set secret
    mgr.set_secret("test_api_key", "sk-1234567890abcdef")
    print("Secret stored")
    
    # Get secret
    value = mgr.get_secret("test_api_key")
    print(f"Retrieved: {value}")
    
    # List secrets
    keys = mgr.list_secrets()
    print(f"Secrets: {keys}")
    
    # Rotate
    mgr.rotate_secret("test_api_key", "sk-new-key-9876")
    print("Secret rotated")
    
    # Delete
    mgr.delete_secret("test_api_key")
    print("Secret deleted")
    
    print("=" * 50)
