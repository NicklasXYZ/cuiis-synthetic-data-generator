# Use an official lightweight Python image: https://hub.docker.com/_/python
FROM python:3.12-slim as python-base

# Set environment variables:
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install fastapi \
    "uvicorn[standard]" \
    "celery[redis]" \
    httpx \
    flower \
    matplotlib \
    scipy \
    numpy \
    redis \
    pyyaml \
    pyproj \
    shapely \
    jinja2

COPY . /genserver

WORKDIR /genserver

# Command to run the uvicorn server
# CMD ["uvicorn", "genserver:app", "--host", "0.0.0.0", "--port", "8080"]