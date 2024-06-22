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
from datetime import datetime
import logging

# Load and define environment variables
load_dotenv()

ENDPOINT = os.getenv('RETAIL_CORE_API_URL')
USERNAME = os.getenv('RETAIL_CORE_API_USERNAME')
PASSWORD = os.getenv('RETAIL_CORE_API_PASSWORD')

if not ENDPOINT or not USERNAME or not PASSWORD:
    raise ValueError("Essential environment variables (RETAIL_CORE_API_URL, RETAIL_CORE_API_USERNAME, RETAIL_CORE_API_PASSWORD) are not set.")

CUSTOMERS_API = f'/priv/v1/apps/{USERNAME}/users'
API_URL = ENDPOINT + CUSTOMERS_API

fake = Faker()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the logs directory exists
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Function to generate a random phone number
def generate_phone_number():
    return f'+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}'

# Function to generate a random email address
def generate_email(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}@sessionmdemo.com"

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
    except Exception as e:
        logger.error(f"Error sending data to API: {e}")
        return {"status": "error", "response": str(e)}

# Generate random data
async def generate_and_send_data():
    auth = BasicAuth(login=USERNAME, password=PASSWORD)
    async with aiohttp.ClientSession() as session:
        tasks = []
        user_ids = []
        for _ in range(random.randint(10, 100)):
            external_id = str(uuid.uuid4())
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = generate_email(first_name, last_name)
            phone_number = generate_phone_number()
            date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
            address = fake.address().replace("\n", ", ")

            # Parse the address into components
            address_components = parse_address(address)

            data = {
                "user": {
                    "external_id": external_id,
                    "external_id_type": "py-script",
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
                    "locale": "en-us",
                    "user_profile": {
                        "brand": ["vrg","kr","ta","psg","gho","me"]
                    }
                }
            }
            tasks.append(send_to_api(session, data, auth))
            user_ids.append(external_id)

        results = await asyncio.gather(*tasks)

        # Log the full results for debugging
        logger.info("Full results from asyncio.gather:")
        for result in results:
            logger.info(result)

        # Create the filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.join(LOG_DIR, f"customers_{timestamp}.json")

        # Extract and write the responses to the local JSON file
        responses = [result["response"] for result in results if "response" in result]
        with open(filename, 'w') as file:
            json.dump(responses, file, indent=4)

        logger.info(f"{len(results)} customers saved to {filename}")
        logger.info(f"Summary of responses: {responses}")

        return user_ids

async def main(send_txns):
    user_ids = await generate_and_send_data()
    if send_txns:
        from send_retail_transactions import send_retail_transactions
        await send_retail_transactions(user_ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and send customer data.')
    parser.add_argument('--sendTxns', action='store_true', help='Send transactions after creating customers')
    args = parser.parse_args()

    asyncio.run(main(args.sendTxns))
