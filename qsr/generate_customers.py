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

# Load and define environment variables based on argument
def load_environment_variables(context):
    load_dotenv()
    env_vars = {
        'HOST': os.getenv(f'{context.upper()}_CORE_HOST'),
        'USERNAME': os.getenv(f'{context.upper()}_CORE_USERNAME'),
        'PASSWORD': os.getenv(f'{context.upper()}_CORE_PASSWORD'),
        'MONGO_URI': os.getenv(f'{context.upper()}_MONGO_URI'),
        'MONGO_DB_NAME': os.getenv(f'{context.upper()}_MONGO_DB_NAME'),
        'MONGO_COLLECTION_NAME': os.getenv(f'{context.upper()}_MONGO_COLLECTION_NAME')
    }

    for key, value in env_vars.items():
        if not value:
            raise ValueError(f"Essential environment variable {key} is not set for context {context}.")

    return env_vars

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

fake = Faker()

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
async def send_to_api(session, data, auth, api_url):
    headers = {'Content-Type': 'application/json'}
    try:
        async with session.post(api_url, headers=headers, json=data, auth=auth) as response:
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
def generate_customer_data(context):
    external_id = str(uuid.uuid4())
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = generate_email(first_name, last_name)
    phone_number = generate_phone_number()
    date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
    address = fake.address().replace("\n", ", ")

    # Parse the address into components
    address_components = parse_address(address)

    base_data = {
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
        "country": "USA"
    }

    if context == "retail":
        base_data.update({
            "user_profile": {
                "brand": ["vrg","kr","ta","psg","gho","me"]
            }
        })
    elif context == "qsr":
        base_data.update({
          "user_profile": {
              "Allergies": [],
              "allowed_third_party_login_clients": [],
              "Closest_Location": [],
              "Delivery_Service": [],
              "Dietary_Restrictions": [],
              "Favorite_Team": [],
              "Mobile_Order_Account_ID": [],
              "Most_Frequent_Store": [],
              "pass_data": [],
              "Payment_Card_Hashed_IDs": [],
              "device_details": [],
              "device_details_offer": [],
              "GameAttendance": [],
              "Occasions": []
          }
        })
    elif context == "fuel":
        base_data.update({
            "user_profile": {
                "brand": ["kr"]
            }
        })

    return base_data

# Generate random data
async def generate_and_send_data(context, env_vars, enable_logging):
    auth = BasicAuth(login=env_vars['USERNAME'], password=env_vars['PASSWORD'])
    api_url = env_vars['HOST'] + f'/priv/v1/apps/{env_vars["USERNAME"]}/users'
    mongo_client = MongoClient(env_vars['MONGO_URI'])
    db = mongo_client[env_vars['MONGO_DB_NAME']]
    collection = db[env_vars['MONGO_COLLECTION_NAME']]

    async with aiohttp.ClientSession() as session:
        tasks = []
        user_ids = []
        user_records = []

        # --------------------------- VERY IMPORTANT SETTING  ---------------------------
        # This determines the min and max number of customer profiles to generate
        # DO NOT EXCEED MAX OF 500
        for _ in range(random.randint(1, 10)):
            customer_data = generate_customer_data(context)
            data = {"user": customer_data}
            tasks.append(send_to_api(session, data, auth, api_url))
            user_ids.append(customer_data["external_id"])

        results = await asyncio.gather(*tasks)

        # Log the full results for debugging
        logger.info("Full results from asyncio.gather:")
        for result in results:
            logger.info(result)

        if enable_logging:
            # Create the filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            filename = os.path.join('logs', f"customers_{timestamp}.json")

            # Extract and write the responses to the local JSON file
            responses = [result["response"] for result in results if "response" in result]
            with open(filename, 'w') as file:
                json.dump(responses, file, indent=4)

            logger.info(f"{len(results)} customers saved to {filename}")

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

        logger.info(f"Summary of responses: {responses}")

        return [record["user_id"] for record in user_records]

async def main(context, send_txns, enable_logging):
    if enable_logging:
        setup_logging()
    env_vars = load_environment_variables(context)
    user_ids = await generate_and_send_data(context, env_vars, enable_logging)
    if send_txns:
        from send_first_transactions import send_first_transactions
        await send_first_transactions(user_ids, context, enable_logging)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and send customer data.')
    parser.add_argument('--context', required=True, choices=['retail', 'qsr', 'fuel'], help='Specify the context: retail, qsr, or fuel')
    parser.add_argument('--sendTxns', action='store_true', help='Send transactions after creating customers')
    parser.add_argument('--enableLogging', action='store_true', help='Enable logging')
    args = parser.parse_args()

    asyncio.run(main(args.context, args.sendTxns, args.enableLogging))
