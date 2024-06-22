# Generate Customers and Send First Transactions

## Overview

This project generates random customer data and, optionally, sends a first transaction to a randomized percentage of the new customers. The project is designed to be run exclusively from the `generate_customer.py` script.

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

Run the `generate_customer.py` script to generate random customer data. This script accepts command-line arguments to customize its behavior.

### Arguments

- `--context` (required): Specifies the demo environment context: expects retail, qsr or fuel.
- `--sendTxns` (optional): If included, invokes the `send_first_transactions.py` script to send the first transactions for the generated customers.
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

This is the main script for generating random customer data. It accepts command-line arguments to control the number of customers generated and whether to invoke the transaction script.

### send_first_transactions.py

This script is invoked by `generate_customer.py` if the `--sendTxns` argument is included. It handles sending the first transactions for the generated customers.

## Contributing

This is a private project and not open to public contribution.

## License

This project is licensed under the MIT License.

---

## Example Code Snippets

### generate_customer.py

```python
import argparse
from pymongo import MongoClient
from faker import Faker
import subprocess

def generate_customers(num_customers):
    fake = Faker()
    client = MongoClient('localhost', 27017)
    db = client.mydatabase
    customers = db.customers

    for _ in range(num_customers):
        customer = {
            'name': fake.name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'address': fake.address()
        }
        customers.insert_one(customer)

    client.close()

def main():
    parser = argparse.ArgumentParser(description='Generate random customers.')
    parser.add_argument('--num_customers', type=int, required=True, help='Number of customers to generate')
    parser.add_argument('--sendTxns', action='store_true', help='Send first transactions for the customers')
    args = parser.parse_args()

    generate_customers(args.num_customers)

    if args.sendTxns:
        subprocess.call(['python', 'send_first_transactions.py'])

if __name__ == '__main__':
    main()
```

### send_first_transactions.py

```python
from pymongo import MongoClient
from faker import Faker

def send_transactions():
    fake = Faker()
    client = MongoClient('localhost', 27017)
    db = client.mydatabase
    customers = db.customers.find()

    for customer in customers:
        transaction = {
            'customer_id': customer['_id'],
            'amount': fake.random_number(digits=5),
            'date': fake.date_time_this_year()
        }
        db.transactions.insert_one(transaction)

    client.close()

if __name__ == '__main__':
    send_transactions()
```

---
