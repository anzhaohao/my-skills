# 服务器 Docker 部署规范 Skill

这个 skill 用来记录 An Zhaofeng 的服务器部署习惯，尤其是 Docker、Docker Compose、n8n、自托管服务、反向代理、备份和服务目录结构。

## 什么时候使用

- 在服务器上部署 Docker 服务时。
- 更新、迁移、排查已有 Docker Compose 服务时。
- 部署 n8n、数据库、反向代理、Webhook、自动化服务时。
- 需要判断服务目录、备份位置、日志位置、环境变量管理方式时。

## 核心约定

Docker 服务默认部署在根目录下的个人文件夹：

```text
/anzhaofeng/<service-name>
```

例如：

```text
/anzhaofeng/n8n
/anzhaofeng/mysql
/anzhaofeng/one-api
/anzhaofeng/frp
```

推荐目录结构：

```text
/anzhaofeng/<service-name>
  docker-compose.yml
  .env
  data/
  logs/
  backup/
```

## 当前 n8n 部署

- 服务器：新云数据香港 CN2 云服务器，`103.56.112.21`
- 安装位置：`/anzhaofeng/n8n`
- 初始访问地址：`http://103.56.112.21:5678/`
- 当前镜像：`n8nio/n8n:2.22.5`、`postgres:16-alpine`、`n8nio/runners:2.22.5`
- 数据库：PostgreSQL，数据目录 `postgres_data/`
- n8n 数据目录：`n8n_data/`
- 备份目录：`backup/`
- 时区：`Asia/Shanghai`
- 私密信息：只保存在服务器 `.env`，不写入 skill 或 README
- 2026-05-31 验证结果：服务器本机访问和本地 Windows 公网访问均返回 HTTP 200
- 临时限制：目前是 IP + HTTP 直连，正式长期使用前建议配置域名 + HTTPS 反向代理，或限制来源 IP/改用 SSH 隧道

## n8n 默认方案

n8n 默认安装位置：

```text
/anzhaofeng/n8n
```

推荐初始栈：

- n8n
- PostgreSQL
- 新版本 n8n 可搭配 external task runner，减少主进程执行任务的压力
- 有域名时使用 Caddy 或 Nginx 做 HTTPS 反向代理

后续如果工作流执行变重，再升级为 Redis + n8n worker 队列模式。

## 安全规则

- 密码、API key、token、私钥不写入 skill 或 README。
- `.env` 只保留在服务器本地，不复制到公开位置。
- 公网服务优先启用 HTTPS。
- 修改已有服务前，尽量先备份 compose 文件和重要数据。
- Docker 发布端口可能绕过普通 UFW 规则，公网管理面板需要额外确认访问控制。

## 最近维护

- 2026-05-31：记录 n8n 已部署到 `/anzhaofeng/n8n`，当前栈为 n8n 2.22.5 + PostgreSQL 16 + external task runner，并记录临时 HTTP 入口和后续 HTTPS 建议。
- 2026-05-31：新建 skill，记录默认 Docker 部署根目录 `/anzhaofeng`，并明确 n8n 默认部署到 `/anzhaofeng/n8n`。
