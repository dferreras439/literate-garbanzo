# Use the official Python 3.11.11 image
FROM python:3.11.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Run main.py and terminate the container after 60 minutes
CMD ["sh", "-c", "python main.py && sleep 3600 && exit"]
