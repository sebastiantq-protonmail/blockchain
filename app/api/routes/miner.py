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
from blockchain_project import Transaction
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

@router.post('/mine/', 
            response_model=str, 
            status_code=status.HTTP_200_OK, 
            tags=["MINER"],
            responses={
                400: {"model": ResponseError, "description": "Invalid transaction data."},
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."}
            })
@limiter.limit("500/minute")
def mine(request: Request):
    """Add a new transaction to the blockchain.
    
    Args:
    - transaction (Transaction): Transaction data to be added.
    
    Returns:
    - str: Response message after adding the transaction.
    """
    try:
        logger.info("Mining new block...")
        result = blockchain.mine()

        if not result:
            raise HTTPException(status_code=400, detail="No transactions to mine.")
        
        chain_length = len(blockchain.chain)
        logger.info("Consensus...")
        blockchain.consensus()
        logger.info("Consensus done.")
        if chain_length == len(blockchain.chain):
            logger.info("Announcing new block...")
            blockchain.announce_new_block(blockchain.last_block)
            logger.info("Announcement done.")
        logger.info("Block successfully mined.")
        return "Block #{} is mined.".format(result)
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)