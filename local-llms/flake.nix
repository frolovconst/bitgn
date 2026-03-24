{
  description = "Columbarium local LLM and agent development environment";

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
            export LOCAL_LLM_HOME="$PWD"
            export OLLAMA_HOST="127.0.0.1:11434"

            echo "Entered Columbarium local LLM dev shell"
            echo "LOCAL_LLM_HOME=$LOCAL_LLM_HOME"
            echo "OLLAMA_HOST=$OLLAMA_HOST"
          '';
        };
      });
}
