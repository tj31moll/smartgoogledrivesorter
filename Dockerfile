# Use the official Python image as the base image
FROM python:3.8

# Set the working directory
WORKDIR /app2

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3636
# Copy the Python script and credentials file
COPY main.py credentials.json ./



# Set the entry point
ENTRYPOINT ["python", "main.py"]
