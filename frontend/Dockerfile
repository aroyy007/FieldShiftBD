FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 8082

CMD ["npx", "expo", "start", "--host", "lan", "--port", "8082"]
