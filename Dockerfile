# Reference environment of ADR-005 (amendment 2026-10-14): GDAL at system level
# from Debian 13 (trixie, GDAL 3.10), Python and dependencies managed by uv from
# pyproject.toml and uv.lock. PDAL is deferred to Sprint 9 and not installed.
#
# Both external images are pinned to an explicit version tag. Digests are not
# pinned (see the handoff report); to harden further, append `@sha256:<digest>`
# taken from `docker buildx imagetools inspect <image:tag>`.

FROM ghcr.io/astral-sh/uv:0.12.23 AS uv

FROM debian:trixie

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive

# System GIS libraries and the few tools the gate needs (git: the policy-guard
# tests run it against throwaway repositories). Headers are installed so the
# Block 3 bindings can be built against the system version; no compiler yet.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
    ca-certificates \
    git \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/

# Non-root user. Debian has no default user at UID 1000; if the base image ever
# ships one, it is removed first so that the UID and GID are free.
RUN existing="$(getent passwd "${USER_UID}" | cut -d: -f1)" \
    && if [ -n "${existing}" ]; then userdel --remove "${existing}"; fi \
    && (getent group "${USER_GID}" >/dev/null || groupadd --gid "${USER_GID}" "${USERNAME}") \
    && useradd --create-home --uid "${USER_UID}" --gid "${USER_GID}" --shell /bin/bash "${USERNAME}" \
    && mkdir -p /opt/venv /opt/python /workspace \
    "/home/${USERNAME}/.cache/uv" "/home/${USERNAME}/.cache/mypy" "/home/${USERNAME}/.cache/ruff" \
    && chown "${USER_UID}:${USER_GID}" /opt/venv /opt/python /workspace \
    && chown -R "${USER_UID}:${USER_GID}" "/home/${USERNAME}/.cache"

# The virtualenv and the managed interpreter live outside /workspace, which is
# bind-mounted from the host: the host's macOS .venv is never used or touched.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PYTHON_PREFERENCE=only-managed \
    UV_CACHE_DIR=/home/${USERNAME}/.cache/uv \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    MYPY_CACHE_DIR=/home/${USERNAME}/.cache/mypy \
    RUFF_CACHE_DIR=/home/${USERNAME}/.cache/ruff \
    PATH=/opt/venv/bin:${PATH}

USER ${USERNAME}
WORKDIR /workspace

# Layer 1: interpreter and locked dependencies. Only the manifests are copied,
# so this layer is rebuilt only when pyproject.toml, uv.lock or .python-version
# change. --no-install-project: the package sources are not there yet.
COPY --chown=${USER_UID}:${USER_GID} pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/home/${USERNAME}/.cache/uv,uid=${USER_UID},gid=${USER_GID} \
    uv python install \
    && uv sync --locked --no-install-project

# Layer 2: the source, then the project itself (editable, so the bind mount of
# the repository over /workspace takes effect without a rebuild).
COPY --chown=${USER_UID}:${USER_GID} . .
RUN --mount=type=cache,target=/home/${USERNAME}/.cache/uv,uid=${USER_UID},gid=${USER_GID} \
    uv sync --locked

CMD ["bash"]
