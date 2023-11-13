import ecdsa
import binascii
from typing import Optional
from pydantic import BaseModel

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
#from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding

class Wallet(BaseModel):
    """
    The Wallet class is a wallet that contains the public and private keys.
    """
    private_key: Optional[str]
    public_key: Optional[str]

    """
    def generate_keys(self):
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Generate public key
        public_key = private_key.public_key()

        # Convert keys to PEM format
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        self.private_key = pem_private
        self.public_key = pem_public
    """

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
    
    # Transaction signing
    '''
    def sign_transaction(self, transaction):
        """
        Sign a transaction with the private key.
        """
        private_key = serialization.load_pem_private_key(
            self.private_key.encode(),
            password=None,
            backend=default_backend()
        )
        signature = private_key.sign(
            transaction.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    '''

    '''
    @staticmethod
    def verify_signature(transaction, signature, public_key):
        """
        Verify the signature of a transaction.
        """
        public_key = serialization.load_pem_public_key(public_key.encode(), backend=default_backend())
        try:
            public_key.verify(
                signature,
                transaction.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False
    '''