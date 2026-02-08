{
  config,
  pkgs,
  lib,
  helpers,
  ...
}:

let
  enable = helpers.hasIn "services" "task-manager";

  gitRepo = "https://github.com/umokee/jsddsfjlskdfj.git";
  gitBranch = "claude/review-refactored-code-EWP7N";
  # gitBranch = "claude/fix-missed-day-roll-8h2dP";

  domain = "tasks.umkcloud.xyz";
  publicPort = 8888;
  backendPort = 8000;
  backendHost = "127.0.0.1";

  # IP whitelist — добавь свои IP (должны совпадать с word-forge.nix)
  allowedIPs = [
    "127.0.0.1" # VPN (sing-box) трафик — не убирать!
    "178.218.98.184"
    # "1.2.3.4"          # твой домашний IP
    # "5.6.7.0/24"       # диапазон мобильного оператора
  ];

  projectPath = "/var/lib/task-manager";
  secretsDir = "/var/lib/task-manager-secrets";
  logDir = "/var/log/task-manager";
  frontendBuildDir = "${projectPath}/frontend/dist";

  user = "task-manager";
  group = "task-manager";

  nodeDeps = with pkgs; [
    nodejs
    nodePackages.npm
  ];
in
{
  config = lib.mkIf enable {
    users.users.${user} = {
      isSystemUser = true;
      group = group;
      description = "Task Manager service user";
      home = projectPath;
    };
    users.groups.${group} = { };

    # Открываем порт для внешнего доступа (защита через IP whitelist)
    networking.firewall.allowedTCPPorts = [ publicPort ];

    systemd.tmpfiles.rules = [
      "d ${projectPath} 0755 ${user} ${group} -"
      "d ${secretsDir} 0700 ${user} ${group} -"
      "d ${logDir} 0750 ${user} ${group} -"
      "f ${logDir}/app.log 0640 ${user} ${group} -"
    ];

    sops.secrets."task-manager-api" = {
      owner = user;
    };

    sops.templates."task-manager-env" = {
      content = ''
        TASK_MANAGER_API_KEY=${config.sops.placeholder."task-manager-api"}
      '';
      owner = user;
      group = group;
    };

    systemd.services.task-manager-git-sync = {
      description = "Sync Task Manager from Git";
      wantedBy = [ "multi-user.target" ];
      after = [
        "systemd-tmpfiles-setup.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      requires = [ "systemd-tmpfiles-setup.service" ];
      path = [
        pkgs.git
        pkgs.coreutils
        pkgs.bash
      ];

      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        User = user;
        Group = group;
      };

      script = ''
        set -e

        mkdir -p ${projectPath}
        chmod 755 ${projectPath}

        if [ -d ${projectPath}/.git ]; then
          cd ${projectPath}
          ${pkgs.git}/bin/git fetch origin
          ${pkgs.git}/bin/git checkout ${gitBranch}
          ${pkgs.git}/bin/git reset --hard origin/${gitBranch}
          ${pkgs.git}/bin/git pull origin ${gitBranch}
        else
          rm -rf ${projectPath}/*
          rm -rf ${projectPath}/.* 2>/dev/null || true
          cd ${projectPath}
          ${pkgs.git}/bin/git clone -b ${gitBranch} ${gitRepo} .
        fi

        chmod -R u+w ${projectPath}
        echo "Git sync completed successfully"
      '';
    };

    systemd.services.task-manager-frontend-build = {
      description = "Build Task Manager Frontend";
      after = [ "task-manager-git-sync.service" ];
      requires = [ "task-manager-git-sync.service" ];
      wantedBy = [ "multi-user.target" ];
      path = nodeDeps ++ [
        pkgs.coreutils
        pkgs.bash
      ];

      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        User = user;
        Group = group;
        WorkingDirectory = "${projectPath}/frontend";
      };

      script = ''
        set -e

        if [ ! -d ${projectPath}/frontend ]; then
          echo "Error: Frontend directory does not exist"
          exit 1
        fi

        cd ${projectPath}/frontend

        echo "Installing frontend dependencies..."
        ${pkgs.nodejs}/bin/npm install

        echo "Building frontend..."
        ${pkgs.nodejs}/bin/npm run build

        echo "Frontend build completed successfully"
        ls -la dist/
      '';
    };

    systemd.services.task-manager-backend = {
      description = "Task Manager API Backend";
      after = [
        "task-manager-git-sync.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      requires = [
        "task-manager-git-sync.service"
      ];
      wantedBy = [ "multi-user.target" ];

      environment = {
        TASK_MANAGER_LOG_DIR = logDir;
        TASK_MANAGER_LOG_FILE = "app.log";
        PYTHONPATH = projectPath;
      };

      path = [
        pkgs.python312
        pkgs.gcc
        pkgs.stdenv.cc
        pkgs.zlib
      ];

      serviceConfig = {
        Type = "simple";
        User = user;
        Group = group;
        WorkingDirectory = projectPath;
        TimeoutStartSec = "infinity";

        EnvironmentFile = config.sops.templates."task-manager-env".path;
        ExecStart = "${projectPath}/venv/bin/uvicorn backend.main:app --host ${backendHost} --port ${toString backendPort}";
        Restart = "always";
        RestartSec = "10";

        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "full";
        ProtectHome = true;
        ReadWritePaths = [
          logDir
          projectPath
        ];

        StandardOutput = "journal";
        StandardError = "journal";
        SyslogIdentifier = "task-manager-backend";
      };

      preStart = ''
        if [ ! -d ${projectPath} ]; then
          echo "Error: ${projectPath} does not exist"
          exit 1
        fi

        if [ ! -d ${projectPath}/venv ]; then
          echo "Creating virtualenv..."
          ${pkgs.python312}/bin/python -m venv ${projectPath}/venv
        fi

        echo "Installing dependencies from requirements.txt..."
        ${projectPath}/venv/bin/pip install --upgrade pip
        ${projectPath}/venv/bin/pip install -r ${projectPath}/backend/requirements.txt
      '';
    };

    systemd.services.task-manager-update = {
      description = "Update Task Manager";

      path = [
        pkgs.coreutils
        pkgs.systemd
      ];

      serviceConfig = {
        Type = "oneshot";
      };

      script = ''
        set -e
        echo "=== Updating Task Manager ==="

        echo "[1/7] Stopping backend..."
        ${pkgs.systemd}/bin/systemctl stop task-manager-backend

        echo "[2/7] Updating code from Git..."
        ${pkgs.systemd}/bin/systemctl restart task-manager-git-sync
        sleep 2

        echo "[3/7] Recreating Python environment..."
        if [ -d ${projectPath}/venv ]; then
          echo "Removing old venv..."
          rm -rf ${projectPath}/venv
        fi

        echo "[4/7] Rebuilding frontend..."
        ${pkgs.systemd}/bin/systemctl restart task-manager-frontend-build
        sleep 3

        echo "[5/7] Starting backend..."
        ${pkgs.systemd}/bin/systemctl start task-manager-backend
        sleep 5

        echo "[6/7] Checking backend status..."
        if ! ${pkgs.systemd}/bin/systemctl is-active --quiet task-manager-backend; then
          echo "ERROR: Backend failed to start!"
          ${pkgs.systemd}/bin/systemctl status task-manager-backend --no-pager || true
          exit 1
        fi

        echo "[7/7] Reloading reverse proxy..."
        ${pkgs.systemd}/bin/systemctl reload nginx

        echo "Done!"
        echo ""
      '';
    };

    # --- nginx reverse proxy (HTTP + IP whitelist) ---
    services.nginx = {
      enable = lib.mkDefault true;

      recommendedGzipSettings = lib.mkDefault true;
      recommendedOptimisation = lib.mkDefault true;
      recommendedProxySettings = lib.mkDefault true;

      proxyTimeout = "60s";

      # IP whitelist через geo модуль
      commonHttpConfig = ''
        proxy_headers_hash_max_size 1024;
        proxy_headers_hash_bucket_size 128;

        geo $tm_allowed {
          default 0;
          ${lib.concatMapStrings (ip: "${ip} 1;\n          ") allowedIPs}
        }
      '';

      virtualHosts."${domain}" = {
        listen = [
          { addr = "0.0.0.0"; port = publicPort; }
        ];

        locations."/api/" = {
          proxyPass = "http://${backendHost}:${toString backendPort}";
          extraConfig = ''
            if ($tm_allowed = 0) { return 403; }

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
          '';
        };

        locations."/" = {
          root = frontendBuildDir;
          tryFiles = "$uri $uri/ /index.html";
          extraConfig = ''
            if ($tm_allowed = 0) { return 403; }
          '';
        };

        locations."~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$" = {
          root = frontendBuildDir;
          extraConfig = ''
            if ($tm_allowed = 0) { return 403; }
            add_header Cache-Control "public, max-age=31536000, immutable";
            access_log off;
          '';
        };
      };
    };
  };
}
