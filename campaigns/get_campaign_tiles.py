import os
import json
import argparse
import asyncio
import aiohttp
from aiohttp import BasicAuth
from dotenv import load_dotenv
import logging

# Load and define environment variables based on argument
def load_environment_variables(context):
    load_dotenv()
    env_vars = {
        'HOST': os.getenv(f'{context.upper()}_CORE_HOST'),
        'USERNAME': os.getenv(f'{context.upper()}_CORE_USERNAME'),
        'PASSWORD': os.getenv(f'{context.upper()}_CORE_PASSWORD')
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
    logging.basicConfig(level=logging.INFO, filename=os.path.join(LOG_DIR, 'campaigns.log'),
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# Function to fetch campaigns for a user
async def fetch_campaigns(user_id, env_vars):
    auth = BasicAuth(login=env_vars['USERNAME'], password=env_vars['PASSWORD'])
    api_url = f"{env_vars['HOST']}/priv/v1/apps/{env_vars['USERNAME']}/users/{user_id}/campaigns"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, auth=auth) as response:
                status = response.status
                response_text = await response.text()
                logger.info(f"Response Status: {status}, Response Text: {response_text}")
                if status == 200:
                    return json.loads(response_text)
                else:
                    logger.error(f"Failed to fetch campaigns: {response_text}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

# Function to filter and print internal tile templates
def filter_and_print_internal_tiles(campaigns, type_filter):
    filtered_tiles = []
    if campaigns and "campaigns" in campaigns and "tiles" in campaigns["campaigns"]:
        for tile in campaigns["campaigns"]["tiles"]:
            if tile.get("template", {}).get("type") == "internal_tile":
                if type_filter:
                    if tile.get("custom_payload", {}).get("type") == type_filter:
                        filtered_tiles.append(tile)
                else:
                    filtered_tiles.append(tile)

    for tile in filtered_tiles:
        print(json.dumps(tile, indent=4))

    print(f"Number of filtered tiles: {len(filtered_tiles)}")

# Main function
async def main(context, user_id, enable_logging, type_filter):
    if enable_logging:
        setup_logging()
    env_vars = load_environment_variables(context)
    campaigns = await fetch_campaigns(user_id, env_vars)
    filter_and_print_internal_tiles(campaigns, type_filter)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch and print internal tile campaigns for a user.')
    parser.add_argument('--context', required=True, choices=['retail', 'qsr', 'fuel'], help='Specify the context: retail, qsr, or fuel')
    parser.add_argument('--user_id', required=True, help='Specify the user ID')
    parser.add_argument('--enableLogging', action='store_true', help='Enable logging')
    parser.add_argument('--typeFilter', required=False, help='Specify the custom_payload type to filter by')
    args = parser.parse_args()

    asyncio.run(main(args.context, args.user_id, args.enableLogging, args.typeFilter))
