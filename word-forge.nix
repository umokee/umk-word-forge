{
  config,
  pkgs,
  lib,
  helpers,
  ...
}:

let
  enable = helpers.hasIn "services" "wordforge";

  gitRepo = "https://github.com/umokee/umk-word-forge.git";
  gitBranch = "main";

  domain = "words.umkcloud.xyz";
  publicPort = 8889;
  backendPort = 8001;
  backendHost = "127.0.0.1";

  # IP whitelist — добавь свои IP (домашний, мобильный оператор, и т.д.)
  allowedIPs = [
    "127.0.0.1" # VPN (sing-box) трафик — не убирать!
    "178.218.98.184"
    # "1.2.3.4"          # твой домашний IP
    # "5.6.7.0/24"       # диапазон мобильного оператора
  ];

  projectPath = "/var/lib/wordforge";
  secretsDir = "/var/lib/wordforge-secrets";
  logDir = "/var/log/wordforge";
  dataDir = "${projectPath}/data";
  frontendBuildDir = "${projectPath}/frontend/dist";

  user = "wordforge";
  group = "wordforge";

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
      description = "WordForge service user";
      home = projectPath;
    };
    users.groups.${group} = { };

    # Открываем порт для внешнего доступа (защита через IP whitelist)
    networking.firewall.allowedTCPPorts = [ publicPort ];

    systemd.tmpfiles.rules = [
      "d ${projectPath} 0755 ${user} ${group} -"
      "d ${secretsDir} 0700 ${user} ${group} -"
      "d ${logDir} 0750 ${user} ${group} -"
      "d ${dataDir} 0750 ${user} ${group} -"
      "f ${logDir}/app.log 0640 ${user} ${group} -"
    ];

    # --- Secrets (sops-nix) ---
    sops.secrets."word-forge/gemini-key" = {
      owner = user;
    };

    sops.templates."wordforge-env" = {
      content = ''
        GEMINI_API_KEY=${config.sops.placeholder."word-forge/gemini-key"}
        DATABASE_URL=sqlite:///${dataDir}/wordforge.db
        CORS_ORIGINS=http://${domain}:${toString publicPort},http://127.0.0.1:${toString publicPort}
        DEBUG=false
        WORDFORGE_LOG_DIR=${logDir}
        WORDFORGE_LOG_FILE=app.log
      '';
      owner = user;
      group = group;
    };

    # --- Git sync ---
    systemd.services.wordforge-git-sync = {
      description = "Sync WordForge from Git";
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

    # --- Frontend build ---
    systemd.services.wordforge-frontend-build = {
      description = "Build WordForge Frontend";
      after = [ "wordforge-git-sync.service" ];
      requires = [ "wordforge-git-sync.service" ];
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

    # --- Backend (uvicorn) ---
    systemd.services.wordforge-backend = {
      description = "WordForge API Backend";
      after = [
        "wordforge-git-sync.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      requires = [
        "wordforge-git-sync.service"
      ];
      wantedBy = [ "multi-user.target" ];

      environment = {
        WORDFORGE_LOG_DIR = logDir;
        WORDFORGE_LOG_FILE = "app.log";
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

        EnvironmentFile = config.sops.templates."wordforge-env".path;
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
          dataDir
        ];

        StandardOutput = "journal";
        StandardError = "journal";
        SyslogIdentifier = "wordforge-backend";
      };

      preStart = ''
        mkdir -p ${dataDir}

        if [ ! -d ${projectPath}/venv ]; then
          echo "Creating virtualenv..."
          ${pkgs.python312}/bin/python -m venv ${projectPath}/venv
        fi

        echo "Installing Python dependencies..."
        ${projectPath}/venv/bin/pip install --upgrade pip
        ${projectPath}/venv/bin/pip install -r ${projectPath}/backend/requirements.txt

        # Seed database on first run (if empty)
        if [ ! -f ${dataDir}/wordforge.db ]; then
          echo "First run detected — seeding database with 5000 words..."
          cd ${projectPath}
          DATABASE_URL=sqlite:///${dataDir}/wordforge.db ${projectPath}/venv/bin/python -m backend.seed --count 5000
          echo "Seed completed"
        fi

        # Run migrations for existing databases
        if [ -f ${dataDir}/wordforge.db ]; then
          echo "Running database migrations..."
          cd ${projectPath}
          ${projectPath}/venv/bin/python migrate_db.py || echo "Migration completed or not needed"
        fi
      '';
    };

    # --- One-shot update service ---
    systemd.services.wordforge-update = {
      description = "Update WordForge";

      path = [
        pkgs.coreutils
        pkgs.systemd
      ];

      serviceConfig = {
        Type = "oneshot";
      };

      script = ''
        set -e
        echo "=== Updating WordForge ==="

        echo "[1/7] Stopping backend..."
        ${pkgs.systemd}/bin/systemctl stop wordforge-backend

        echo "[2/7] Updating code from Git..."
        ${pkgs.systemd}/bin/systemctl restart wordforge-git-sync
        sleep 2

        echo "[3/7] Recreating Python environment..."
        if [ -d ${projectPath}/venv ]; then
          echo "Removing old venv..."
          rm -rf ${projectPath}/venv
        fi

        echo "[4/7] Rebuilding frontend..."
        ${pkgs.systemd}/bin/systemctl restart wordforge-frontend-build
        sleep 3

        echo "[5/7] Starting backend..."
        ${pkgs.systemd}/bin/systemctl start wordforge-backend
        sleep 5

        echo "[6/7] Checking backend status..."
        if ! ${pkgs.systemd}/bin/systemctl is-active --quiet wordforge-backend; then
          echo "ERROR: Backend failed to start!"
          ${pkgs.systemd}/bin/systemctl status wordforge-backend --no-pager || true
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

      virtualHosts."${domain}" = {
        listen = [
          { addr = "0.0.0.0"; port = publicPort; }
        ];

        # IP whitelist через allow/deny
        extraConfig = ''
          ${lib.concatMapStrings (ip: "allow ${ip};\n          ") allowedIPs}
          deny all;
        '';

        locations."/api/" = {
          proxyPass = "http://${backendHost}:${toString backendPort}";
          extraConfig = ''
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
          '';
        };

        locations."/" = {
          root = frontendBuildDir;
          tryFiles = "$uri $uri/ /index.html";
        };

        locations."~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$" = {
          root = frontendBuildDir;
          extraConfig = ''
            add_header Cache-Control "public, max-age=31536000, immutable";
            access_log off;
          '';
        };
      };
    };

  };
}
