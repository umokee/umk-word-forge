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
  gitBranch = "claude/build-app-from-spec-qPE1y";

  domain = "words.umkcloud.xyz";
  publicPort = 8889;
  backendPort = 8001;
  backendHost = "127.0.0.1";

  projectPath = "/var/lib/wordforge";
  secretsDir = "/var/lib/wordforge-secrets";
  logDir = "/var/log/wordforge";
  dataDir = "${projectPath}/data";
  frontendBuildDir = "${projectPath}/frontend/dist";

  enableFail2ban = true;
  fail2banMaxRetry = 2;
  fail2banFindTime = "1d";
  fail2banBanTime = "52w";

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

    networking.firewall.allowedTCPPorts = [
      80
      publicPort
    ];

    systemd.tmpfiles.rules = [
      "d ${projectPath} 0755 ${user} ${group} -"
      "d ${secretsDir} 0700 ${user} ${group} -"
      "d ${logDir} 0750 ${user} ${group} -"
      "d ${dataDir} 0750 ${user} ${group} -"
      "f ${logDir}/app.log 0640 ${user} ${group} -"
    ];

    # --- Secrets (sops-nix) ---
    sops.secrets."word-forge/api-key" = {
      owner = user;
    };
    sops.secrets."word-forge/gemini-key" = {
      owner = user;
    };

    sops.templates."wordforge-env" = {
      content = ''
        API_KEY=${config.sops.placeholder."word-forge/api-key"}
        GEMINI_API_KEY=${config.sops.placeholder."word-forge/gemini-key"}
        DATABASE_URL=sqlite:///${dataDir}/wordforge.db
        CORS_ORIGINS=https://${domain}:${toString publicPort},http://${domain}
        DEBUG=false
        WORDFORGE_LOG_DIR=${logDir}
        WORDFORGE_LOG_FILE=app.log
      '';
      owner = user;
      group = group;
    };

    security.acme = {
      acceptTerms = lib.mkDefault true;
      defaults.email = lib.mkDefault "admin@umkcloud.xyz";
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
          echo "First run detected — seeding database with 500 words..."
          cd ${projectPath}
          DATABASE_URL=sqlite:///${dataDir}/wordforge.db ${projectPath}/venv/bin/python -m backend.seed --count 500
          echo "Seed completed"
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

    # --- nginx reverse proxy ---
    services.nginx = {
      enable = lib.mkDefault true;

      recommendedGzipSettings = lib.mkDefault true;
      recommendedOptimisation = lib.mkDefault true;
      recommendedProxySettings = lib.mkDefault true;
      recommendedTlsSettings = lib.mkDefault true;

      appendHttpConfig = ''
        limit_req_zone $binary_remote_addr zone=wf_api_limit:10m rate=10r/s;
        limit_conn_zone $binary_remote_addr zone=wf_conn_limit:10m;
      '';

      virtualHosts."${domain}" = {
        addSSL = true;
        enableACME = true;

        listen = [
          {
            addr = "0.0.0.0";
            port = 80;
            ssl = false;
          }
          {
            addr = "0.0.0.0";
            port = publicPort;
            ssl = true;
          }
        ];

        locations."/api/" = {
          proxyPass = "http://${backendHost}:${toString backendPort}";
          extraConfig = ''
            limit_req zone=wf_api_limit burst=20 nodelay;
            limit_conn wf_conn_limit 15;

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
            add_header X-Content-Type-Options "nosniff";
            add_header X-Frame-Options "SAMEORIGIN";
            add_header X-XSS-Protection "1; mode=block";
            add_header Referrer-Policy "no-referrer-when-downgrade";

            add_header Cache-Control "public, max-age=3600";
            limit_conn wf_conn_limit 30;
          '';
        };

        # Cache static assets aggressively
        locations."~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$" = {
          root = frontendBuildDir;
          extraConfig = ''
            add_header Cache-Control "public, max-age=31536000, immutable";
            access_log off;
          '';
        };
      };
    };

    # --- fail2ban ---
    environment.etc."fail2ban/filter.d/wordforge-api.conf" = lib.mkIf enableFail2ban {
      text = ''
        [Definition]
        failregex = ^.*Invalid API key attempt from <HOST>.*$
        ignoreregex =
      '';
    };

    services.fail2ban = lib.mkIf enableFail2ban {
      enable = true;

      jails = {
        wordforge-api = {
          settings = {
            enabled = true;
            filter = "wordforge-api";
            logpath = "${logDir}/app.log";
            backend = "auto";
            action = "iptables-allports";
            maxretry = fail2banMaxRetry;
            findtime = fail2banFindTime;
            bantime = fail2banBanTime;
          };
        };
        nginx-req-limit = {
          settings = {
            enabled = true;
            filter = "nginx-limit-req";
            action = "iptables-allports";
            backend = "systemd";
            maxretry = fail2banMaxRetry;
            findtime = fail2banFindTime;
            bantime = fail2banBanTime;
          };
        };
      };
    };
  };
}
