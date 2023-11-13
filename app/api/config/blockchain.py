from blockchain_project import Transaction, Block, Blockchain

# Instantiating the blockchain
blockchain = Blockchain(chain_file_name="blockchain.json")
blockchain.load_from_file()