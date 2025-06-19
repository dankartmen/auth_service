# Используем официальный образ Python
FROM python:3.9

# Рабочая директория
WORKDIR /app

COPY . .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
