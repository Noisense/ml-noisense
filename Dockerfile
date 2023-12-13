FROM python:3.9

# Set direktori kerja
WORKDIR /app

# Instal pustaka-pustaka yang diperlukan
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# Salin skrip Python ETL ke kontainer
COPY ./app .

# Jalankan skrip ETL saat kontainer dijalankan
CMD ["python", "etl.py"]
