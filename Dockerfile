FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY app ./app
COPY profile ./profile
COPY data ./data

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

ENTRYPOINT ["portfoliofit"]
CMD ["--help"]
