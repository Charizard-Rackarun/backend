FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para compilar drivers do Postgres se necessário
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte do backend
COPY . .

# Comando para iniciar a API com Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]