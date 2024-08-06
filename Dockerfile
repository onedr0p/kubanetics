FROM docker.io/library/alpine:3.20.2 as base
ARG TARGETPLATFORM
ENV PATH="${PATH}:/root/.krew/bin"

RUN apk add --no-cache bash ca-certificates catatonit curl git jq util-linux yq-go

COPY --from=ghcr.io/fluxcd/flux-cli:v2.3.0 /usr/local/bin/flux /usr/local/bin/flux
COPY --from=ghcr.io/siderolabs/talosctl:v1.7.6 /talosctl /usr/local/bin/talosctl
COPY --from=quay.io/prometheus/alertmanager:v0.27.0 /bin/amtool /usr/local/bin/amtool
COPY --from=registry.k8s.io/kubectl:v1.30.3 /bin/kubectl /usr/local/bin/kubectl

RUN curl -fsSL "https://i.jpillora.com/kubernetes-sigs/krew!!?as=krew&type=script" | bash
RUN krew install cnpg && kubectl cnpg version

WORKDIR /app

COPY ./scripts .
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/usr/bin/catatonit", "--"]
CMD ["/entrypoint.sh"]
