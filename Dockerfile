FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py ./run.py

ENV HEADLESS=true
ENV PORT=3000
EXPOSE 3000

CMD ["python", "run.py"]
