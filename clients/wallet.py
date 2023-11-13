import json
import requests
import ecdsa
import binascii
import os

CONFIG_FILE = "wallet_config.json"

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return {"public_key": "", "private_key": "", "node_url": ""}

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def create_wallet(node_url):
    response = requests.post(f"http://{node_url}/api/v1/blockchain/wallet/")
    if response.status_code == 201:
        return response.json()["public_key"], response.json()["private_key"]
    else:
        raise Exception("Failed to create wallet")

def sign_content(content: dict, private_key_str):
    content_json = json.dumps(content, separators=(',', ':'))
    sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key_str), curve=ecdsa.SECP256k1)
    signature = sk.sign(content_json.encode())
    return binascii.hexlify(signature).decode('utf-8')

def send_transaction(node_url, transaction):
    response = requests.post(f"http://{node_url}/api/v1/blockchain/transaction/", json=transaction)
    return response.status_code, response.text

def main():
    config = load_or_create_config()

    # If node_url is not set, ask the user
    if not config["node_url"]:
        config["node_url"] = input("Enter the node URL: ")
        save_config(config)

    # If keys do not exist, create new ones
    if not config["public_key"] or not config["private_key"]:
        public_key, private_key = create_wallet(config["node_url"])
        config["public_key"] = public_key
        config["private_key"] = private_key
        save_config(config)

    # Transaction details
    receiver = input("Enter receiver address: ")
    amount = float(input("Enter amount to transfer: "))

    # Prepare the transaction
    content = {
        "sender": config["public_key"],
        "receiver": receiver,
        "amount": amount
    }
    signature = sign_content(content, config["private_key"])

    transaction = {
        "type": 0,  # COIN_TRANSFER
        "content": content,
        "signature": signature
    }

    # Send the transaction
    status_code, response_text = send_transaction(config["node_url"], transaction)
    print(f"Response: {status_code}, {response_text}")

if __name__ == "__main__":
    main()
