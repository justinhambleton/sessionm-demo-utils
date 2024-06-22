import os
import json
import uuid
import random
import asyncio
import aiohttp
from aiohttp import BasicAuth
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone

# Load and define environment variables
load_dotenv()

CLOUDPOS_ENDPOINT = os.getenv('CLOUDPOS_ENDPOINT')
AUTH_TOKEN = os.getenv('CLOUDPOS_AUTH_TOKEN')

if not CLOUDPOS_ENDPOINT or not AUTH_TOKEN:
    raise ValueError("Essential environment variables (CLOUDPOS_ENDPOINT, CLOUDPOS_AUTH_TOKEN) are not set.")

# Configure logging
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, filename=os.path.join(LOG_DIR, 'transactions.log'),
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to send transaction to the REST API asynchronously
async def send_transaction(session, transaction_data):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {AUTH_TOKEN}'
    }
    try:
        async with session.post(CLOUDPOS_ENDPOINT, headers=headers, json=transaction_data) as response:
            status = response.status
            response_text = await response.text()
            logger.info(f"Transaction Response Status: {status}, Response Text: {response_text}")
            return {"status": status, "response": response_text, "request_body": transaction_data}
    except aiohttp.ClientError as e:
        logger.error(f"Client error: {e}")
        return {"status": "error", "response": str(e), "request_body": transaction_data}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "response": str(e), "request_body": transaction_data}

# Function to generate transaction data
def generate_transaction_data(user_id):
    # Get current UTC time
    current_utc_time = datetime.now(timezone.utc)
    # Format the time to JavaScript JSON date-time format (yyyy-MM-ddTHH:mm:ss.fffZ)
    formatted_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # Generate random values for monetary amounts
    amount = float(random.randint(10, 100))
    unit_price = amount
    subtotal = amount

    channel = random.choice(["IN-STORE", "MOBILE"])
    payment_type = random.choice(["Credit", "Cash", "Gift Card"])

    return {
        "store_id": "6A2FE030-08F8-44E0-842F-1D92A0874096",
        "client_id": "02B8E29F-7475-436F-94AA-D631E3577A28",
        "request_id": str(uuid.uuid4()),
        "request_payload": {
            "is_closed": True,
            "is_voided": False,
            "channel": channel,
            "pos_employee_id": "234234",
            "transaction_id": str(uuid.uuid4()),
            "guest_count": 1,
            "subtotal": subtotal,
            "tax_total": 0.00,
            "open_time": formatted_time,
            "modified_time": formatted_time,
            "items": [
                {
                    "line_id": "1",
                    "item_id": "008884303989M",
                    "quantity": 1,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                    "tax_included": 0
                }
            ],
            "payments": [
                {
                    "payment_id": str(uuid.uuid4()),
                    "amount": amount,
                    "type": payment_type,
                    "payment_time": formatted_time,
                    "user_id": user_id,
                    "user_id_type": "External_ID"
                }
            ],
            "discounts": []
        }
    }

# Main function to send transactions
async def send_qsr_transactions(user_ids):
    sample_size = int(len(user_ids) * 0.4)
    sample_user_ids = random.sample(user_ids, sample_size)

    async with aiohttp.ClientSession() as session:
        tasks = [send_transaction(session, generate_transaction_data(user_id)) for user_id in sample_user_ids]
        results = await asyncio.gather(*tasks)
        logger.info("Full results from asyncio.gather:")
        for result in results:
            logger.info(result)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.join(LOG_DIR, f"transactions_{timestamp}.json")

        full_log = [{
            "request_body": result["request_body"],
            "status": result["status"],
            "response": result["response"]
        } for result in results]

        with open(filename, 'w') as file:
            json.dump(full_log, file, indent=4)

        logger.info(f"{len(results)} transactions saved to {filename}")
        logger.info(f"Summary of responses: {full_log}")

if __name__ == "__main__":
    user_ids = ["670cbd3c-2ebe-11ef-96f3-3491ac110006"]  # Replace with actual user_ids
    asyncio.run(send_qsr_transactions(user_ids))
