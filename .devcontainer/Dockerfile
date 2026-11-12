# Economics research stack for Pixi, rv, TinyTeX, Quarto, and cloud IDE agents.
FROM ubuntu:22.04@sha256:076e7bf82319619f28dd0aa9c02ab34b055ad37100395b4f49a2ffba04fb5e11

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# ========= 1) OS Base =========
# Infrastructure for:
# - Git/GitHub CLI
# - Python/R package managers and compiled infrastructure packages
# - Jupyter/Quarto runtime support
# - TinyTeX + Japanese fonts
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg \
    git git-lfs openssh-client \
    make build-essential pkg-config cmake \
    libffi-dev \
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

# Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i 's/^# *\(ja_JP.UTF-8 UTF-8\)/\1/' /etc/locale.gen && locale-gen
ENV LANG=ja_JP.UTF-8 LC_ALL=ja_JP.UTF-8

# ========= 1.1) TinyTeX =========
# Install the monthly release; tlmgr supplies the required document packages.
ARG TINYTEX_VERSION=v2026.11
ENV TINYTEX_HOME=/opt/TinyTeX
ENV PATH="${TINYTEX_HOME}/bin/x86_64-linux:${PATH}"
RUN curl -fsSL "https://github.com/rstudio/tinytex-releases/releases/download/${TINYTEX_VERSION}/TinyTeX-linux-x86_64-${TINYTEX_VERSION}.tar.xz" -o /tmp/tinytex.tar.xz && \
    echo "50e68059058db770a28bcca44d5a323cb57fc10d470017c858404aafeaac9dd7  /tmp/tinytex.tar.xz" | sha256sum -c - && \
    tar -xJf /tmp/tinytex.tar.xz -C /opt && \
    mv /opt/.TinyTeX "${TINYTEX_HOME}" && \
    rm -f /tmp/tinytex.tar.xz && \
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
WORKDIR /workspaces
ENV PATH="/home/$USERNAME/.local/bin:${PATH}"

# Commit identity comes from the user's Git configuration or credential sharing.

# ========= 3) Pixi =========
ARG PIXI_VERSION=v0.84.2
RUN curl -fsSL "https://github.com/prefix-dev/pixi/releases/download/${PIXI_VERSION}/install.sh" -o /tmp/install-pixi.sh && \
    echo "cbfca96e77535be88051d6c6fa64833b22b2c2bf70fc29ec573a132866251311  /tmp/install-pixi.sh" | sha256sum -c - && \
    PIXI_VERSION="${PIXI_VERSION}" PIXI_NO_PATH_UPDATE=1 PIXI_NO_TELEMETRY=1 bash /tmp/install-pixi.sh && \
    rm -f /tmp/install-pixi.sh
ENV PATH="/home/$USERNAME/.pixi/bin:$PATH"

# ========= 4) Runtime Dependency Setup =========
# The workspace .pixi volume supplies the runtime environment.
# setup-environment.sh installs project dependencies after the container starts.

# ========= 5.5) rv =========
ARG RV_VERSION=v0.23.3
RUN curl -fsSL "https://github.com/A2-ai/rv/releases/download/${RV_VERSION}/rv-${RV_VERSION}-x86_64-unknown-linux-musl.tar.gz" -o /tmp/rv.tar.gz && \
    echo "92dd9516c39b80ef52931e1d05262a836e1ddb87c4e46dba142d7327cac5bab5  /tmp/rv.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/rv.tar.gz -C /tmp rv && \
    install -Dm755 /tmp/rv "/home/$USERNAME/.local/bin/rv" && \
    rm -f /tmp/rv.tar.gz /tmp/rv

# ========= 8) Default Command =========
USER root
CMD ["/bin/bash"]
