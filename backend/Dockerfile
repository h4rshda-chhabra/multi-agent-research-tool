FROM python:3.11-slim

WORKDIR /app

# No system packages required — WeasyPrint (GTK) is not used in this image;
# PDF export falls back to fpdf2 (pure Python, no native deps).

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
