# ── Stage 1: Build React app ────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

# ── Stage 2: One-shot file copier (exits immediately) ───────────────
# This container copies /dist → /html (the shared volume) and exits 0.
# nginx gateway mounts the same volume and serves the files.
FROM busybox:1.36
COPY --from=builder /app/dist /dist
CMD ["/bin/sh", "-c", "cp -r /dist/. /html/ && echo 'Frontend ready'"]
