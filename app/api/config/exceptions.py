from incidentsBugDSI import BugReports

# Configurations import
from app.api.config.env import RABBIT_USER, RABBIT_PASSWORD, RABBITMQ_IP, RABBITMQ_QUEUE

# Configure RabbitMQ credentials at library initialization
bugReportsInstance = BugReports(user=RABBIT_USER, password=RABBIT_PASSWORD, host=RABBITMQ_IP, queue=RABBITMQ_QUEUE)