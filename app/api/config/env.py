import os

# Add here all the environment variables

# Basic configuration
API_NAME = os.getenv('API_NAME')
JWT_SECRET = os.getenv('JWT_SECRET') # The JWT secret string
MONGO_CLIENT = os.getenv('MONGO_CLIENT') # Something like: mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]
PRODUCTION_SERVER_URL = os.getenv('PRODUCTION_SERVER_URL')
DEVELOPMENT_SERVER_URL = os.getenv('DEVELOPMENT_SERVER_URL')
IS_PRODUCTION = os.getenv('IS_PRODUCTION') # Boolean to determine if is prod environment or nah

# IncidentsBug library configuration
JIRA_PROJECT_ID = os.getenv('JIRA_PROJECT_ID')
RABBIT_USER = os.getenv('RABBIT_USER') # Your Jira credentials
RABBIT_PASSWORD = os.getenv('RABBIT_PASSWORD')
RABBITMQ_IP = os.getenv('RABBITMQ_IP') # Ask someone for the assigned server for this project
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE')

# N8 configuration
N8_IP = os.getenv('N8_IP')
N8_USER = os.getenv('N8_USER')
N8_PASSWORD = os.getenv('N8_PASSWORD')