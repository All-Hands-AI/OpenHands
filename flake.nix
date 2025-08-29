{
  description = "Development environment with Python, Node.js, Poetry, and build tools";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Check if we're on WSL
        isWSL = builtins.pathExists /proc/sys/fs/binfmt_misc/WSLInterop;

        # Python 3.12 with development headers
        python312 = pkgs.python312;

        # Poetry 1.8.x
        poetry = pkgs.poetry;

        # Build essential tools
        buildTools = with pkgs; [
          gcc
          gnumake
          cmake
          pkg-config
          autoconf
          automake
          libtool
        ];

        # Development headers for Python
        pythonDev = with pkgs; [
          python312.pkgs.pip
          python312.pkgs.setuptools
          python312.pkgs.wheel
          # Python development headers are included with python312
        ];

        # Optional WSL-specific tools
        wslTools = with pkgs; lib.optionals isWSL [
          netcat-gnu
        ];

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python312
            nodejs_22
            poetry
            pre-commit
          ] ++ buildTools ++ pythonDev ++ wslTools;

          shellHook = ''
            echo "Development environment loaded!"
            echo "Python: $(python --version)"
            echo "Node.js: $(node --version)"
            echo "Poetry: $(poetry --version)"
            echo "GCC: $(gcc --version | head -n1)"
            ${if isWSL then ''echo "WSL detected - netcat included"'' else ""}
            echo ""
            echo "All development dependencies are ready."
          '';

          # Set up environment variables
          PYTHON = "${python312}/bin/python";
          NODE_PATH = "${pkgs.nodejs_22}/lib/node_modules";

          # Ensure Python can find its headers
          C_INCLUDE_PATH = "${python312}/include/python3.12";
          CPLUS_INCLUDE_PATH = "${python312}/include/python3.12";
        };
      });
}
