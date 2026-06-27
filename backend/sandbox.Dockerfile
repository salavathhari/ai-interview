# Using a lightweight python image
FROM python:3.11-slim

# Create a non-privileged user to run the code
RUN useradd -m sandboxuser

WORKDIR /sandbox

# Set common environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Default command is just to wait for input
USER sandboxuser
CMD ["python", "code.py"]
