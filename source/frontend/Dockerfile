FROM python:3.12-slim

WORKDIR /app
COPY app/pyproject.toml .
COPY app/uv.lock .
RUN pip install uv
RUN uv sync

COPY . .

CMD ["uv", "run", "python", "app/main.py"]
