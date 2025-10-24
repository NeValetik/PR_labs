FROM python:3.13-slim
WORKDIR /lab1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m labuser && chown -R labuser:labuser /lab1
USER labuser

EXPOSE 6789

CMD ["python", "src/server.py"]