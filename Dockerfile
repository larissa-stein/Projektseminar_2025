FROM python:3.11-slim

# Installiere deutsche Locale
RUN apt-get update && apt-get install -y locales \
 && echo "de_DE.UTF-8 UTF-8" > /etc/locale.gen \
 && locale-gen de_DE.UTF-8 \
 && update-locale LANG=de_DE.UTF-8

# Setze Environment-Variable
ENV LANG=de_DE.UTF-8
ENV LANGUAGE=de_DE:de
ENV LC_ALL=de_DE.UTF-8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_main.py"]
