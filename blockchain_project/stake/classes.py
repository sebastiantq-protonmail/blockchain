from pydantic import BaseModel

class Stake(BaseModel):
    """
    The Stake class is a stake that contains the node url and the amount of coins.
    """
    node_url: str # Backed up node for the stake
    amount: float