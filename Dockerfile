# Use the official Python image from the Docker Hub
FROM python:3.9

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /usr/src/app

# Install any global dependencies (if any)
# RUN pip install some-global-dependency

# Copy the requirements.txt file into the container
COPY requirements.txt /usr/src/app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /usr/src/app/

# Specify the command to run the application
# Adjust the CMD line based on the script you want to run, for example:
# CMD ["python", "customers/generate_customers.py"]
CMD ["python", "customers/generate_customers.py"]
