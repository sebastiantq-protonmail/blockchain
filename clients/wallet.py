from enum import Enum
import json
import os
import requests
import ecdsa
import binascii
import random
from typing import Tuple, Union

CONFIG_FILE = "wallet_config.json"

class TransactionType(int, Enum):
    """
    The TransactionType class is an enumeration that contains the types of transactions.
    """
    COIN_TRANSFER = 0
    STAKE_DEPOSIT = 1
    STAKE_WITHDRAW = 2
    SMART_CONTRACT_DEPLOY = 3
    SMART_CONTRACT_EXECUTION = 4

def load_or_create_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return {"public_key": "", "private_key": "", "node_url": ""}

def save_config(config: dict):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def create_wallet(node_url: str) -> Tuple[str, str]:
    response = requests.post(f"http://{node_url}/api/v1/blockchain/wallet/")
    if response.status_code == 201:
        return response.json()["public_key"], response.json()["private_key"]
    else:
        raise Exception("Failed to create wallet")

def sign_content(content: dict, private_key_str: str) -> str:
    content_json = json.dumps(dict(content), separators=(',', ':'))
    sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key_str), curve=ecdsa.SECP256k1)
    signature = sk.sign(content_json.encode())
    return binascii.hexlify(signature).decode('utf-8')

def send_transaction(node_url: str, transaction: dict) -> Union[int, str]:
    response = requests.post(f"http://{node_url}/api/v1/blockchain/transaction/", json=transaction)
    return response.status_code, response.text

def menu():
    config = load_or_create_config()
    while True:
        print("\n1. Set Configuration")
        print("2. Send Transaction")
        print("3. Send Test Transaction")
        print("4. Stake Operation")
        print("5. Stake Test Operation")
        print("6. Deploy Smart Contract")
        print("7. Deploy Test Smart Contract")
        print("8. Call Smart Contract")
        print("9. Call Test Smart Contract")
        print("10. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            set_configuration(config)
        elif choice == '2':
            send_manual_transaction(config)
        elif choice == '3':
            send_test_transaction(config)
        elif choice == '4':
            stake_operation(config)
        elif choice == '5':
            stake_test_operation(config)
        elif choice == '6':
            deploy_smart_contract(config)
        elif choice == '7':
            deploy_test_smart_contract(config)
        elif choice == '8':
            call_smart_contract(config)
        elif choice == '9':
            call_test_smart_contract(config)
        elif choice == '10':
            break
        else:
            print("Invalid choice. Please try again.")

def set_configuration(config: dict):
    config["node_url"] = input("Enter the node URL: ")
    config["public_key"] = input("Enter your public key: ")
    config["private_key"] = input("Enter your private key: ")
    save_config(config)

# Transaction operations
def send_manual_transaction(config: dict):
    receiver = input("Enter receiver address: ")
    amount = float(input("Enter amount to transfer: "))
    create_and_send_transaction(config, receiver, amount, TransactionType.COIN_TRANSFER)

def send_test_transaction(config: dict):
    receiver = "b9c1ee14a373ba42e8231ba2731635b937aebdf7b84c2567f7dc2d2bb50c2969d5017dcb0c892444365ff210ba87232ff4b28df0d8ca88ec317255e89c1a4da5"
    amount = random.uniform(1, 1000)
    create_and_send_transaction(config, receiver, amount, TransactionType.COIN_TRANSFER)

# Stake operations
def stake_operation(config: dict):
    node_url = input("Enter node URL: ")
    amount = float(input("Enter amount to stake: "))
    create_and_send_transaction(config, node_url, amount, TransactionType.STAKE_DEPOSIT)

def stake_test_operation(config: dict):
    amount = random.uniform(1, 1000)
    create_and_send_transaction(config, config["node_url"], amount, TransactionType.STAKE_DEPOSIT)

# Smart contract operations
def deploy_smart_contract(config: dict):
    # Read the smart contract code from a file
    smart_contract_file = input("Enter the smart contract file: ")
    with open(smart_contract_file, "r") as file:
        contract_code = file.read()
    
    create_and_send_transaction(config, config["node_url"], contract_code, TransactionType.SMART_CONTRACT_DEPLOY)

def deploy_test_smart_contract(config: dict):
    contract_code = """
def increment():
    if "counter" not in state:
        state["counter"] = 0
    state["counter"] += 1
    return state["counter"]

def decrement():
    if "counter" not in state:
        state["counter"] = 0
    state["counter"] -= 1
    return state["counter"]
"""

    create_and_send_transaction(config, config["node_url"], contract_code, TransactionType.SMART_CONTRACT_DEPLOY)

def call_smart_contract(config: dict):
    contract_address = input("Enter contract address: ")
    function_signature = input("Enter function signature: ")
    create_and_send_transaction(config, contract_address, function_signature, TransactionType.SMART_CONTRACT_EXECUTION)

def call_test_smart_contract(config: dict):
    contract_address = "c5b1e9a9c7b6d5d5a9d0d9c9e8b9a9c7b6d5d5a9d0d9c9e8b9a9c7b6d5d5a9d0"
    function_signature = "increment"
    create_and_send_transaction(config, contract_address, function_signature, TransactionType.SMART_CONTRACT_EXECUTION)

def create_and_send_transaction(config: dict, receiver: str, payload, transaction_type: TransactionType):
    content = {
        "sender": config["public_key"],
        "receiver": receiver,
        "amount": payload
    } if transaction_type == TransactionType.COIN_TRANSFER else {
        "sender": config["public_key"],
        "node_url": receiver,  # In stake transactions, 'receiver' is the node_url
        "amount": payload
    } if transaction_type == TransactionType.STAKE_DEPOSIT else {
        "sender": config["public_key"],
        "node_url": receiver,  # In stake transactions, 'receiver' is the node_url
        "amount": payload
    } if transaction_type == TransactionType.STAKE_WITHDRAW else {
        "sender": config["public_key"],
        "contract_code": payload  # In smart contract transactions, 'payload' is the contract code
    } if transaction_type == TransactionType.SMART_CONTRACT_DEPLOY else {
        "sender": config["public_key"],
        "contract_address": receiver,  # In smart contract transactions, 'receiver' is the contract address
        "function_signature": payload,
        "args": [],
        "kwargs": {}
    } if transaction_type == TransactionType.SMART_CONTRACT_EXECUTION else None

    signature = sign_content(content, config["private_key"])
    transaction = {
        "type": transaction_type,
        "content": content,
        "signature": signature
    }

    print(f"Transaction: {transaction}")
    status_code, response_text = send_transaction(config["node_url"], transaction)
    print(f"Response: {status_code}, {response_text}")

if __name__ == "__main__":
    menu()

# TODO: Add a function to get the nonce of a wallet