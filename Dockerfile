FROM docker.io/library/python:3.12.6-alpine
ARG TARGETPLATFORM
ENV \
    PATH="${PATH}:/root/.krew/bin" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1

RUN apk add --no-cache bash ca-certificates catatonit curl git jq tzdata util-linux yq-go

COPY --from=ghcr.io/fluxcd/flux-cli:v2.4.0 /usr/local/bin/flux /usr/local/bin/flux
COPY --from=ghcr.io/siderolabs/talosctl:v1.8.0 /talosctl /usr/local/bin/talosctl
COPY --from=quay.io/prometheus/alertmanager:v0.27.0 /bin/amtool /usr/local/bin/amtool
COPY --from=registry.k8s.io/kubectl:v1.31.1 /bin/kubectl /usr/local/bin/kubectl

RUN curl -fsSL "https://i.jpillora.com/kubernetes-sigs/krew!!?as=krew&type=script" | bash
RUN krew install cnpg && kubectl cnpg version

WORKDIR /app

COPY requirements.txt .
RUN pip install uv \
    && \
    uv pip install --system --requirement requirements.txt \
    && pip uninstall --yes uv \
    && \
    rm -rf \
        /root/.cache \
        /root/.cargo \
        /tmp/*

COPY ./scripts .
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/usr/bin/catatonit", "--"]
CMD ["/entrypoint.sh"]
