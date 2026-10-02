# syntax=docker/dockerfile:1
# ------------------------------------------------------------------------------
# Stage 1: Install dependencies
# ------------------------------------------------------------------------------
FROM node:22-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy root workspace manifests
COPY package.json package-lock.json ./
COPY packages/api-types/package.json ./packages/api-types/
COPY apps/web/package.json ./apps/web/

RUN npm ci

# ------------------------------------------------------------------------------
# Stage 2: Build Next.js application
# ------------------------------------------------------------------------------
FROM node:22-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages/api-types/node_modules ./packages/api-types/node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules

COPY package.json package-lock.json tsconfig.json* ./
COPY packages ./packages
COPY apps/web ./apps/web

ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

RUN npm run build:web

# ------------------------------------------------------------------------------
# Stage 3: Minimal production runner
# ------------------------------------------------------------------------------
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static assets and standalone server
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-3000}/api/health || exit 1

CMD ["node", "apps/web/server.js"]
