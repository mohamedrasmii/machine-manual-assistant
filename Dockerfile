FROM python:3.11-slim

WORKDIR /app

# CPU-only PyTorch keeps the image much smaller
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main2.py rag2.py ingest.py index.html script.js ./

EXPOSE 8000

CMD ["uvicorn", "main2:app", "--host", "0.0.0.0", "--port", "8000"]
