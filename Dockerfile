# Use a Python base image for your application
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port the app will run on
EXPOSE 8080

# Define the command to start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
#FKKKKKKK