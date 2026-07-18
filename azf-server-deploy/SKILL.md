---
name: azf-server-deploy
description: >-
  An Zhaofeng's server deployment conventions. Use when deploying, updating,
  inspecting, backing up, or troubleshooting Docker, Docker Compose, reverse
  proxies, databases, self-hosted services, n8n, webhooks, or server-side
  automation on An Zhaofeng's servers. Prefer the default service root
  /anzhaofeng/{service-name} unless an existing server convention clearly says
  otherwise.
---

# AZF Server Deploy

Use this skill for An Zhaofeng's server operation and Docker deployment conventions. Stable server hardware facts belong in the Obsidian asset card `新云数据香港CN2云服务器`; this skill records how services should be arranged and maintained.

## Default Docker Location

- Default root directory for Docker services: `/anzhaofeng`
- Each service gets its own subdirectory: `/anzhaofeng/<service-name>`
- For n8n, use: `/anzhaofeng/n8n`

Preferred service layout:

```text
/anzhaofeng/<service-name>
  docker-compose.yml
  .env
  data/
  logs/
  backup/
```

For services with a database, use a clear subdirectory, for example:

```text
/anzhaofeng/n8n
  docker-compose.yml
  .env
  n8n_data/
  postgres_data/
  backup/
  logs/
```

## Deployment Rules

- Prefer Docker Compose for self-hosted services.
- Keep each service isolated in its own directory.
- Store runtime secrets in `.env`; do not write passwords into skills, README files, chat summaries, or public notes.
- Before deploying, inspect whether `/anzhaofeng` already exists and whether the target service directory has existing files.
- Before changing an existing service, back up `docker-compose.yml`, `.env` if safe to copy locally, and important data volumes when practical.
- Use `Asia/Shanghai` for service timezone settings unless the service clearly needs another timezone.
- Prefer PostgreSQL for durable n8n deployments instead of long-term SQLite.
- For public services, use HTTPS through a reverse proxy such as Caddy or Nginx, and avoid exposing admin panels without authentication.
- After deployment, report service URL, install path, container status, and any unresolved security or backup tasks.

## Current n8n Deployment

- Server: 新云数据香港 CN2 云服务器，`103.56.112.21`
- Path: `/anzhaofeng/n8n`
- Public URL for initial setup: `http://103.56.112.21:5678/`
- Current stack: `n8nio/n8n:2.22.5` + `postgres:16-alpine` + `n8nio/runners:2.22.5`
- Database: PostgreSQL, data directory `postgres_data/`
- n8n data directory: `n8n_data/`
- Backup directory: `backup/`
- Timezone: `Asia/Shanghai`
- Secrets: stored only in server-side `.env`; never record them in skills or README files
- Status on 2026-05-31: deployed and verified with HTTP 200 from both server localhost and local Windows machine
- Temporary limitation: direct HTTP by IP is only suitable for first setup/testing; prefer domain + HTTPS reverse proxy or access restriction before regular use

## n8n Preference

Default n8n deployment path:

```text
/anzhaofeng/n8n
```

Preferred initial n8n stack:

- `n8n`
- `postgres`
- External task runner when the server can spare memory, especially for newer n8n versions
- Reverse proxy / HTTPS if a domain is available

Scale-up path when executions become heavy:

- Add Redis.
- Add n8n worker containers.
- Move to n8n queue mode so the editor/API process is less affected by heavy workflow execution.
