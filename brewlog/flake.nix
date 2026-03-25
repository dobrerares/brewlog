{
  description = "BrewLog development environment with Playwright testing";

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
            firefox
            # X11 and graphics libraries required by Playwright
            libxcb
            libx11
            libxext
            libxrandr
            libxcomposite
            libxcursor
            libxdamage
            libxfixes
            libxi
            libxrender
            libxkbcommon
            libxkbfile
            # GTK and rendering
            atk
            gdk-pixbuf
            cairo
            pango
            gtk3
            # Audio
            alsa-lib
            # Fonts and text rendering
            freetype
            fontconfig
            # System libraries
            glib
            dbus
            libGL
            zlib
            libuuid
            glibc
            stdenv.cc.cc.lib
          ];

          shellHook = ''
            # Combine all library paths
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
              pkgs.libxcb
              pkgs.libx11
              pkgs.libxext
              pkgs.libxrandr
              pkgs.libxcomposite
              pkgs.libxcursor
              pkgs.libxdamage
              pkgs.libxfixes
              pkgs.libxi
              pkgs.libxrender
              pkgs.libxkbcommon
              pkgs.libxkbfile
              pkgs.atk
              pkgs.gdk-pixbuf
              pkgs.cairo
              pkgs.pango
              pkgs.gtk3
              pkgs.alsa-lib
              pkgs.freetype
              pkgs.fontconfig
              pkgs.glib
              pkgs.dbus
              pkgs.libGL
              pkgs.zlib
              pkgs.stdenv.cc.cc.lib
            ]}:$LD_LIBRARY_PATH

            # Playwright configuration
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
            export NIXOS_SYSTEM_FIREFOX=true

            # Add Firefox to PATH
            export PATH=${pkgs.firefox}/bin:$PATH

            # Function to patch Firefox binary for NixOS compatibility
            patch_firefox_binary() {
              local firefox_dir="$HOME/.cache/ms-playwright/firefox-1509/firefox"
              if [ -f "$firefox_dir/firefox" ] && [ ! -f "$firefox_dir/firefox.patched" ]; then
                echo "Patching Firefox binary for NixOS..."
                ${pkgs.patchelf}/bin/patchelf \
                  --set-interpreter "$(cat ${pkgs.stdenv.cc}/nix-support/dynamic-linker)" \
                  --set-rpath "${pkgs.lib.makeLibraryPath [
                    pkgs.libxcb pkgs.libx11 pkgs.libxext pkgs.libxrandr pkgs.libxcomposite
                    pkgs.libxcursor pkgs.libxdamage pkgs.libxfixes pkgs.libxi pkgs.libxrender
                    pkgs.libxkbcommon pkgs.libxkbfile pkgs.atk pkgs.gdk-pixbuf pkgs.cairo
                    pkgs.pango pkgs.gtk3 pkgs.alsa-lib pkgs.freetype pkgs.fontconfig pkgs.glib
                    pkgs.dbus pkgs.libGL pkgs.zlib pkgs.stdenv.cc.cc.lib
                  ]}" \
                  "$firefox_dir/firefox" || true
                touch "$firefox_dir/firefox.patched"
              fi
            }

            # Try to patch Firefox on shell entry
            patch_firefox_binary || true
          '';
        };
      }
    );
}
