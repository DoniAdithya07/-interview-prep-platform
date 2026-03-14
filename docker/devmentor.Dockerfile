FROM node:22-alpine

WORKDIR /app

COPY devmentor/package.json devmentor/package-lock.json ./
RUN npm ci

COPY devmentor ./

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
