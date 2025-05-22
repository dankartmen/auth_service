# Используем официальный образ Python
FROM python:3.9

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY ./app /app

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
