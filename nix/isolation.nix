# Host-side bridge filter for a Crawl4AI container. Import this on the host
# that owns the veth, not inside the container.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.crawl4ai.isolation;
  # nft -c opens a netlink socket, so it cannot run in a sandboxed build.
  rules = pkgs.runCommand "crawl4ai-isolation.nft" {
    preferLocalBuild = true;
  } ''
    substitute ${./isolation.nft} "$out" \
      --replace-fail '@ifname@' ${lib.escapeShellArg cfg.interface}
    grep -q ${lib.escapeShellArg cfg.interface} "$out"
  '';
in
{
  options.services.crawl4ai.isolation = {
    enable = lib.mkEnableOption ''
      host-side bridge filtering that stops the Crawl4AI container from
      opening new connections to local or non-global addresses, including
      the host
    '';

    interface = lib.mkOption {
      type = lib.types.str;
      default = "ve-crawl4ai";
      description = ''
        Host-side veth of the container (`ve-<container name>`). NixOS
        containers name this interface from the container name, truncated
        to 15 characters.
      '';
    };

    containerUnit = lib.mkOption {
      type = lib.types.str;
      default = "container-crawl4ai.service";
      description = ''
        systemd unit that starts the container. It is ordered after the
        filter and will not start if the filter fails to load.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    boot.kernelModules = [ "nf_conntrack_bridge" ];

    systemd.services.crawl4ai-isolation = {
      description = "Crawl4AI container egress isolation";
      wantedBy = [ "multi-user.target" ];
      before = [ cfg.containerUnit ];
      requiredBy = [ cfg.containerUnit ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStartPre = [
          "${pkgs.kmod}/bin/modprobe nf_conntrack_bridge"
          "-${pkgs.nftables}/bin/nft delete table bridge crawl4ai_isolation"
        ];
        ExecStart = "${pkgs.nftables}/bin/nft -f ${rules}";
        ExecStop = "${pkgs.nftables}/bin/nft delete table bridge crawl4ai_isolation";
      };
    };

    systemd.services.${lib.removeSuffix ".service" cfg.containerUnit} = {
      after = [ "crawl4ai-isolation.service" ];
      requires = [ "crawl4ai-isolation.service" ];
    };
  };
}
