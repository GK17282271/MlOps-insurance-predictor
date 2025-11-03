FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and model (CI ensures model.pkl exists in app/ before docker build context)
COPY . .

EXPOSE 5000
# Use gunicorn for production; binds to 0.0.0.0:5000 and serves the Flask `app` object from app.py
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
