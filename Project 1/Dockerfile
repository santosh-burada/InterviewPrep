# Base image
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY main.py database.json /app/

# Set Flask environment variables
# ENV FLASK_APP=main.py
# ENV FLASK_RUN_PORT=80
# ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 80

# Command to run the application
# CMD ["flask", "run"]
CMD ["python", "main.py"]
