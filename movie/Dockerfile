FROM python:3.14-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY movie .

CMD ["python", "movie.py"]
