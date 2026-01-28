from cryptography.fernet import Fernet
import os

key = os.environ.get('ENCRYPTION_KEY')
if key:
    fernet = Fernet(key.encode())
else:
    raise ValueError("ENCRYPTION_KEY not set in .env file")

def encrypt_data(data):
    if not data:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return None
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return "Decryption Error" 