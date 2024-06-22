# Generate Customers and Send First Transactions

## Overview

This project generates random customer data against a specific SessionM demo environment and, optionally, sends a first transaction to a randomized percentage of the newly generated customers. The project is designed to be run exclusively from the `generate_customer.py` script, along wih the arguments outlined below.

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

You can install the required Python packages using the following command:

```sh
pip install pymongo faker
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

### Example Usage

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

## Scripts

### generate_customer.py

This is the main script for generating random customer data. It accepts command-line arguments to control the number of customers generated and whether to invoke the transaction script. It includes an important setting that determines the range of new customer profiles created. This range is always random and between a min and max value. The max value is the most important setting to pay attention to. It is recommended this never exceed 500.

This script can run indepdently and without generating transactions so long as the --sendTxns argument is not included when the script is invoked (see usage example above).

### send_first_transactions.py

This script is only invoked by `generate_customer.py` when the `--sendTxns` argument is included. This script handles sending first transactions to a randomized percentage of the newly generated customers. By default, the script only sends transactions to a randomized 40% of the new customer profiles. It is not a realistic scenario for 100% of new customers to perform a first transaction. This setting can be set to 100% if used for testing purposes and not to simulate real-world transaction behavior.

## Contributing

This is a private project and not open to public contribution.

## License

This project is licensed under the MIT License.

---