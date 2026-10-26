{
  description = "Crawl4AI: LLM-friendly crawler, API server, and MCP endpoint";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in
    {
      packages = forAllSystems (pkgs: {
        default = pkgs.callPackage ./nix/package.nix { src = self; };
      });

      # API/MCP server. Set services.crawl4ai.package to
      # inputs.crawl4ai.packages.${system}.default and mount the API token at
      # /run/secrets/crawl4ai-api-token.
      nixosModules.default = import ./nix/module.nix;

      # Host-side bridge filter for a container veth. Import on the host, not
      # inside the container. See nix/isolation.nft.
      nixosModules.isolation = import ./nix/isolation.nix;
    };
}
