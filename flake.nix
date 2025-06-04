{
  # Nix Flake for this package
  description = "rhasselbaum/host-tools package Flake";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        pname = "host-tools";
      in
      {
        packages = {
          host-tools = pkgs.stdenv.mkDerivation {
            inherit pname;
            version = "git";

            src = ./.;
            buildInputs = [
              (pkgs.python3.withPackages (p: with p; [ ]))
              pkgs.makeWrapper
              pkgs.iputils
              pkgs.systemd
            ];

            installPhase = ''
              mkdir -p $out/bin
              cp $src/src/network_or_bust.py $out/bin
              chmod +x $out/bin/network_or_bust.py
              makeWrapper $out/bin/network_or_bust.py $out/bin/network-or-bust \
                --set PATH ${pkgs.iputils}/bin:${pkgs.systemd}/bin
            '';
          };
        };

        defaultPackage = self.packages.${system}.host-tools;
      }
    );
  }