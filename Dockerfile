FROM python:3.11-slim

WORKDIR /app

COPY aws_nyc/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY aws_nyc/ .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "with_memory.py", "--server.address", "0.0.0.0"]
