import json
import os
import time
from typing import List, Optional, Union
import requests
from pydantic import BaseModel, validator

from blockchain_project import Block, BlockWithAdditionalData, TransactionType, Transaction, TransactionWithAdditionalData

class Blockchain(BaseModel):
    """
    A class representing the blockchain itself.
    """
    difficulty: int = 2
    peers: set = set()
    unconfirmed_transactions: list[TransactionWithAdditionalData] = []
    unconfirmed_balances: dict[str, float] = {}
    balances: dict[str, float] = {
        "eea28673cdf0a5d5bb429aac8be6ff29520d436cd402af205776ae3bbf428d9055ede3bf09b6c802c99c40e444a0a5e84afcf32b9ed648d008e08d09334fbb6e": 3000000.0, # Treasury address
        "357c6f13b5cf0eb3647dbaaed897eeec448a913fa48575a275af91122d0eb33a79dde99ee98fd6806f5de6ff27deb375e7db1fe1d8ef3c0f3abff8cd667f9a07": 0.0, # Burn address
    }
    chain: list[BlockWithAdditionalData] = []
    chain_file_name: str = None

    @validator('chain', pre=True, always=True)
    def create_genesis(cls, chain):
        """
        Create the genesis block during the initialization of the blockchain
        """
        if not chain:
            genesis_block = Block(index=0, transactions=[], previous_hash="0")
            genesis_block_data = genesis_block.dict()
            genesis_block_data_with_additional_data = BlockWithAdditionalData(**genesis_block_data)
            genesis_block_data_with_additional_data.hash = genesis_block_data_with_additional_data.compute_hash()
            return [genesis_block_data_with_additional_data]
        return chain
 
    def load_from_file(self) -> None:
        """
        A method to load the blockchain's chain from a file.
        """
        if self.chain_file_name is not None:
            # First, we need to check if the file exists
            if os.path.exists(self.chain_file_name):
                with open(self.chain_file_name, 'r') as chain_file:
                    raw_data = chain_file.read()
                    if raw_data and len(raw_data) != 0:
                        self.set_chain(json.loads(raw_data))

    @property
    def last_block(self) -> BlockWithAdditionalData:
        """
        A quick pythonic way to retrieve the most recent block in the chain. Note that the chain will always consist of at least one block (i.e., genesis block).
        """
        return self.chain[-1]

    def set_difficulty(self, difficulty: int) -> None:
        """
        A method to set the difficulty.
        """
        self.difficulty = difficulty

    def set_peers(self, peers: set) -> None:
        """
        A method to set the peers.
        """
        self.peers = self.peers.union(peers)

    def set_chain(self, chain: list[BlockWithAdditionalData]) -> None:
        """
        A method to set the blockchain.
        """        
        # Convert dict to BlockWithAdditionalData
        self.chain = [BlockWithAdditionalData(**block) for block in chain]

    def set_unconfirmed_transactions(self, unconfirmed_transactions: list[TransactionWithAdditionalData]) -> None:
        """
        A method to set the unconfirmed transactions.
        """
        # Convert dict to TransactionWithAdditionalData
        self.unconfirmed_transactions = [TransactionWithAdditionalData(**transaction) for transaction in unconfirmed_transactions]

    def get_difficulty(self) -> int:
        """
        A method to display the difficulty.
        """
        return self.difficulty

    def get_peers(self) -> set:
        """
        A method to display the peers.
        """
        return self.peers

    def get_chain(self) -> list[BlockWithAdditionalData]:
        """
        A method to display the blockchain.
        """
        return [dict(block) for block in self.chain]
    
    def get_unconfirmed_transactions(self) -> list[TransactionWithAdditionalData]:
        """
        A method to display the unconfirmed transactions.
        """
        return [dict(block) for block in self.unconfirmed_transactions]
    
    def check_chain_validity(self, chain: list[BlockWithAdditionalData]) -> bool:
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not self.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def announce_new_block(self, block: BlockWithAdditionalData) -> None:
        for peer in self.peers:
            url = f"http://{peer}/api/v1/blockchain/block/"
            data = block.json()
            response = requests.post(url, data=data)

    def consensus(self) -> bool:
        """
        A simple consensus algorithm that replaces our chain with the longest one in the network.
        """
        longest_chain = None
        current_len = len(self.chain)
    
        for node in self.peers:
            response = requests.get(f'http://{node}/api/v1/blockchain/chain/')
            chain = response.json()
            length = len(chain)
            if length > current_len and self.check_chain_validity(chain):
                current_len = length
                longest_chain = chain
    
        if longest_chain:
            return self.set_chain(longest_chain)

        return False
 
    def register_new_peer(self, node_address: str) -> None:
        """
        Add a new node to the list of peers.
        """
        self.peers.add(node_address)

    def create_chain_from_dump(self, chain_dump) -> None:
        """
        A method to add the chain from a dump and validate it.
        """
        for index, block_data in enumerate(chain_dump):
            block = BlockWithAdditionalData(**block_data)

            if index == 0:
                self.chain.append(block)
            else:
                added = self.add_block(block, block.hash)
                if not added: return False

        return True

    def create_genesis_block(self) -> None:
        """
        A method to generate the genesis block and appends it to the chain.
        """
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.compute_hash() # Manually set the hash of the genesis block
        self.chain.append(genesis_block)
    
    def proof_of_work(self, block: BlockWithAdditionalData) -> str:
        """
        Function that tries different values of the nonce to get a hash that satisfies our difficulty criteria.
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
 
        return computed_hash

    def add_block(self, block: BlockWithAdditionalData, proof: str) -> bool:
        """
        A method that adds the block to the chain after verification.
        """
        previous_hash = dict(self.last_block)['hash']
        
        if previous_hash != block.previous_hash:
            return False
        
        if not self.is_valid_proof(block, proof):
            return False
        
        mined_transactions_uuids = set()

        # Proccess the transactions
        for transaction in block.transactions:
            mined_transactions_uuids.add(transaction.uuid)

            # Verify the transaction data (signature, ...)
            if not self.is_valid_transaction(transaction):
                return False
        
        # Process the transactions
        if not self.process_transactions(block.transactions):
            return False

        # Update the unconfirmed transactions
        unconfirmed_transactions = [
            transaction for transaction in self.unconfirmed_transactions
            if transaction.uuid not in mined_transactions_uuids
        ]

        self.set_unconfirmed_transactions(unconfirmed_transactions)
        
        block.hash = proof
        self.chain.append(block)

        return True
 
    def is_valid_proof(self, block: BlockWithAdditionalData, block_hash: str) -> bool:
        """
        Check if block_hash is valid hash of block and satisfies the difficulty criteria.
        """
        # Remove the hash field from the block copy and then compute the hash again.
        # Because on previous computing block does not have hash field.
        block.hash = None
        return (block_hash.startswith('0' * self.difficulty) and block_hash == block.compute_hash())

    def add_new_unconfirmed_transaction_from_node(self, transaction: TransactionWithAdditionalData) -> bool:
        """
        Adds a new unconfirmed transaction to the list of transactions.
        """
        if not self.is_valid_transaction(transaction):
            raise False

        if self.transaction_exists(transaction.hash):
            return False

        self.unconfirmed_transactions.append(transaction)
        return True

    def transaction_exists(self, hash: str) -> bool:
        """
        Check if a transaction with a given hash exists in the blockchain.
        """
        for transaction in self.unconfirmed_transactions:
            if transaction.hash == hash:
                return True
        return False

    def add_new_unconfirmed_transaction(self, transaction: Transaction) -> TransactionWithAdditionalData:
        """
        Adds a new unconfirmed transaction to the list of transactions.
        """
        if not self.is_valid_transaction(transaction):
            raise False
        
        transaction_with_additional_data = TransactionWithAdditionalData(**transaction.dict())
        transaction_with_additional_data.hash = transaction_with_additional_data.compute_hash()
        
        if self.transaction_exists(transaction_with_additional_data.hash):
            raise Exception("Transaction already exists.")

        self.unconfirmed_transactions.append(transaction_with_additional_data)
        return transaction_with_additional_data

    def announce_new_transaction(self, transaction: TransactionWithAdditionalData) -> None:
        for peer in self.peers:
            url = f"http://{peer}/api/v1/blockchain/transaction/node/"
            data = transaction.json()
            response = requests.post(url, data=data)
            print(f"Peer {peer} response:", response.status_code)
            #print(response.json())

    def mine(self) -> bool:
        """
        This method serves as an interface to add the pending transactions to the blockchain by adding them to the block and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False
        
        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          previous_hash=last_block.hash)
        new_block_with_additional_data = BlockWithAdditionalData(**new_block.dict())
        proof = self.proof_of_work(new_block_with_additional_data)
        self.add_block(new_block_with_additional_data, proof)
        self.unconfirmed_transactions = []
        
        return new_block_with_additional_data.index
    
    def save_chain(self) -> None:
        """
        A method to save the blockchain's chain to a file.
        """
        if self.chain_file_name is not None:
            with open(self.chain_file_name, 'w') as chain_file:
                chain_file.write(self.get_chain())

    # Wallet methods
    def add_new_wallet(self, public_key: str) -> bool:
        """
        Add a new wallet to the blockchain.

        Args:
        - public_key (str): The public key of the new wallet.

        Returns:
        - bool: True if the wallet is added successfully, False otherwise.
        """
        if public_key in self.balances:
            return False  # Wallet already exists

        self.balances[public_key] = 0.0  # Set initial balance to 0
        return True

    def get_balance(self, public_key: str) -> Optional[float]:
        """
        Calculate and return the balance of a wallet.

        Args:
        - public_key (str): The public key of the wallet.

        Returns:
        - Optional[float]: The balance of the wallet, or None if the wallet is not found.
        """
        if public_key not in self.balances:
            return None

        return self.balances[public_key]

    def update_balance(self, address: str, amount: float) -> None:
        """
        Update the balance of a wallet.
        """
        if address not in self.balances:
            self.balances[address] = 0.0
        self.balances[address] += amount

    def get_transactions_for_wallet(self, public_key: str) -> List[TransactionWithAdditionalData]:
        """
        Retrieve all transactions associated with a wallet.

        Args:
        - public_key (str): The public key of the wallet.

        Returns:
        - List[TransactionWithAdditionalData]: A list of transactions associated with the wallet.
        """
        transactions = []
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.content.sender == public_key or transaction.content.receiver == public_key:
                    transactions.append(transaction)

        return transactions

    # Transaction methods
    def is_valid_transaction(self, transaction: Union[Transaction, TransactionWithAdditionalData]) -> bool:
        if transaction.type == TransactionType.COIN_TRANSFER:
            # Verify if the sender has enough balance to avoid double spending
            sender_unconfirmed_balance = self.unconfirmed_balances.get(transaction.content.sender, 0.0)
            sender_balance = self.get_balance(transaction.content.sender)

            if sender_balance - sender_unconfirmed_balance < transaction.content.amount:
                return False
            
            # Verify the signature of the transaction
            if not transaction.verify_signature(transaction.content, transaction.signature, transaction.content.sender):
                return False 

            # Update the unconfirmed balance
            self.unconfirmed_balances[transaction.content.sender] = sender_unconfirmed_balance + transaction.content.amount
        #else:
            # Add new transaction types here
        
        return True
    
    def process_transactions(self, transactions: list[TransactionWithAdditionalData]) -> bool:
        """
        Process a list of transactions.
        """
        for transaction in transactions:
            if transaction.type == TransactionType.COIN_TRANSFER:
                self.update_balance(transaction.content.sender, -transaction.content.amount)
                self.update_balance(transaction.content.receiver, transaction.content.amount)
            # else:
                # Add new transaction types here

        return True