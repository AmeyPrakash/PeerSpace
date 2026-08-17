"""
PeerSpace Secure Passkey Verification Module
Implements bcrypt-based secure passkey comparison and utilities.
"""

import bcrypt
import os
from typing import Optional

def hash_passkey(passkey: str) -> str:
    """
    Hash a passkey using bcrypt with salt.
    
    Args:
        passkey: Plain text passkey to hash
        
    Returns:
        Bcrypt hashed passkey (can be stored securely)
    """
    if not passkey:
        raise ValueError("Passkey cannot be empty")
    
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(passkey.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_passkey(provided_passkey: str, stored_hash: str) -> bool:
    """
    Securely compare a provided passkey against a stored hash.
    Uses bcrypt's constant-time comparison to prevent timing attacks.
    
    Args:
        provided_passkey: The passkey provided by the user
        stored_hash: The bcrypt hash from environment/config
        
    Returns:
        True if passkey matches, False otherwise
    """
    if not provided_passkey or not stored_hash:
        return False
    
    try:
        return bcrypt.checkpw(
            provided_passkey.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
    except (ValueError, TypeError):
        # Invalid hash format - deny access
        return False


def generate_secure_passkey(length: int = 16) -> str:
    """
    Generate a cryptographically secure random passkey.
    
    Args:
        length: Length of passkey to generate (default 16)
        
    Returns:
        Random hex string of specified length
    """
    return os.urandom(length).hex()
