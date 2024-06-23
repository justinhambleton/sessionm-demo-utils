# SessionM Demo Utils

## Overview

This collection of scripts automates the random generation of customer profiles and transaction data and sends it to different SessionM demo environment endpoints, depending on the intended context. There are two primary scripts that can be run from the command line, or scheduled via cron or apscheduler:

`generate_customer.py`
`txn_randomizer.py`

### generate_customer.py
This collection of python scripts interacts with specific Sessionm demo environments to perform the following functions:
- Randomly generates new customers profiles within a specified SessionM demo environment, and with an environment specific customer data dictionary
- New customer profiles are generated based on a random value between a min and max value. This allows the script to generte a random number of users each time it runs, but never exceeding a max number of profiles so as to not degrade environment performance.
- The `generate_customer.py` script can optionally send a first transaction to a randomized percentage of the newly generated customers.
- The `txn_randomizer.py` is designed to pull a random selection of user_IDs from a MongoDB and sends transactions to that filtered list of customer profiles.

These script make use of the [Faker Python Library](https://faker.readthedocs.io/en/master/), which randomizes most of the customer data, including first and last name, email address, and address. Further randomization is applied to the user_profile customer attributes to introduce variety in the new customers that are created.

`generate_customer.py` expects a `--context` argument which determines which SessionM demo environment the script will execute against. Currently, this script is configured to only work with one of three demo environments, denoted by the argument values: retail, qsr or fuel. Each of the three contexts have specific data dictionaries for the customer profiles, allowing them to be further customized based on the customer data model within the respective demo environment.

## Table of Contents

- [Dependencies](#dependencies)
- [MongoDB Setup](#mongodb-setup)
- [Usage](#usage)
  - [Arguments](#arguments)
- [Contributing](#contributing)
- [License](#license)

## Dependencies

Before running this project, ensure you have the following dependencies installed:

- Python 3.x
- pymongo
- faker
- asyncio
- aiohttp
- argparse

You can install the required Python packages using the following command:

```sh
pip install pymongo faker asyncio aiohttp argparse
```

## MongoDB Setup

1. **Install MongoDB**:
   - Follow the instructions on the [official MongoDB installation page](https://docs.mongodb.com/manual/installation/) for your operating system.

2. **Start MongoDB**:
   - Start the MongoDB server by running the following command in your terminal:

     ```sh
     mongod
     ```

3. **Create the Database and Collection**:
   - Open a MongoDB shell by running `mongo` in your terminal.
   - Authenticate as admin user
   - Create three new databases: retail_db, qsr_db and fuel_db
   - Create three users for each database. All to be named: retail_user, qsr_user, fuel_user
   - Use openssl to generate base64 passwords for each user: ❯ openssl rand -base64 48
   - Collections will be created upon the first run of the script

## Usage

### Running the Script

This script accepts important command-line arguments to customize its behavior. Before running the `generate_customer.py` script, familiarize yourself with the arguments below to ensure proper useage.

### Arguments

- `--context` (required): Specifies the demo environment context. Can only be one of: retail, qsr or fuel.
- `--sendTxns` (optional): If included, invokes the `send_first_transactions.py` script to send first transactions to a randomized percentage of the the generated customers.
- `--enableLogging` (optional): If included, enables logging, which writes a JSON file for generate_customers and, if enabled, send_first_transactions.

### Example Usage for generate_customer.py

1. **Generate QSR Customers with first transactions and with logging**:

   ```sh
   python generate_customers.py --context qsr --sendTxns --enableLogging
   ```

2. **Generate Retail Customers with first transactions and without logging**:

   ```sh
   python generate_customers.py --context retail --sendTxns
   ```

3. **Generate QSR Customers without first transactions and without logging**:

   ```sh
   python generate_customers.py --context qsr
   ```

### Example Usage for txn_randomizer.py

1. **Send transactions to a random sample of existing QSR customer profiles with logging**:

   ```sh
   python txn_randomizer.py --context qsr --enableLogging
   ```

2. **Send transactions to a random sample of existing Retail customer profiles without logging**:

   ```sh
   python txn_randomizer.py --context retail
   ```

## Scripts

### generate_customer.py

This is the main script for generating random customer data. It accepts command-line arguments to control the number of customers generated and whether to invoke the transaction script. It includes an important setting that determines the range of new customer profiles created. This range is always random and between a min and max value. The max value is the most important setting to pay attention to. It is recommended this never exceed 500.

This script can run indepdently and without generating transactions so long as the `--sendTxns` argument is not included when the script is invoked (see usage example above).

### txn_randomizer.py
The purpose of this script is to send transactions against a randomized collection of existing users. The intent is to simulate realistic transaction activity against a random sample size of existing customer profiles. This script accepts the same `--context` argument as generate_customers.py. The script reads from the designated MongoDB and returns the entire collection. The full collection is then reduced to a sample size between 10% and 40%, which are then sent to send_transactions.py

### send_transactions.py
This is a utility script used by `generate_customer.py` and `txn_randomizer.py`

When the `--sendTxns` argument is used with the `generate_customer.py` script, first transactions will be sent to a randomized percentage of the newly generated customers. By default, the script only sends transactions to a randomized selection of 40% of the new customer profiles. It is not a realistic scenario for 100% of new customers to perform a first transaction. This setting can 100% if intended to be used for testing purposes and not to simulate real-world transaction behavior.

Similarly, `txn_randomizer.py` invokes send_transactions.py once the randomized sample size is selected. When logging is enabled, this script will only write the response status to the log file since the SessionM POS API does not return anything in the response other than a "200" code if the response is successful. Because of this, the log file also include the request JSON body to aid in troubleshooting.

## Contributing

This is a private project and not open to public contribution.

## License

This project is licensed under the MIT License.

---