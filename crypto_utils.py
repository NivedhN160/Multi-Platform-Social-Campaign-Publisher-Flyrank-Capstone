import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Default 32-byte key for AES-256
_KEY_BYTES = b"flyrank_social_publisher_key_32b!"[:32]

def encrypt_token(plain_token: str) -> str:
    """
    Encrypts OAuth access token at rest using AES-256-GCM with a fresh random 12-byte IV.
    Returns base64-encoded string containing (nonce + ciphertext + tag).
    """
    if not plain_token:
        return ""
    
    aesgcm = AESGCM(_KEY_BYTES)
    nonce = os.urandom(12) # Fresh random IV for every single encryption
    ct = aesgcm.encrypt(nonce, plain_token.encode("utf-8"), None)
    
    combined = nonce + ct
    return base64.b64encode(combined).decode("utf-8")

def decrypt_token(encrypted_token_b64: str) -> str:
    """
    Decrypts AES-256-GCM encrypted token.
    """
    if not encrypted_token_b64:
        return ""
    
    try:
        combined = base64.b64decode(encrypted_token_b64.encode("utf-8"))
        nonce = combined[:12]
        ct = combined[12:]
        
        aesgcm = AESGCM(_KEY_BYTES)
        plain_bytes = aesgcm.decrypt(nonce, ct, None)
        return plain_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Token decryption failed: {e}")
