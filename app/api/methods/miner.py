import asyncio
import logging
from app.api.config.env import API_NAME

# Blockchain project import
from app.api.config.blockchain import blockchain

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    handlers=[logging.FileHandler(log_filename),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

async def mine_block(initial_delay: float = 33):
    try:
        print("Sleeping for {} seconds...".format(initial_delay))
        await asyncio.sleep(initial_delay)

        while True:
            logger.info("Mining new block...")
            result = blockchain.mine()

            if result:
                logger.info("Consensus...")
                await blockchain.consensus()
                logger.info("Consensus done.")
                
                logger.info("Announcing new block...")
                await blockchain.announce_new_block(blockchain.last_block)
                logger.info("Announcement done.")
                
                logger.info("Block successfully mined.")
                logger.info("Block #{} is mined.".format(result))
            else:
                logger.info("No transactions to mine.")

            await asyncio.sleep(33)
    except asyncio.CancelledError:
        # Handle the cancellation if needed
        pass