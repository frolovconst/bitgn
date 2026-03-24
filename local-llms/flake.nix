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

        localLlmHome = ''
          if [ -d "$PWD/local-llms" ]; then
            export LOCAL_LLM_HOME="$PWD/local-llms"
          else
            export LOCAL_LLM_HOME="$PWD"
          fi
        '';
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
            ollama
          ];

          shellHook = ''
            ${localLlmHome}

            export OLLAMA_HOST="127.0.0.1:11434"
            export OLLAMA_MODELS="$LOCAL_LLM_HOME/.ollama/models"

            mkdir -p "$OLLAMA_MODELS"

            echo "Entered Columbarium local LLM dev shell"
            echo "LOCAL_LLM_HOME=$LOCAL_LLM_HOME"
            echo "OLLAMA_HOST=$OLLAMA_HOST"
            echo "OLLAMA_MODELS=$OLLAMA_MODELS"
          '';
        };

        apps = {
          ollama-serve = {
            type = "app";
            program =
              let
                app = pkgs.writeShellApplication {
                  name = "ollama-serve";
                  runtimeInputs = [ pkgs.ollama ];
                  text = ''
                    ${localLlmHome}
                    export OLLAMA_HOST="127.0.0.1:11434"
                    export OLLAMA_MODELS="$LOCAL_LLM_HOME/.ollama/models"
                    mkdir -p "$OLLAMA_MODELS"
                    exec bash ${./bin/ollama-serve.sh}
                  '';
                };
              in
              "${app}/bin/ollama-serve";
          };

          qwen25-coder-3b-pull = {
            type = "app";
            program =
              let
                app = pkgs.writeShellApplication {
                  name = "qwen25-coder-3b-pull";
                  runtimeInputs = [ pkgs.ollama ];
                  text = ''
                    ${localLlmHome}
                    export OLLAMA_HOST="127.0.0.1:11434"
                    export OLLAMA_MODELS="$LOCAL_LLM_HOME/.ollama/models"
                    mkdir -p "$OLLAMA_MODELS"
                    exec bash ${./bin/qwen25-coder-3b-pull.sh}
                  '';
                };
              in
              "${app}/bin/qwen25-coder-3b-pull";
          };

          qwen25-coder-3b-chat = {
            type = "app";
            program =
              let
                app = pkgs.writeShellApplication {
                  name = "qwen25-coder-3b-chat";
                  runtimeInputs = [ pkgs.ollama ];
                  text = ''
                    ${localLlmHome}
                    export OLLAMA_HOST="127.0.0.1:11434"
                    export OLLAMA_MODELS="$LOCAL_LLM_HOME/.ollama/models"
                    mkdir -p "$OLLAMA_MODELS"
                    exec bash ${./bin/qwen25-coder-3b-chat.sh}
                  '';
                };
              in
              "${app}/bin/qwen25-coder-3b-chat";
          };
        };
      });
}
