# Base image
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies needed for Next.js (libc6-compat)
RUN apk add --no-cache libc6-compat

# Install dependencies
COPY package.json package-lock.json* ./
# Use legacy-peer-deps to avoid conflicts with newer React/Next versions
RUN npm install --legacy-peer-deps

# Build args
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the app
COPY . .
RUN npm run build

# Production image
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Install libc6-compat in runner as well if needed for runtime binaries
RUN apk add --no-cache libc6-compat

ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/.next/standalone ./

EXPOSE 3000

CMD ["node", "server.js"]
