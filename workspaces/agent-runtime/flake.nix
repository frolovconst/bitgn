{
  description = "Columbarium runtime and testing environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python312
            uv
            git
            jq
            ripgrep
            curl
          ];

          shellHook = ''
            if [ -d "$PWD/workspaces/agent-runtime" ]; then
              export AGENT_RUNTIME_HOME="$PWD/workspaces/agent-runtime"
            else
              export AGENT_RUNTIME_HOME="$PWD"
            fi

            echo "Entered Columbarium agent runtime shell"
            echo "AGENT_RUNTIME_HOME=$AGENT_RUNTIME_HOME"
            echo "Tip: uv pip install -e .[dev]"
          '';
        };
      });
}
