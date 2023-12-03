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

from blockchain_project import Blockchain

router = APIRouter()

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    handlers=[logging.FileHandler(log_filename),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

@router.get('/blockchain/', 
            response_model=Blockchain,
            status_code=status.HTTP_200_OK, 
            tags=["BLOCKCHAIN"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                400: {"model": ResponseError, "description": "Invalid data."},
            })
@limiter.limit("5/minute")
def get_complete_blockchain(request: Request):
    """
    Get the blockchain.

    Returns:
    - Blockchain: The blockchain data.
    """
    try:
        blockchain = get_blockchain()
        logger.info("Getting blockchain...")
        return blockchain
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)