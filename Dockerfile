FROM python:3.8-slim

# Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# Copy the current directory contents into the container at /app
WORKDIR /app
COPY ./requirements.txt /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get install -y libglib2.0-dev

COPY . .

EXPOSE 5000
ENV FLASK_APP=server.py
CMD ["flask", "run", "--host", "0.0.0.0"]


