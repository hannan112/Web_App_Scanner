# Deployment scripts

These scripts assume a self-hosted deployment (e.g. a DigitalOcean droplet) reachable over SSH,
with the repo checked out at `~/Web_App_Scanner` and running via `deployment/docker-compose.prod.yml`.

They read their target server from environment variables instead of hardcoding it, so set these
before running any of them:

```bash
export DEPLOY_SSH_KEY=~/.ssh/your_deploy_key
export DEPLOY_SERVER=root@your-server-ip-or-domain
export DEPLOY_DOMAIN=api.your-domain.com
export DEPLOY_FRONTEND_ORIGINS=https://your-domain.com,https://your-frontend.vercel.app
```

- `deploy_changes.sh` — pushes local commits, then SSHes in to pull, rebuild, and update CORS/host config on the server. Refuses to run if you have uncommitted local changes (commit them yourself first).
- `update_cors.sh` — just updates `CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS` on the server without a full deploy.
- `sync_db.sh` — downloads the production SQLite DB to your local machine for debugging. Only relevant if you're running SQLite in production; back up your local DB first (this script does that automatically).
- `restart_containers.sh` / `restart_zap.sh` — restart the named Docker containers locally or on a server you're already SSHed into.
