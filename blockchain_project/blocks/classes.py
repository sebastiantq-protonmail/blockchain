import pytz
from datetime import datetime
import json
from hashlib import sha256
from typing import Optional
from pydantic import BaseModel

from blockchain_project import TransactionWithAdditionalData

class Block(BaseModel):
    """
    The Block class is a block that contains a list of transactions in the blockchain being developed.
    """
    index: int
    transactions: list[TransactionWithAdditionalData]
    previous_hash: str
    
class BlockWithAdditionalData(Block):
    """
    The BlockWithAdditionalData class is a block that contains a list of transactions in the blockchain being developed.
    """
    timestamp: Optional[int] = int(datetime.now(pytz.timezone('America/Bogota')).timestamp())
    hash: Optional[str] = None

    def compute_hash(block) -> str:
        """
        Computes the hash of a block.
        :param block: Block to compute the hash of.
        :return: Hash of the block.
        """
        block_data = block.json()
        hash = sha256(block_data.encode()).hexdigest()
        return hash