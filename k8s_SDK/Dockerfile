FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV HOST=0.0.0.0
ENV PORT=8000


COPY utils ./utils
COPY main.py handlers.py job.py db.py schemas.py /app/


ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]