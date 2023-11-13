import json
from pathlib import Path

def save_wallet_to_file(wallet):
    """
    Save the wallet details in a JSON.
    """
    file_path = Path('wallets.json')

    # Load the existing wallets
    if file_path.exists():
        with file_path.open('r') as file:
            data = json.load(file)
    else:
        data = []

    # Add the new wallet
    data.append({
        "private_key": wallet.private_key,
        "public_key": wallet.public_key
    })

    # Save the wallets
    with file_path.open('w') as file:
        json.dump(data, file, indent=4)