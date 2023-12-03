import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Methods imports
from app.api.methods.miner import mine_block

# Routes and config modules import
from app.api.config.env import API_NAME, PRODUCTION_SERVER_URL, DEVELOPMENT_SERVER_URL
from app.api.config.limiter import limiter
from app.api.config.blockchain import get_blockchain

from app.api.routes.blockchain import router as blockchain_router
from app.api.routes.transactions import router as transactions
from app.api.routes.blocks import router as blocks
from app.api.routes.chain import router as chain
#from app.api.routes.miner import router as miner # Deprecated, PoS is executed automatically
from app.api.routes.nodes import router as nodes
from app.api.routes.wallets import router as wallets
from app.api.routes.stakes import router as stakes

from blockchain_project.blockchain import Blockchain

from fastapi.openapi.utils import get_openapi

title=f'{API_NAME} API'
description=f'{API_NAME} API description.'
version='0.0.1'

app = FastAPI(
    openapi_url=f'/api/v1/{API_NAME}/openapi.json',
    docs_url=f'/api/v1/{API_NAME}/docs',
    redoc_url=f'/api/v1/{API_NAME}/redoc',
    servers=[
        {"url": PRODUCTION_SERVER_URL, "description": "Production server"},
        {"url": DEVELOPMENT_SERVER_URL, "description": "Development server"},
    ],
    title=title,
    description=description,
    version=version,
    terms_of_service='',
    contact={
        'name': '',
        'url': '',
        'email': '',
    },
    license_info={
        'name': '',
        'url': '',
    },
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "..."
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware configuration
origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def on_startup():
    blockchain = get_blockchain()
    # Actions to be executed when the API starts.
    blockchain.load_from_file()

    # Start mining
    app.state.mining_task = asyncio.create_task(mine_block())
    print('API started')

@app.on_event('shutdown')
async def on_shutdown():
    # Actions to be executed when the API shuts down.
    print('API shut down')

# Include the routes
app.include_router(blockchain_router, prefix=f'/api/v1/{API_NAME}')
app.include_router(chain, prefix=f'/api/v1/{API_NAME}')
app.include_router(transactions, prefix=f'/api/v1/{API_NAME}')
app.include_router(blocks, prefix=f'/api/v1/{API_NAME}')
#app.include_router(miner, prefix=f'/api/v1/{API_NAME}')
app.include_router(nodes, prefix=f'/api/v1/{API_NAME}')
app.include_router(wallets, prefix=f'/api/v1/{API_NAME}')
app.include_router(stakes, prefix=f'/api/v1/{API_NAME}')
