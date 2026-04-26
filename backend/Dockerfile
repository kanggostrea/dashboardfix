FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY panel_registry.py .
COPY discovery_service.py .COPY --chown=root:root ../frontend /app/frontend
EXPOSE 5000
CMD ["python", "app.py"]
