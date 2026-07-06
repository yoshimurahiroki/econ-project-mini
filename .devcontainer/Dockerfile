# Minimal economics research stack for Pixi, rv, TinyTeX, Quarto, and cloud IDE agents.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# ========= 1) OS Base =========
# Keep only infrastructure needed for:
# - Git/GitHub CLI
# - Python/R package managers and compiled infrastructure packages
# - Jupyter/Quarto runtime support
# - TinyTeX + Japanese fonts
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg \
    git git-lfs openssh-client \
    make build-essential pkg-config cmake \
    libcurl4-openssl-dev libssl-dev libxml2-dev libffi-dev \
    libcairo2-dev libfontconfig1-dev libfreetype6-dev libfribidi-dev libharfbuzz-dev \
    libpng-dev libjpeg-dev \
    locales tzdata jq sudo procps zstd unzip sqlite3 \
    perl xz-utils \
    fonts-noto-cjk fonts-noto-cjk-extra \
    openssl && \
    mkdir -p -m 755 /etc/apt/keyrings && \
    wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && \
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y --no-install-recommends gh && \
    rm -rf /var/lib/apt/lists/*

# Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i 's/^# *\(ja_JP.UTF-8 UTF-8\)/\1/' /etc/locale.gen && locale-gen
ENV LANG=ja_JP.UTF-8 LC_ALL=ja_JP.UTF-8

# ========= 1.1) TinyTeX =========
# The installer fetches the current TinyTeX daily release; tlmgr remains
# available for installing any missing TeX packages later.
ENV TINYTEX_HOME=/opt/TinyTeX
ENV PATH="${TINYTEX_HOME}/bin/x86_64-linux:${PATH}"
RUN curl -fsSL https://yihui.org/tinytex/install-unx.sh -o /tmp/install-tinytex.sh && \
    sh /tmp/install-tinytex.sh --admin --no-path && \
    mv /root/.TinyTeX "${TINYTEX_HOME}" && \
    rm -f /tmp/install-tinytex.sh && \
    "${TINYTEX_HOME}/bin/x86_64-linux/tlmgr" option repository https://tlnet.yihui.org/ && \
    "${TINYTEX_HOME}/bin/x86_64-linux/tlmgr" update --self --all && \
    "${TINYTEX_HOME}/bin/x86_64-linux/tlmgr" install \
      latexmk \
      xetex \
      luatex \
      luatexja \
      collection-latexrecommended \
      collection-latexextra \
      collection-fontsrecommended \
      collection-bibtexextra \
      collection-langjapanese \
      biber && \
    chmod -R a+rX "${TINYTEX_HOME}"

# ========= 1.2) Global NPM Packages =========
# Keep the default image lean. Optional MCP servers are added only when a task
# actually needs them; setup_ide_mcp.sh detects what is installed.
RUN npm install -g repomix

# ========= 2) User Setup =========
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid "$USER_GID" "$USERNAME" || true && \
    useradd --uid "$USER_UID" --gid "$USER_GID" -m -s /bin/bash "$USERNAME" || true && \
    mkdir -p /etc/sudoers.d && \
    echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    chown -R "$USERNAME:$USERNAME" "${TINYTEX_HOME}"

USER $USERNAME
WORKDIR /workspaces/econ-project
ENV PATH="/home/$USERNAME/.cargo/bin:/home/$USERNAME/.local/bin:/home/$USERNAME/go/bin:${PATH}"

# Rust is kept because it is useful for modern Python/R tooling and rv itself.
RUN curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs | \
    sh -s -- -y --profile minimal --default-toolchain stable

# ========= Git Identity =========
ARG GIT_USER_NAME=yoshimurahiroki
ARG GIT_USER_EMAIL=yoshimurahiroki@akane.waseda.jp
RUN command -v git >/dev/null 2>&1 && \
    git config --global user.name "$GIT_USER_NAME" && \
    git config --global user.email "$GIT_USER_EMAIL"

# ========= 3) Pixi =========
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/home/$USERNAME/.pixi/bin:$PATH"

# ========= 4) Runtime Dependency Setup =========
# The workspace .pixi directory is mounted as a devcontainer volume, so any
# Pixi environment created during image build would be hidden at runtime.
# setup-environment.sh installs project dependencies after the container starts.
RUN mkdir -p /tmp/package-lists
WORKDIR /workspaces/econ-project

# ========= 5.5) rv =========
RUN curl -sSL https://raw.githubusercontent.com/A2-ai/rv/refs/heads/main/scripts/install.sh | bash
ENV PATH="/home/$USERNAME/.local/bin:/home/$USERNAME/go/bin:$PATH"

# ========= 6) Runtime Kernel Registration =========
# Kernelspecs are registered from the workspace environment by the
# devcontainer setup script. Registering them here would point at /tmp/pixi,
# which is hidden by the runtime workspace and .pixi volume.
WORKDIR /workspaces/econ-project

# ========= 7) On-demand AI References =========
# setup_ai_skills.sh can fetch optional reference repositories after creation.
RUN sudo mkdir -p /workspaces/econ-project/.resources && \
    sudo chown -R $USERNAME:$USERNAME /workspaces/econ-project/.resources

# ========= 8) Default Command =========
USER root
CMD ["/bin/bash"]
