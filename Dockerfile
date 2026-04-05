# Use the official Python 3.11 slim image as a base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
# The .dockerignore file will prevent copying venv, .env, etc.
COPY . .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
# This port is specified for Hugging Face Spaces
EXPOSE 7860

# Define the command to run the application
# Use uvicorn to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
