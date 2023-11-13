from fastapi import APIRouter, HTTPException, Request, Depends, status
from slowapi.errors import RateLimitExceeded
from typing import List
import pymongo.errors
import logging

# Configuration, models, methods and authentication modules imports
#from app.api.config.db import database
from app.api.config.limiter import limiter
from app.api.config.env import API_NAME
from app.api.models.models import ResponseError
#from app.api.auth.auth import auth_handler
from app.api.methods.methods import handle_error
from app.api.routes.transactions import add_new_transaction

# Blockchain and wallet import
from blockchain_project import Wallet, \
                               TransactionType, Transaction, TransactionWithAdditionalData
from blockchain_project import save_wallet_to_file
from app.api.config.blockchain import blockchain

router = APIRouter()

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    handlers=[logging.FileHandler(log_filename),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

@router.post('/wallet/', 
            response_model=Wallet, 
            status_code=status.HTTP_201_CREATED, 
            tags=["WALLETS"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                400: {"model": ResponseError, "description": "Invalid wallet data."},
            })
@limiter.limit("100/hour")
def create_wallet(request: Request):
    """Create a new wallet.
    
    Returns:
    - Wallet: The created wallet with public and private keys.
    """
    try:
        logger.info("Creating a new wallet.")

        # Create a new wallet
        new_wallet = Wallet()
        new_wallet.generate_keys()

        logger.info("Wallet successfully created.")

        # Save the wallet in JSON format
        save_wallet_to_file(new_wallet)

        return new_wallet
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

@router.get('/wallet/balance/{public_key}/', 
            response_model=float, 
            status_code=status.HTTP_200_OK, 
            tags=["WALLETS"],
            responses={
                404: {"model": ResponseError, "description": "Wallet not found."},
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."}
            })
@limiter.limit("100/hour")
def get_wallet_balance(public_key: str, request: Request):
    """Get the balance of a wallet.
    
    Args:
    - public_key (str): The public key of the wallet.
    
    Returns:
    - float: The balance of the wallet.
    """
    try:
        logger.info(f"Fetching balance for wallet {public_key}.")

        balance = blockchain.get_balance(public_key)
        if balance is None:
            raise HTTPException(status_code=404, detail="Wallet not found.")

        logger.info(f"Balance for wallet {public_key}: {balance}")
        return balance
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

@router.get('/wallet/transactions/{public_key}/', 
            response_model=List[TransactionWithAdditionalData], 
            status_code=status.HTTP_200_OK, 
            tags=["WALLETS"],
            responses={
                404: {"model": ResponseError, "description": "Wallet not found."},
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."}
            })
@limiter.limit("50/hour")
def get_wallet_transactions(public_key: str, request: Request):
    """Get transactions associated with a wallet.
    
    Args:
    - public_key (str): The public key of the wallet.
    
    Returns:
    - List[TransactionWithAdditionalData]: List of transactions associated with the wallet.
    """
    try:
        logger.info(f"Fetching transactions for wallet {public_key}.")

        transactions = blockchain.get_transactions_for_wallet(public_key)
        if transactions is None:
            raise HTTPException(status_code=404, detail="Wallet not found.")

        logger.info(f"Found {len(transactions)} transactions for wallet {public_key}.")
        return transactions
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)
