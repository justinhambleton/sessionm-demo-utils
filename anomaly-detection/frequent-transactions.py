import sys
import os
import argparse
import logging
import random
import asyncio
from pymongo import MongoClient, UpdateOne
from datetime import datetime, timezone
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from send_transactions import send_transactions

# Load and define environment variables based on argument
def load_environment_variables(context):
    # Specify the path to the .env file in the root directory
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(dotenv_path=env_path)
    env_vars = {
        'CLOUDPOS_ENDPOINT': os.getenv(f'{context.upper()}_CLOUDPOS_ENDPOINT'),
        'AUTH_TOKEN': os.getenv(f'{context.upper()}_CLOUDPOS_AUTH_TOKEN'),
        'STORE_ID': os.getenv(f'{context.upper()}_STORE_ID'),
        'CLIENT_ID': os.getenv(f'{context.upper()}_CLIENT_ID'),
        'MONGO_URI': os.getenv(f'{context.upper()}_MONGO_URI'),
        'MONGO_DB_NAME': os.getenv(f'{context.upper()}_MONGO_DB_NAME'),
        'MONGO_COLLECTION_NAME': os.getenv(f'{context.upper()}_MONGO_COLLECTION_NAME')
    }

    for key, value in env_vars.items():
        if value is None:
            raise ValueError(f"Essential environment variable {key} is not set for context {context}.")

    return env_vars

# Configure logging
def setup_logging():
    LOG_DIR = 'logs'
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(level=logging.INFO, filename=os.path.join(LOG_DIR, 'transactions.log'),
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    return logger

# MongoDB connection setup
def connect_mongo(mongo_uri, mongo_db_name):
    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]
    return db

# Function to fetch data based on context
def fetch_data(collection_name, db):
    collection = db[collection_name]
    data = collection.find().sort("timestamp", -1)  # Sort by timestamp in descending order
    return data

# Main function to orchestrate fetching data and sending transactions
async def burst_transactions(context, enable_logging, num_transactions_per_user):
    # Load environment variables
    env_vars = load_environment_variables(context)

    # Setup logging
    if enable_logging:
        logger = setup_logging()
    else:
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())

    # Connect to MongoDB
    db = connect_mongo(env_vars['MONGO_URI'], env_vars['MONGO_DB_NAME'])

    # Fetch data
    data = fetch_data(env_vars['MONGO_COLLECTION_NAME'], db)
    user_ids_with_timestamp = [{'user_id': doc['user_id'], 'timestamp': doc['timestamp']} for doc in data]
    total_collection_size = len(user_ids_with_timestamp)

    # Define the sample size (1% of total collection size)
    sample_size = max(1, int(total_collection_size * 0.01))  # Ensure at least 1 user is sampled
    sample_users = user_ids_with_timestamp[:sample_size]
    sample_user_ids = [doc['user_id'] for doc in sample_users]

    # Send transactions for each user in the sample
    for user_id in sample_user_ids:
        await send_transactions([user_id] * num_transactions_per_user, context, enable_logging)

    # Update sampled users in MongoDB with the last transaction timestamp
    lasttxn_timestamp = datetime.now(timezone.utc).isoformat()
    updates = [
        UpdateOne({'user_id': user['user_id']}, {'$set': {'lasttxn_timestamp': lasttxn_timestamp}})
        for user in sample_users
    ]
    db[env_vars['MONGO_COLLECTION_NAME']].bulk_write(updates)

    # Print the total collection size and number of transactions sent
    print(f"Total collection size: {total_collection_size}")
    print(f"Number of transactions sent: {sample_size * num_transactions_per_user}")

if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Generate and send random transactions.')
    parser.add_argument('--enableLogging', action='store_true', help='Enable logging.')
    parser.add_argument('--context', choices=['retail', 'qsr', 'fuel'], required=True, help='Context for the data.')
    parser.add_argument('--burstAmount', type=int, default=10, help='Number of transactions per user in the sample.')

    args = parser.parse_args()

    # Run the main function
    asyncio.run(burst_transactions(args.context, args.enableLogging, args.burstAmount))