import asyncio
from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import IPvAnyAddress
import requests
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
from app.api.methods.miner import mine_block

# Blockchain project import
from app.api.config.blockchain import blockchain

from blockchain_project.blockchain import Blockchain

router = APIRouter()

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    handlers=[logging.FileHandler(log_filename),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

@router.post('/register/{node_address}/{node_id}/', 
            response_model=Blockchain,
            status_code=status.HTTP_200_OK, 
            tags=["NODES"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                400: {"model": ResponseError, "description": "Invalid data."},
            })
@limiter.limit("500/minute")
def register_new_peers(node_address: str, node_id: str, request: Request):
    """
    Register a new peer node.
    
    Args:
    - node_address (str): The address of the peer node.
    - node_id (str): The id of the peer node.

    Returns:
    - Blockchain: The blockchain data.
    """
    try:
        logger.info("Registering a new peer node.")

        if not node_address:
            raise HTTPException(status_code=400, detail="Invalid data")

        blockchain.register_new_peer(node_address, node_id)
        logger.info("New peer node successfully registered.")

        # Returns blockchain data
        return dict(blockchain)
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

@router.post('/register/peers/', 
            response_model=dict[str, str],
            status_code=status.HTTP_200_OK, 
            tags=["NODES"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                400: {"model": ResponseError, "description": "Invalid data."},
            })
@limiter.limit("500/minute")
def register_peers(peers: dict[str, str], request: Request):
    """
    Register node peers. This method is used when you want to register all peers on the node.

    Args:
    - peers (dict[str, str]): The peers to register.

    Returns:
    - dict[str, str]: The peers registered.
    """
    try:
        logger.info("Registering node peers.")

        blockchain.set_peers(peers)

        logger.info("Node peers successfully registered.")
        return dict(peers)
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Get the time to next mining
@router.get('/mining/time/',
            response_model=str,
            status_code=status.HTTP_200_OK, 
            tags=["NODES"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
            })
@limiter.limit("500/minute")
def get_time_to_next_mining(request: Request):
    """
    Get the time to next mining.

    Returns:
    - str: The time to next mining.
    """
    try:
        logger.info("Returning the last mined date.")
        return blockchain.time_to_next_mining()
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

@router.post('/connect/{node_address}/', 
            response_model=Blockchain,
            status_code=status.HTTP_200_OK, 
            tags=["NODES"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                400: {"model": ResponseError, "description": "Invalid data."},
            })
@limiter.limit("500/minute")
async def connect_to_new_node(node_address: str, request: Request):
    """
    Connect to a new peer node. This method is used when you want to connect your node to another node. 
    
    Args:
    - node_address (str): The address of the peer node.

    Returns:
    - Blockchain: The blockchain data.
    """
    try:
        logger.info("Connecting to a new peer node.")

        if not node_address:
            raise HTTPException(status_code=400, detail="Invalid data")

        base_url = str(request.base_url)
        address = base_url.split("//")[1].rstrip("/")

        logger.info(f"Connecting to {node_address} from {address}.")

        # Connect to the node and get the response
        response = requests.post(f"http://{node_address}/api/v1/blockchain/register/{address}/{blockchain.node_id}/")

        # If the status code is 200, it means that everything went well.
        # Update the blockchain and the peers.
        if response.status_code == 200:
            chain_dump = response.json()['chain']
            
            if blockchain.create_chain_from_dump(chain_dump):
                blockchain.set_difficulty(response.json()['difficulty'])
                blockchain.set_peers(response.json()['peers'])
                blockchain.set_unconfirmed_transactions(response.json()['unconfirmed_transactions'])
                blockchain.set_chain(response.json()['chain'])
            else:
                raise HTTPException(status_code=400, detail="Invalid data")
            
            # Register the new peer node
            blockchain.register_new_peer(node_address, response.json()['node_id'])
        
            # Send the peers to the new peer node
            logger.info(f"Sending peers to {node_address}.")
            response = requests.post(f"http://{node_address}/api/v1/blockchain/register/peers/", json=blockchain.peers)

            if response.status_code != 200:
                logger.error("Failed to send peers to the new peer node.")
                raise HTTPException(status_code=500, detail="Connection to peer node failed")
            
            # Get the next mining time
            logger.info(f"Getting the next mining time from {node_address}.")
            response = requests.get(f"http://{node_address}/api/v1/blockchain/mining/time/")

            if response.status_code != 200:
                logger.error("Failed to get the next mining time from the new peer node.")
                raise HTTPException(status_code=500, detail="Connection to peer node failed")
            
            # Cancel the current mining task and create a new one with the new mining time
            app = request.app
            if app.state.mining_task and not app.state.mining_task.done():
                app.state.mining_task.cancel()
            app.state.mining_task = asyncio.create_task(mine_block(float(response.json()))) # Adjust the mining schedule
        else:
            raise HTTPException(status_code=500, detail="Connection to peer node failed")

        logger.info("New peer node successfully registered.")
        return dict(blockchain)
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)