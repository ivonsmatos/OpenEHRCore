
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Run gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
# For development, we use runserver as specified in docker-compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
