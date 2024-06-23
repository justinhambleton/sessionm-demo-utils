import os
import argparse
import logging
import random
import asyncio
from pymongo import MongoClient
from dotenv import load_dotenv
from send_transactions import send_first_transactions

# Load and define environment variables based on argument
def load_environment_variables(context):
    load_dotenv()
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
async def randomize_transactions(context, enable_logging):
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

    # Define the sample percentage
    sample_percentage = 0.1  # Change this value as needed

    # Retain only a percentage of the total collection
    sample_size = int(total_collection_size * sample_percentage)
    sample_user_ids = [doc['user_id'] for doc in user_ids_with_timestamp[:sample_size]]

    # Send transactions
    await send_first_transactions(sample_user_ids, context, enable_logging)

    # Print the total collection size and number of transactions sent
    print(f"Total collection size: {total_collection_size}")
    print(f"Number of transactions sent: {sample_size}")

if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Generate and send random transactions.')
    parser.add_argument('--enableLogging', action='store_true', help='Enable logging.')
    parser.add_argument('--context', choices=['retail', 'qsr', 'fuel'], required=True, help='Context for the data.')

    args = parser.parse_args()

    # Run the main function
    asyncio.run(randomize_transactions(args.context, args.enableLogging))
