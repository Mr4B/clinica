# app/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
import os

class FieldEncryption:
    def __init__(self):
        # In produzione, carica da variabile d'ambiente o vault (es. HashiCorp Vault)
        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)
    
    def _get_or_create_key(self) -> bytes:
        """Ottieni chiave da env o genera (NON fare in prod, usa un vault!)"""
        key_str = os.getenv("ENCRYPTION_KEY")
        if key_str:
            return key_str.encode()
        
        # SOLO PER DEV - In produzione usa un key management service
        password = os.getenv("MASTER_PASSWORD", "change-me-in-production").encode()
        salt = os.getenv("ENCRYPTION_SALT", "fixed-salt-change-me").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_dict(self, data: dict) -> str:
        """Critta un dizionario e ritorna base64 string"""
        json_str = json.dumps(data, ensure_ascii=False, default=str)
        encrypted = self._fernet.encrypt(json_str.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_dict(self, encrypted_str: str) -> dict:
        """Decritta una stringa base64 e ritorna dizionario"""
        encrypted = base64.b64decode(encrypted_str.encode('utf-8'))
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode('utf-8'))
    
    def encrypt_str(self, data: str) -> str:
        """Critta una stringa e ritorna base64 string"""
        encrypted = self._fernet.encrypt(data.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_str(self, encrypted_str: str) -> str:
        """Decritta una stringa base64 e ritorna dizionario"""
        encrypted = base64.b64decode(encrypted_str.encode('utf-8'))
        decrypted = self._fernet.decrypt(encrypted)
        return decrypted.decode('utf-8')

# Singleton
field_encryption = FieldEncryption()