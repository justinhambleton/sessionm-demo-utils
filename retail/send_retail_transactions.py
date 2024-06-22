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

TRANSACTION_ENDPOINT = 'https://cloudpos-connecteast1.ent-sessionm.com/api/2.0/send_transaction'
AUTH_TOKEN = os.getenv('TRANSACTION_API_AUTH_TOKEN')

if not TRANSACTION_ENDPOINT or not AUTH_TOKEN:
    raise ValueError("Essential environment variables (TRANSACTION_ENDPOINT, TRANSACTION_API_AUTH_TOKEN) are not set.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the logs directory exists
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Function to send transaction to the REST API asynchronously
async def send_retail_transaction(session, transaction_data):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {AUTH_TOKEN}'
    }
    try:
        async with session.post(TRANSACTION_ENDPOINT, headers=headers, json=transaction_data) as response:
            status = response.status
            response_text = await response.text()
            logger.info(f"Transaction Response Status: {status}, Response Text: {response_text}")
            return {"status": status, "response": response_text, "request_body": transaction_data}
    except Exception as e:
        logger.error(f"Error sending transaction: {e}")
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

    # Randomly select a value for channel and type (of payment)
    channel = random.choice(["IN-STORE", "POS", "MOBILE"])
    payment_type = random.choice(["Credit", "Cash", "Gift Card"])

    return {
        "store_id": "B7944570-DA96-4C87-8629-87AAC7BEB4E8",
        "client_id": "bee4a5bb-a65f-4245-a8ef-ae6d38157858",
        "request_id": str(uuid.uuid4()),
        "request_payload": {
            "is_closed": True,
            "is_voided": False,
            "channel": channel,
            "custom_data": {"brand": "Koalla Retail"},
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
async def send_retail_transactions(user_ids):
    # Select a random sample of 40% of the user_ids
    sample_size = int(len(user_ids) * 0.4)
    sample_user_ids = random.sample(user_ids, sample_size)

    async with aiohttp.ClientSession() as session:
        tasks = [send_retail_transaction(session, generate_transaction_data(user_id)) for user_id in sample_user_ids]
        results = await asyncio.gather(*tasks)
        logger.info("Full results from asyncio.gather:")
        for result in results:
            logger.info(result)

        # Set the filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.join(LOG_DIR, f"transactions_{timestamp}.json")

        # Extract and write the request bodies along with the responses (which are useless) so we know what was sent to a local JSON file
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
    # Example usage
    user_ids = ["670cbd3c-2ebe-11ef-96f3-3491ac110006"]  # Replace with actual user_ids
    asyncio.run(send_retail_transactions(user_ids))
