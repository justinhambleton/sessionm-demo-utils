import os
import random
import uuid
import json
import re
import asyncio
import aiohttp
import argparse
from aiohttp import BasicAuth
from dotenv import load_dotenv
from faker import Faker
from datetime import datetime, timezone
import logging
from pymongo import MongoClient

# Load and define environment variables
load_dotenv()

HOST = os.getenv('QSR_CORE_HOST')
USERNAME = os.getenv('QSR_CORE_USERNAME')
PASSWORD = os.getenv('QSR_CORE_PASSWORD')
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
MONGO_COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME')

if not HOST or not USERNAME or not PASSWORD or not MONGO_URI or not MONGO_DB_NAME or not MONGO_COLLECTION_NAME:
    raise ValueError("Essential environment variables are not set.")

CUSTOMERS_API = f'/priv/v1/apps/{USERNAME}/users'
API_URL = HOST + CUSTOMERS_API

fake = Faker()

# Configure logging (initially set to no-op)
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

def setup_logging():
    global logger
    LOG_DIR = 'logs'
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(level=logging.INFO, filename=os.path.join(LOG_DIR, 'qsr-birth.log'),
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# MongoDB client setup
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]

# Function to generate a random phone number
def generate_phone_number():
    return f'+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}'

# Function to generate a random email address
def generate_email(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@sessionmdemo.com"

# Function to parse a full street address into components
def parse_address(address):
    address_pattern = re.compile(
        r'(?P<street_address>[\d\s\w.,-]+)\s*,?\s*'
        r'(?P<city>[\w\s]+)\s*,\s*'
        r'(?P<state_code>[A-Z]{2})\s+'
        r'(?P<postal_code>\d{5}(?:-\d{4})?)'
    )
    match = address_pattern.match(address)
    if not match:
        logger.warning(f"Address format is incorrect or unsupported: {address}")
        return {
            "street_address": address,
            "city": '',
            "state_code": '',
            "postal_code": ''
        }
    return match.groupdict()

# Function to send data to REST API asynchronously
async def send_to_api(session, data, auth):
    headers = {'Content-Type': 'application/json'}
    try:
        async with session.post(API_URL, headers=headers, json=data, auth=auth) as response:
            status = response.status
            response_text = await response.text()
            logger.info(f"Response Status: {status}, Response Text: {response_text}")
            return {"status": status, "response": response_text}
    except aiohttp.ClientError as e:
        logger.error(f"Client error: {e}")
        return {"status": "error", "response": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "response": str(e)}

# Function to generate customer data
def generate_customer_data():
    external_id = str(uuid.uuid4())
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = generate_email(first_name, last_name)
    phone_number = generate_phone_number()
    date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
    address = fake.address().replace("\n", ", ")

    # Parse the address into components
    address_components = parse_address(address)

    return {
        "external_id": external_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "opted_in": True,
        "dob": date_of_birth,
        "address": address_components['street_address'],
        "city": address_components['city'],
        "zip": address_components['postal_code'],
        "state": address_components['state_code'],
        "country": "USA",
        "locale": "en-us"
    }

# Generate random data
async def generate_and_send_data():
    auth = BasicAuth(login=USERNAME, password=PASSWORD)
    async with aiohttp.ClientSession() as session:
        tasks = []
        user_ids = []
        user_records = []

        for _ in range(random.randint(10, 100)):
            customer_data = generate_customer_data()
            data = {"user": customer_data}
            tasks.append(send_to_api(session, data, auth))
            user_ids.append(customer_data["external_id"])

        results = await asyncio.gather(*tasks)

        # Log the full results for debugging
        logger.info("Full results from asyncio.gather:")
        for result in results:
            logger.info(result)

        # Create the filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = os.path.join('logs', f"customers_{timestamp}.json")

        # Extract and write the responses to the local JSON file
        responses = [result["response"] for result in results if "response" in result]
        with open(filename, 'w') as file:
            json.dump(responses, file, indent=4)

        # Extract user.id and user.email from responses and store in MongoDB
        for result in results:
            if result["status"] == 200:
                try:
                    response_json = json.loads(result["response"])
                    if "user" in response_json:
                        user_id = response_json["user"]["id"]
                        email = response_json["user"]["email"]
                        user_records.append({"user_id": user_id, "email": email, "timestamp": datetime.now(timezone.utc)})
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error parsing response: {e}")

        if user_records:
            collection.insert_many(user_records)
            logger.info(f"{len(user_records)} user records stored in MongoDB")

        logger.info(f"{len(results)} customers saved to {filename}")
        logger.info(f"Summary of responses: {responses}")

        return [record["user_id"] for record in user_records]

        logger.info(f"{len(records)} user IDs stored in MongoDB")

async def main(send_txns, enable_logging):
    if enable_logging:
        setup_logging()
    user_ids = await generate_and_send_data()
    if send_txns:
        from send_qsr_transactions import send_qsr_transactions
        await send_qsr_transactions(user_ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and send customer data.')
    parser.add_argument('--sendTxns', action='store_true', help='Send transactions after creating customers')
    parser.add_argument('--enableLogging', action='store_true', help='Enable logging')
    args = parser.parse_args()

    asyncio.run(main(args.sendTxns, args.enableLogging))
