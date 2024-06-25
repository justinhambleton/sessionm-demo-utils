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

# Load and define environment variables based on argument
def load_environment_variables(context):
    load_dotenv()
    env_vars = {
        'CLOUDPOS_ENDPOINT': os.getenv(f'{context.upper()}_CLOUDPOS_ENDPOINT'),
        'AUTH_TOKEN': os.getenv(f'{context.upper()}_CLOUDPOS_AUTH_TOKEN'),
        'STORE_ID': os.getenv(f'{context.upper()}_STORE_ID'),
        'CLIENT_ID': os.getenv(f'{context.upper()}_CLIENT_ID'),
    }

    for key, value in env_vars.items():
        if not value:
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

# Function to send transaction to the REST API asynchronously
async def send_transaction(session, transaction_data, auth, endpoint, logger):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth}'
    }
    try:
        async with session.post(endpoint, headers=headers, json=transaction_data) as response:
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
def generate_transaction_data(user_id, context, env_vars):
    store_id = env_vars['STORE_ID']
    client_id = env_vars['CLIENT_ID']

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

    transaction_data = {
        "store_id": store_id,
        "client_id": client_id,
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

    if context == "retail":
        transaction_data["request_payload"]["transaction_type"] = "RETAIL_SALE"
    elif context == "qsr":
        transaction_data["request_payload"]["transaction_type"] = "QSR_SALE"
    elif context == "fuel":
        transaction_data["request_payload"]["transaction_type"] = "FUEL_SALE"

    return transaction_data

# Main function to send transactions
async def send_transactions(user_ids, context, enable_logging):
    env_vars = load_environment_variables(context)
    endpoint = env_vars['CLOUDPOS_ENDPOINT']
    auth_token = env_vars['AUTH_TOKEN']

    if enable_logging:
        logger = setup_logging()
    else:
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())

    # --------------------------- VERY IMPORTANT SETTING  ---------------------------
    # This determines the percentage of new customers that send a first transactions
    # Generally, we do not want 100% of new customers to send a transaction
    sample_size = int(len(user_ids) * 0.4)
    sample_user_ids = random.sample(user_ids, sample_size)

    async with aiohttp.ClientSession() as session:
        tasks = [send_transaction(session, generate_transaction_data(user_id, context, env_vars), auth_token, endpoint, logger) for user_id in sample_user_ids]
        results = await asyncio.gather(*tasks)
        logger.info("Full results from asyncio.gather:")
        for result in results:
            logger.info(result)

        if enable_logging:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = os.path.join('logs', f"transactions_{timestamp}.json")

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
    context = "qsr"  # Will be replaced with actual context argument
    enable_logging = True  # Will be replaced with actual enable_logging argument
    user_ids = ["670cbd3c-2ebe-11ef-96f3-3491ac110006"]  # Will be replaced with actual user_ids
    asyncio.run(send_transactions(user_ids, context, enable_logging))
