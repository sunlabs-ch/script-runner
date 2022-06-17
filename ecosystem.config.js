const defaultConfig = {
  restart_delay: "5000",
  max_restarts: "10",
  max_memory_restart: "1G",
  autorestart: true,
};

module.exports = {
  apps: [
    {
      ...defaultConfig,
      name: "TokenSet Notifications",
      interpreter: "/usr/bin/python3",
      cwd: "scripts/SWDTokenSetNotifications",
      script: "main.py",
    },
  ],
};
