from fastapi import APIRouter, HTTPException, Request, Depends, status
from slowapi.errors import RateLimitExceeded
from bson import ObjectId
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

# Blockchain project import
from blockchain_project import Transaction, TransactionType, TransactionWithAdditionalData
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

@router.post('/transaction/', 
            response_model=list[TransactionWithAdditionalData], 
            status_code=status.HTTP_201_CREATED, 
            tags=["TRANSACTIONS"],
            responses={
                400: {"model": ResponseError, "description": "Invalid transaction data."},
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."}
            })
@limiter.limit("500/minute")
def add_new_transaction(transaction: Transaction, request: Request):
    """Add a new transaction to the blockchain.
    
    Args:
    - transaction (Transaction): Transaction data to be added.
    
    Returns:
    - str: Response message after adding the transaction.
    """
    try:
        logger.info("Adding a new transaction.")
        logger.debug(f"Transaction data: {transaction.dict()}") # Using debug level for transaction details
        
        # Verify the transaction data (signature, ...)
        logger.info("Verifying the transaction.")
        if not blockchain.is_valid_transaction(transaction):
            raise HTTPException(status_code=400, detail="Invalid transaction.")

        transaction_with_additional_data = blockchain.add_new_unconfirmed_transaction(transaction)
        logger.info("Transaction successfully added.")

        # Propagate the transaction to other nodes
        logger.info("Propagating the transaction to other nodes.")
        blockchain.announce_new_transaction(transaction_with_additional_data)
        logger.info("Transaction successfully propagated.")

        return blockchain.get_unconfirmed_transactions()
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

@router.post('/transaction/node', 
            response_model=list[TransactionWithAdditionalData], 
            status_code=status.HTTP_201_CREATED, 
            tags=["TRANSACTIONS"],
            responses={
                400: {"model": ResponseError, "description": "Invalid transaction data."},
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."}
            })
@limiter.limit("500/minute")
def receive_transaction(transaction: TransactionWithAdditionalData, request: Request):
    """Add a new transaction to the blockchain from other node.
    
    Args:
    - transaction (TransactionWithAdditionalData): Transaction data to be added.
    
    Returns:
    - str: Response message after adding the transaction.
    """
    try:
        logger.info("Adding a new transaction.")
        logger.debug(f"Transaction data: {transaction.dict()}") # Using debug level for transaction details
        
        # Verify the transaction data (signature, ...)
        logger.info("Verifying the transaction.")
        if not blockchain.is_valid_transaction(transaction):
            raise HTTPException(status_code=400, detail="Invalid transaction.")

        if blockchain.add_new_unconfirmed_transaction_from_node(transaction):
            logger.info("Transaction successfully added.")

            # Propagate the transaction to other nodes
            logger.info("Propagating the transaction to other nodes.")
            blockchain.announce_new_transaction(transaction)
            logger.info("Transaction successfully propagated.")
        else:
            logger.info("Transaction already exists.")

        return blockchain.get_unconfirmed_transactions()
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)