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

router = APIRouter()

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    handlers=[logging.FileHandler(log_filename),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

@router.post('/block/', 
            response_model=BlockWithAdditionalData,
            status_code=status.HTTP_200_OK, 
            tags=["BLOCKS"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                400: {"model": ResponseError, "description": "Invalid data."},
            })
@limiter.limit("5/minute")
def add_new_block(block: BlockWithAdditionalData, request: Request):
    """
    Add a new block to the blockchain.
    
    Args:
    - block (BlockWithAdditionalData): The block to be added to the blockchain.

    Returns:
    - BlockWithAdditionalData: The block added to the blockchain.
    """
    try:
        blockchain = get_blockchain()
        logger.info("Adding new block...")
        if not blockchain.add_block(block, block.hash):
            raise HTTPException(status_code=400, detail="The block was discarded by the node.")
        logger.info("Block added to the blockchain.")
        return block.dict()
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)