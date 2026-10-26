# Crawl4AI API/MCP server.
#
# Does not attach a network interface and does not enforce egress isolation.
# Bridged container traffic bypasses a container firewall; use
# nixosModules.isolation on the host that owns the veth if the browser must
# not open new connections to local addresses.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.crawl4ai;
  stateDir = "/var/lib/crawl4ai";
  redisPasswordFile = "${stateDir}/redis-password";
  tokenFile = "/run/secrets/crawl4ai-api-token";

  startRedis = pkgs.writeShellScript "crawl4ai-redis" ''
    set -eu
    umask 077
    if [ ! -s ${redisPasswordFile} ]; then
      ${pkgs.openssl}/bin/openssl rand -hex 32 > ${redisPasswordFile}
    fi
    password=$(${pkgs.coreutils}/bin/tr -d ' \r\n' < ${redisPasswordFile})
    exec ${pkgs.redis}/bin/redis-server \
      --bind 127.0.0.1 \
      --port 6379 \
      --protected-mode yes \
      --requirepass "$password" \
      --dir ${stateDir}/redis \
      --save "" \
      --appendonly no \
      --daemonize no
  '';

  startServer = pkgs.writeShellScript "crawl4ai-server-start" ''
    set -eu
    password=$(${pkgs.coreutils}/bin/tr -d ' \r\n' < ${redisPasswordFile})
    token=$(${pkgs.coreutils}/bin/tr -d ' \r\n' < ${tokenFile})
    if [ -z "$token" ]; then
      printf 'crawl4ai: API token file %s is empty\n' ${tokenFile} >&2
      exit 1
    fi
    for _ in $(${pkgs.coreutils}/bin/seq 1 50); do
      if ${pkgs.redis}/bin/redis-cli -a "$password" --no-auth-warning ping | ${pkgs.gnugrep}/bin/grep -qx PONG; then
        break
      fi
      ${pkgs.coreutils}/bin/sleep 0.1
    done
    export REDIS_PASSWORD="$password"
    export CRAWL4AI_API_TOKEN="$token"
    export CRAWL4AI_ARTIFACT_DIR=${stateDir}/outputs
    export HOME=${stateDir}/home
    export CRAWL4_AI_BASE_DIRECTORY=${stateDir}/home
    export XDG_CACHE_HOME=${stateDir}/cache
    export GUNICORN_BIND="${cfg.bind}:${toString cfg.port}"
    exec ${lib.getExe cfg.package}
  '';
in
{
  options.services.crawl4ai = {
    enable = lib.mkEnableOption "the Crawl4AI API and MCP server";

    package = lib.mkOption {
      type = lib.types.package;
      description = "crawl4ai-server package (bin/crawl4ai-server).";
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 11235;
      description = "TCP port for the API and MCP SSE endpoint (/mcp/sse).";
    };

    bind = lib.mkOption {
      type = lib.types.str;
      default = "0.0.0.0";
      description = ''
        Address gunicorn binds. Non-loopback requires the API token file;
        the server refuses an unauthenticated non-loopback bind.
      '';
    };

    openFirewall = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Open the service port in this machine's firewall.";
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = "crawl4ai";
      description = "Service account. Keep the uid stable when the host maps it through a user namespace.";
    };

    uid = lib.mkOption {
      type = lib.types.int;
      default = 241;
      description = "Numeric uid of the service account.";
    };

    group = lib.mkOption {
      type = lib.types.str;
      default = "crawl4ai";
    };

    gid = lib.mkOption {
      type = lib.types.int;
      default = 241;
    };
  };

  config = lib.mkIf cfg.enable {
    users.groups.${cfg.group} = {
      gid = cfg.gid;
    };
    users.users.${cfg.user} = {
      isSystemUser = true;
      inherit (cfg) uid group;
      home = stateDir;
      createHome = false;
    };

    systemd.tmpfiles.rules = [
      "d ${stateDir} 0750 ${cfg.user} ${cfg.group} -"
      "d ${stateDir}/home 0700 ${cfg.user} ${cfg.group} -"
      "d ${stateDir}/cache 0700 ${cfg.user} ${cfg.group} -"
      "d ${stateDir}/outputs 0700 ${cfg.user} ${cfg.group} -"
      "d ${stateDir}/redis 0700 ${cfg.user} ${cfg.group} -"
      "f ${redisPasswordFile} 0400 ${cfg.user} ${cfg.group} -"
    ];

    networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];

    fonts.fontconfig.enable = true;
    fonts.packages = [ pkgs.dejavu_fonts ];

    systemd.services.crawl4ai-redis = {
      description = "Crawl4AI Redis";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Group = cfg.group;
        ExecStart = startRedis;
        Restart = "on-failure";
        RestartSec = "2s";
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ stateDir ];
        LockPersonality = true;
        RestrictRealtime = true;
        SystemCallArchitectures = "native";
      };
    };

    systemd.services.crawl4ai = {
      description = "Crawl4AI API and MCP server";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" "crawl4ai-redis.service" ];
      requires = [ "crawl4ai-redis.service" ];
      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Group = cfg.group;
        ExecStart = startServer;
        Restart = "on-failure";
        RestartSec = "5s";
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ stateDir ];
        # Chromium with --no-sandbox still needs /dev and a writable home.
        PrivateDevices = false;
        LockPersonality = true;
        RestrictRealtime = true;
        SystemCallArchitectures = "native";
        LimitNOFILE = 65536;
        MemoryMax = "8G";
      };
    };
  };
}
