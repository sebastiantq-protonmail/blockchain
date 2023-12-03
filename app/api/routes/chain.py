from fastapi import APIRouter, HTTPException, Request, Depends, status
from slowapi.errors import RateLimitExceeded
from bson import ObjectId
from typing import Any, Dict, List
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
from app.api.config.blockchain import get_blockchain

from blockchain_project.blocks import Block, BlockWithAdditionalData
from blockchain_project.transactions import Transaction, TransactionWithAdditionalData

router = APIRouter()

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    handlers=[logging.FileHandler(log_filename),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

@router.get('/chain/', 
            response_model=list[BlockWithAdditionalData],
            status_code=status.HTTP_200_OK, 
            tags=["CHAIN"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."}
            })
@limiter.limit("500/minute")
def get_chain(request: Request):
    """
    Retrieve the current state of the blockchain.
    
    Returns:
    - dict: A dictionary containing the length of the chain and the chain itself.
    """
    try:
        blockchain = get_blockchain()
        logger.info("Fetching the blockchain data.")
        return blockchain.get_chain()
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

@router.get('/pending/', 
            response_model=list[TransactionWithAdditionalData],
            status_code=status.HTTP_200_OK, 
            tags=["CHAIN"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."}
            })
@limiter.limit("500/minute")
def get_unconfirmed_transactions(request: Request):
    """
    Retrieve the current state of the unconfirmed transactions.
    
    Returns:
    - dict: A dictionary containing the length of the unconfirmed transactions and the list itself.
    """
    try:
        blockchain = get_blockchain()
        logger.info("Fetching the unconfirmed transactions data.")
        return blockchain.get_unconfirmed_transactions()
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)