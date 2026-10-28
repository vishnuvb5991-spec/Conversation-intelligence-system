FROM node:22-alpine AS ui-build
WORKDIR /ui
COPY package*.json ./
RUN npm ci
COPY index.html ./
COPY src ./src
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=ui-build /ui/dist ./dist
EXPOSE 8000
CMD uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8000}"
