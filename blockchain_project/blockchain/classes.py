from datetime import datetime
import hashlib
import json
import os
import time
from typing import List, Optional, Union
import uuid
import httpx
from pydantic import BaseModel, validator

from blockchain_project import Block, BlockWithAdditionalData, \
                               TransactionType, Transaction, TransactionWithAdditionalData, \
                               Stake, StakeTransaction

class Blockchain(BaseModel):
    """
    A class representing the blockchain itself.
    """
    node_id: str = str(uuid.uuid4())
    difficulty: int = 2
    peers: dict[str, str] = {}
    unconfirmed_transactions: list[TransactionWithAdditionalData] = []
    unconfirmed_balances: dict[str, float] = {}
    balances: dict[str, float] = {
        "eea28673cdf0a5d5bb429aac8be6ff29520d436cd402af205776ae3bbf428d9055ede3bf09b6c802c99c40e444a0a5e84afcf32b9ed648d008e08d09334fbb6e": 3000000.0, # Treasury address
        "357c6f13b5cf0eb3647dbaaed897eeec448a913fa48575a275af91122d0eb33a79dde99ee98fd6806f5de6ff27deb375e7db1fe1d8ef3c0f3abff8cd667f9a07": 0.0, # Burn address
    }
    stakes: dict[str, Stake] = {
        "eea28673cdf0a5d5bb429aac8be6ff29520d436cd402af205776ae3bbf428d9055ede3bf09b6c802c99c40e444a0a5e84afcf32b9ed648d008e08d09334fbb6e": Stake(node_url="localhost:8000", amount=2000000.0), # Treasury address
    }
    chain: list[BlockWithAdditionalData] = []
    chain_file_name: str = None
    last_mining_time = datetime.now()

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

    def set_peers(self, peers: dict[str, str]) -> None:
        """
        A method to set the peers.
        """
        self.peers = self.peers | peers

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
    
    def get_stakes(self) -> dict[str, Stake]:
        """
        A method to display the stakes.
        """
        return self.stakes

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

    async def announce_new_block(self, block: BlockWithAdditionalData) -> None:
        async with httpx.AsyncClient() as client:
            for node_url, node_id in self.peers.items():
                url = f"http://{node_url}/api/v1/blockchain/block/"
                data = block.json()
                response = await client.post(url, data=data)

    async def consensus(self) -> bool:
        """
        A simple consensus algorithm that replaces our chain with the higgest stake in the network.
        """
        longest_chain = None
        current_max_stake = self.calculate_total_stake(self.stakes)

        async with httpx.AsyncClient() as client:
            for node_url, node_id in self.peers.items():
                print(f"Checking chain of {node_url}")
                
                response = await client.get(f'http://{node_url}/api/v1/blockchain/stakes/')
                stake = self.calculate_total_stake(response.json())
                    
                print(f"Stake: {stake}")

                if stake >= current_max_stake:
                    node_chain = await client.get(f'http://{node_url}/api/v1/blockchain/chain/')
                    longest_chain = node_chain.json()
                    current_max_stake = stake
                    print(f"New longest chain")

        if longest_chain:
            return self.set_chain(longest_chain)
        
        return False
 
    def register_new_peer(self, node_address: str, node_id: str) -> None:
        """
        Add a new node to the list of peers.
        """
        self.peers[node_address] = node_id

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
        genesis_block_with_additional_data = BlockWithAdditionalData(**genesis_block.dict())
        genesis_block_with_additional_data.hash = genesis_block_with_additional_data.compute_hash() # Manually set the hash of the genesis block
        self.chain.append(genesis_block)

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
        return block_hash == block.compute_hash()

    def add_new_unconfirmed_transaction_from_node(self, transaction: TransactionWithAdditionalData) -> bool:
        """
        Adds a new unconfirmed transaction to the list of transactions.
        """
        if not self.is_valid_transaction(transaction):
            raise False
        
        if self.transaction_exists(transaction.hash):
            return False
        
        self.proccess_unconfirmed_balances(transaction)
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
        
        self.proccess_unconfirmed_balances(transaction)

        self.unconfirmed_transactions.append(transaction_with_additional_data)
        return transaction_with_additional_data

    async def announce_new_transaction(self, transaction: TransactionWithAdditionalData) -> None:
        async with httpx.AsyncClient() as client:
            for node_url, node_id in self.peers.items():
                url = f"http://{node_url}/api/v1/blockchain/transaction/node/"
                data = transaction.json()
                response = await client.post(url, data=data)

    def mine(self) -> bool:
        """
        This method serves as an interface to add the pending transactions to the blockchain 
        by adding them to the block and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions: # No transactions to mine
            return False
        
        validator = self.select_validator()
        if validator is None: # No validators available
            return None

        validator_node_url = self.stakes.get(validator).node_url
        print(f"Selected validator: {validator_node_url}")
        if self.peers.get(validator_node_url) == self.node_id: # The selected validator is the current node
            last_block = self.last_block
            new_block = Block(index=last_block.index + 1,
                              transactions=self.unconfirmed_transactions,
                              previous_hash=last_block.hash)
            new_block_with_additional_data = BlockWithAdditionalData(**new_block.dict())
            proof = new_block_with_additional_data.compute_hash()
            self.add_block(new_block_with_additional_data, proof)
            self.unconfirmed_transactions = []
            self.update_last_mining_time()
            return new_block_with_additional_data.index
        
        # If the selected validator is not the current node
        return None
    
    def update_last_mining_time(self) -> None:
        """
        Update the last mining time.
        """
        self.last_mining_time = datetime.now()

    def time_to_next_mining(self) -> int:
        """
        Calculate the time to the next mining.
        """
        elapsed = (datetime.now() - self.last_mining_time).total_seconds()
        return max(33 - elapsed, 0)

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
        elif transaction.type == TransactionType.STAKE_DEPOSIT:
            sender_balance = self.get_balance(transaction.content.sender)
            sender_stake = self.stakes.get(transaction.content.sender, Stake(amount=0.0, node_url=transaction.content.node_url)).amount

            if sender_balance + sender_stake < transaction.content.amount:
                return False  # No hay suficiente balance teniendo en cuenta el stake
        elif transaction.type == TransactionType.STAKE_WITHDRAW:
            return
        #else:
            # Add new transaction types here
        
        return True
    
    def proccess_unconfirmed_balances(self, transaction: Union[Transaction, TransactionWithAdditionalData]) -> None:
        """
        Update the unconfirmed balance
        """
        if transaction.type == TransactionType.COIN_TRANSFER:
            self.unconfirmed_balances[transaction.content.sender] = self.unconfirmed_balances.get(transaction.content.sender, 0.0) + transaction.content.amount
        elif transaction.type == TransactionType.STAKE_DEPOSIT:
            self.unconfirmed_balances[transaction.content.sender] = self.unconfirmed_balances.get(transaction.content.sender, 0.0) + transaction.content.amount
        # else:
            # Add new transaction types here

    def process_transactions(self, transactions: list[TransactionWithAdditionalData]) -> bool:
        """
        Process a list of transactions.
        """
        for transaction in transactions:
            if transaction.type == TransactionType.COIN_TRANSFER:
                self.update_balance(transaction.content.sender, -transaction.content.amount)

                # Remove the unconfirmed balance of the sender
                self.unconfirmed_balances[transaction.content.sender] -= transaction.content.amount

                self.update_balance(transaction.content.receiver, transaction.content.amount)
            elif transaction.type == TransactionType.STAKE_DEPOSIT:
                if not self.add_stake(transaction.content):
                    return False
                
                self.unconfirmed_balances[transaction.content.sender] -= transaction.content.amount
            elif transaction.type == TransactionType.STAKE_WITHDRAW:
                return self.withdraw_stake(transaction.content)
            # else:
                # Add new transaction types here

        return True
    
    # Stake methods
    def add_stake(self, stake: StakeTransaction) -> bool:
        """
        Add stake to a user.

        Args:
        - stake (StakeTransaction): Stake to add.

        Returns:
        - bool: True if the stake is added successfully, False otherwise.
        """
        balance = self.get_balance(stake.sender)
        if balance is None or balance < stake.amount:
            return False # Not enough balance to stake

        self.balances[stake.sender] -= stake.amount
        self.stakes[stake.sender] = self.stakes.get(stake.sender, Stake(amount=stake.amount, node_url=stake.node_url))
        self.stakes[stake.sender].amount += stake.amount
        return True
    
    def withdraw_stake(self, stake: StakeTransaction) -> bool:
        """
        Withdraw stake from a user.

        Args:
        - stake (StakeTransaction): Stake to withdraw.

        Returns:
        - bool: True if the stake is withdrawn successfully, False otherwise.
        """
        stake_amount = self.stakes.get(stake.sender, Stake(amount=0.0, node_url=stake.node_url)).amount
        if stake_amount < stake.amount:
            return False # Not enough stake to withdraw

        self.stakes[stake.sender].amount -= stake.amount
        self.balances[stake.sender] += stake.amount
        return True
    
    # PoS methods
    def select_validator(self) -> Optional[str]:
        """
        Seleccionar un validador para el próximo bloque basado en los stakes.
        Retorna la clave pública del validador seleccionado.
        """
        if not self.stakes:
            return None

        # Combinar elementos determinísticos
        last_block_hash = self.last_block.hash
        hash_value = hashlib.sha256(last_block_hash.encode()).hexdigest()

        # Convertir el hash en un número y usarlo para seleccionar el validador
        hash_number = int(hash_value, 16)

        # Crear una lista de candidatos donde cada uno aparece tantas veces como su stake
        candidates = []
        for public_key, stake in self.stakes.items():
            candidates.extend([public_key] * int(stake.amount))

        # Seleccionar el validador usando el número hash
        chosen_validator = candidates[hash_number % len(candidates)]

        return chosen_validator
    
    def calculate_total_stake(self, stakes: dict[str, Stake]):
        """
        Calculate the total staked.
        """
        return sum(Stake(**dict(stake)).amount for stake in stakes.values())
    
    def distribute_rewards(self, validator_public_key: str) -> None:
        """
        Distribuir las recompensas entre los participantes del stake del nodo validador.
        """
        REWARD_AMOUNT = 10  # Puedes ajustar este valor

        total_stake = sum(stake.amount for stake in self.stakes.values() if stake.node_url == validator_public_key)
        if total_stake == 0:
            return

        for public_key, stake in self.stakes.items():
            if stake.node_url == validator_public_key:
                reward = (stake.amount / total_stake) * self.REWARD_AMOUNT
                self.balances[public_key] = self.balances.get(public_key, 0) + reward

    def penalize_validator(self, validator_public_key: str) -> None:
        """
        Penalizar al validador quitándole tokens.
        """
        PENALTY_AMOUNT = 5  # Puedes ajustar este valor

        current_balance = self.balances.get(validator_public_key, 0)
        self.balances[validator_public_key] = max(0, current_balance - self.PENALTY_AMOUNT)