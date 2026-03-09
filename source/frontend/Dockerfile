FROM python:3.12-slim

WORKDIR /src
COPY src/pyproject.toml .
COPY src/uv.lock .
RUN pip install uv
RUN uv sync

COPY . .

CMD ["uv", "run", "python", "src/main.py"]
