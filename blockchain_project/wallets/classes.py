import ecdsa
import binascii
from typing import Optional
from pydantic import BaseModel

class Wallet(BaseModel):
    """
    The Wallet class is a wallet that contains the public and private keys.
    """
    private_key: Optional[str]
    public_key: Optional[str]

    def generate_keys(self) -> None:
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) # Private key
        vk = sk.verifying_key # Public key

        self.private_key = binascii.hexlify(sk.to_string()).decode('utf-8')
        self.public_key = binascii.hexlify(vk.to_string()).decode('utf-8')
        
    def get_public_key(self) -> str:
        return self.public_key
    
    def get_private_key(self) -> str:
        return self.private_key
    
    def get_public_key_from_private_key(private_key) -> str:
        """
        Gets the public key from the private key.
        """
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
        vk = sk.verifying_key
        return binascii.hexlify(vk.to_string()).decode('utf-8')