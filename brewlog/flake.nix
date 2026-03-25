{
  description = "BrewLog e2e testing environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_24
            npm
            firefox
            playwright-driver
            # X11 and graphics libraries for Firefox
            libxcb
            libX11
            libXrandr
            libXcomposite
            libXcursor
            libXdamage
            libXfixes
            libXi
            libxtst
            libxkbcommon
            gtk3
            gdk-pixbuf
            pango
            cairo
            atk
            libdbus
            libfreetype
            fontconfig
            libasound
            libxshmfence
            mesa
            xorg.libxinerama
            xorg.libxext
          ];

          shellHook = ''
            export PLAYWRIGHT_FIREFOX_INSTALL_DIR="${pkgs.firefox}"
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
          '';
        };
      }
    );
}
