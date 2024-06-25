# SessionM Demo Utils

## Overview
This collection of python scripts interacts with specific Sessionm demo environments to perform the following functions:

- Randomly generate new customers profiles within a specified SessionM demo environment, and with a vertical-specific customer data dictionary for the user_profile object.
- A `--locale` argument can be specified to localize the random user profile data (e.g. Spanish, Portuguese). This will produce names and addresses that are localized to the region. Most standard locale codes work, just be mindful of address formats in different countries.
- New customer profiles are generated based on a random value between a min and max value. This allows the script to generate a random number of users each time it runs, but never to exceed a max number of profiles so as to not degrade environment performance.
- The `generate_customer.py` script can optionally send a first transaction to a randomized sample of the newly generated customers. This is to simulate the real-world scenario where not all new loyaly members transact. This can be dialed up or down as needed.
- The `txn_randomizer.py` is designed to pull a random sample of user_IDs from a persistent data storage (MongoDB) and sends transactions to that random sample of customer profiles. Many elements within the transaction payload are randomized such as payment_channel, payment_type, amount, and store.

These scripts make use of the [Faker Python Library](https://faker.readthedocs.io/en/master/), which randomizes most of the customer data, including first and last name, email address, and address. Further randomization is applied to the user_profile customer attributes to introduce variety in the custom profile attributes for the new customer profiles.

## Table of Contents
- [Python Dependencies](#python-dependencies)
- [MongoDB Setup](#mongodb-setup)
- [The Scripts](#the-scripts)
- [Usage](#usage)
  - [Arguments](#arguments)
- [Contributing](#contributing)
- [License](#license)

## Python Dependencies
Before running this project, ensure you have the following Python dependencies installed:

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

3. **Create the Databases**:
   - Open a MongoDB shell by running `mongo` in your terminal.
   - Authenticate as admin user
   - Create three new databases: retail_db, qsr_db and fuel_db
   - Create three users for each database. All to be named: retail_user, qsr_user, fuel_user
   - Use openssl to generate base64 passwords for each user: ❯ openssl rand -base64 48
   - Collections will be created upon the first run of the script

## The Scripts

> All scripts runs asynchronously! Be mindful of the important setting thresholds mentioned below to avoid negatively impacting an environment.

### generate-customers/generate_customer.py

This is the main script for generating random customer data. It accepts command-line arguments to control the environment context, locale, logging and whether transactions should be sent after the customer profiles are created. The script includes an important setting that determines the range of new customer profiles created each time the script runs. This range is a randomized value between a min and max value. The max value is the most important setting to pay attention to. It is recommended the range max never exceed 500 to avoid negatively impacting an environment.

> To find this range setting in `generate_customer.py` go to line 167: `for _ in range(random.randint(1, 10)):`

`generate_customer.py` expects a `--context` argument which determines which SessionM demo environment the script will execute against. Currently, this script is configured to only work with one of three demo environments, denoted by the argument values: retail, qsr or fuel. Each of the three contexts have specific data dictionaries for the customer profiles, allowing them to be further customized based on the customer data model within the respective demo environment.

This script can run to only generate customer profiles and without generating transactions so long as the `--sendTxns` argument is not included when the script is invoked (see usage example below).

### txn_randomizer.py
The purpose of this script is to send transactions against a randomized collection of existing users. The intent is to simulate realistic transaction activity against a random sample size of existing customer profiles. This script accepts the same `--context` argument as generate_customers.py. The script reads from the designated MongoDB and returns the entire collection. The full collection is then reduced to a sample size between 10% and 40%, which are then sent to `send_transactions.py`

> To find this range setting in `txn_randomizer.py`, go to line 72: `sample_percentage = random.uniform(0.1, 0.4)`

### send_transactions.py
> This is a utility script used by `generate_customer.py` and `txn_randomizer.py` and is not to be executed directly.

When the `--sendTxns` argument is used with the `generate_customer.py` script, first transactions will be sent to a randomized percentage of the newly generated customers. By default, the script only sends transactions to a randomized selection of 40% of the new customer profiles. It is not a realistic scenario for 100% of new customers to perform a first transaction. This setting can 100% if intended to be used for testing purposes and not to simulate real-world transaction behavior.

Similarly, `txn_randomizer.py` invokes send_transactions.py once the randomized sample size is selected. When logging is enabled, this script will only write the response status to the log file since the SessionM POS API does not return anything in the response other than a "200" code if the response is successful. Because of this, the log file also include the request JSON body to aid in troubleshooting.

## Usage

Navigate to your project directory and activate the virtual environment

   ```sh
   source .venv/bin/activate
   ```
### Using the main `generate_customer.py` Script
The main `generate_customer.py` script accepts important command-line arguments to customize its behavior. Before running the `generate_customer.py` script, familiarize yourself with the arguments below to ensure proper useage.

### Arguments
- `--context` (required): Specifies the demo environment context. Must be one of: retail, qsr or fuel.
- `--sendTxns` (optional): If included, invokes the `send_first_transactions.py` script to send first transactions to a randomized percentage of the the generated customers.
- `--locale` (required): Informs the Faker function to use a specific locale when randomly generating data. Can be any standard locale code but best to limit usage to one of: en_US, es_MX or pt_PT
- `--enableLogging` (optional): Logging is implicily false by design. If this argument is included logging is enabled, which writes a JSON file to a local directory. Each script has it's own log and concatenates every request and response body for testing and diagnosis. For this reason, it's best to exclude this argument unless absolutely necessary. Depending on your environment, your will need to ensure your script has write permissions on a local directory.

### Example Usage for generate_customer.py

1. **Generate QSR Customers with first transactions and with logging**:

   ```sh
   python generate_customers.py --context qsr --sendTxns --enableLogging
   ```

2. **Generate Retail Customers with first transactions with a Spanish/Mexico locale and without logging**:

   ```sh
   python generate_customers.py --context retail --local es_MX --sendTxns
   ```

3. **Generate QSR Customers without first transactions and without logging**:

   ```sh
   python generate_customers.py --context qsr
   ```

### Using the `txn_randomizer.py` Script
This script requires access to the same MongoDB used in the `generate_customer.py` script. This script will grab the entire collection and then apply filtering and randomization to the result_set in order to only send transactions to the sample of total customers created from the `generate_customer.py` script.

> The sample percentage is defined on line 72: sample_percentage = random.uniform(0.1, 0.4)

Depending on the use, this range can be increased to 100%, just be mindful that the `send_transactions.py` script runs asynchronously. The `send_transactions.py` also has protections in place to ensure a max number of transactions are never exceeded when calling the SessionM CLOUDPOS endpoint.

The `txn_randomizer.py` invokes the `send_transactions.py` script, which handles randomization of the transaction payload (e.g. payment_type, payment_channel).

### Arguments
- `--context` (required): Specifies the demo environment context. Must be one of: retail, qsr or fuel.
- `--enableLogging` (optional): Logging is implicily false by design. If this argument is included logging is enabled, which writes a JSON file to a local directory. Each script has it's own log and concatenates every request and response body for testing and diagnosis. For this reason, it's best to exclude this argument unless absolutely necessary. Depending on your environment, your will need to ensure your script has write permissions on a local directory.

### Example Usage for txn_randomizer.py

1. **Generate Random Transactions for the Existing QSR Customers with logging**:

   ```sh
   python txn_randomizer.py --context qsr --enableLogging
   ```

2. **Generate Random Transactions for the Existing Retail Customers without logging**:

   ```sh
   python txn_randomizer.py --context retail
   ```

## Contributing

This is a private project and not open to public contribution.

## License

This project is licensed under the MIT License.

---