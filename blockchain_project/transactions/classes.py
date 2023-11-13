from enum import Enum
import hashlib
import json
import uuid
import pytz
from datetime import datetime

import ecdsa
import binascii

from typing import Optional, Union
from pydantic import BaseModel, validator

class TransactionType(int, Enum):
    """
    The TransactionType class is an enumeration that contains the types of transactions.
    """
    COIN_TRANSFER = 0

class CoinTransferTransaction(BaseModel):
    """
    The CoinTransferTransaction class is a transaction that contains the sender, receiver and amount of coins.
    """
    sender: str
    receiver: str
    amount: float

# Centralized transaction content
PossibleContents = Union[CoinTransferTransaction, None]

class Transaction(BaseModel):
    """
    The Transaction class is a transaction that contains a dictionary depending on the type of transaction.
    """
    uuid: str = str(uuid.uuid4())
    type: TransactionType
    content: PossibleContents
    signature: str = None

    @validator('content', pre=True)
    def validate_content(cls, v, values):
        if 'type' in values:
            if values['type'] == TransactionType.COIN_TRANSFER:
                if isinstance(v, CoinTransferTransaction):
                    return v
                return CoinTransferTransaction(**v)
            # Add new transaction types here
        raise ValueError("Invalid content for transaction type")

    @staticmethod
    def verify_signature(content: PossibleContents, signature: str, public_key: str) -> bool:
        """
        Verify the signature of a transaction using ECDSA.
        :param content: The content of the transaction.
        :param signature: The signature to be verified.
        :param public_key: The public key that corresponds to the private key used for signing.
        :return: True if the signature is valid, False otherwise.
        """
        transaction_content_json = json.dumps(dict(content), separators=(',', ':'))
        vk = ecdsa.VerifyingKey.from_string(binascii.unhexlify(public_key), curve=ecdsa.SECP256k1)
        try:
            return vk.verify(binascii.unhexlify(signature), transaction_content_json.encode())
        except ecdsa.BadSignatureError:
            return False

class TransactionWithAdditionalData(Transaction):
    """
    The TransactionWithAdditionalData class is a transaction that contains a dictionary depending on the type of transaction.
    """
    timestamp: Optional[int] = int(datetime.now(pytz.timezone('America/Bogota')).timestamp())
    hash: Optional[str] = None

    def compute_hash(self) -> str:
        """
        Compute the unique identifier for the transaction.
        """
        return hashlib.sha256(self.json().encode()).hexdigest()
