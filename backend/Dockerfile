FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && apt-get clean

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "app.py"]

EXPOSE 5000
