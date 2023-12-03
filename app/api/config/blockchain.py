from blockchain_project import Transaction, Block, Blockchain

# Instantiating the blockchain
_blockchain_instance = Blockchain(chain_file_name="blockchain.json")

def get_blockchain():
    return _blockchain_instance

def reset_blockchain():
    global _blockchain_instance
    _blockchain_instance = Blockchain(chain_file_name="blockchain.json")