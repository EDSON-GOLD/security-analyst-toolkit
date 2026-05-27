FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install flask
RUN python3 init_db.py
CMD ["python3", "app.py"]