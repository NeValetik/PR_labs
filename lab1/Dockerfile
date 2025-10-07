FROM python:3.13-slim
WORKDIR /lab1

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create user and set permissions
RUN useradd -m labuser && chown -R labuser:labuser /lab1
USER labuser

EXPOSE 6789

CMD ["python", "src/server.py", "src/content"]