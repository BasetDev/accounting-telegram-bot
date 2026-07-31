module.exports = {
  apps: [
    {
      name: "hesab-bot",
      cwd: "/home/hesab/app",
      script: "hesab/main.py",
      interpreter: "/home/hesab/app/venv/bin/python",
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONDONTWRITEBYTECODE: "1",
      },
      // Restart policy — conservative for micro-server
      restart_delay: 8000,
      max_restarts: 15,
      min_uptime: "15s",
      exp_backoff_restart_delay: 500,
      // CRITICAL: 150M limit — OS+PM2 use ~80MB, leaving headroom on 256MB server
      max_memory_restart: "150M",
      // Log configuration
      error_file: "/home/hesab/app/logs/pm2-error.log",
      out_file: "/home/hesab/app/logs/pm2-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      // Graceful shutdown — shorter for micro-server
      kill_timeout: 15000,
      listen_timeout: 10000,
      shutdown_with_message: false,
      // Watch (disabled for production)
      watch: false,
      // PM2's own memory limit
      node_args: ["--max-old-space-size=30"],
      // Reduce PM2 overhead
      vizion: false,
      autorestart: true,
    },
  ],
};
