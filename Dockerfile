# Use an official Python runtime as a base image
FROM python:3.9-slim  # ✅ Using 'slim' reduces image size

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first (for caching dependencies)
COPY requirements.txt .  # ✅ Optimized layer caching

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .  # ✅ Copying code after installing dependencies

# Expose port 5000 for Flask
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0  # ✅ Ensures Flask runs inside the container properly

# Run the application
CMD ["python", "app.py"]
