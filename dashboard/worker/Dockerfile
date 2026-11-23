FROM node:22-bookworm-slim AS node
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /opt/npm
RUN node /opt/npm/bin/npm-cli.js install --omit=dev @vercel/blob@2
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py snapshot.mjs ./
ENV HOSTED_WORKER=1 PYTHONUNBUFFERED=1
CMD ["python", "worker.py"]
