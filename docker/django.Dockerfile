# Use official Python image
FROM python:3.11

RUN apt-get update && apt-get install -y netcat-openbsd

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

COPY .env /app/.env

# Copy requirements first to leverage Docker caching
COPY Globetrotter/requirements.txt /app/

# Install dependencies globally (without virtualenv)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy Django project
COPY Globetrotter/ /app/

# Expose port 8000
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
