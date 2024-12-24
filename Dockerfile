# Dockerfile
FROM hhftechnology/alpine:3.18

# Build arguments for installation options
ARG INSTALL_CLOUDFLARE=true
ARG INSTALL_TAILSCALE=true

# Build arguments for default configuration
# These can be overridden at runtime
ARG DEFAULT_SERVICE_PORT=8080
ARG DEFAULT_SERVICE_PROTOCOL=http
ARG DEFAULT_HOSTNAME=secure-service

# Install base packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    supervisor \
    bash \
    jq

# Install Tailscale if requested
RUN if [ "$INSTALL_TAILSCALE" = "true" ]; then \
        apk add --no-cache iptables ip6tables && \
        curl -fsSL https://tailscale.com/install.sh | sh; \
    fi

# Install Cloudflared if requested
RUN if [ "$INSTALL_CLOUDFLARE" = "true" ]; then \
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && \
        chmod +x /usr/local/bin/cloudflared; \
    fi

# Create necessary directories
RUN mkdir -p /scripts /var/log/supervisor && \
    if [ "$INSTALL_CLOUDFLARE" = "true" ]; then mkdir -p /etc/cloudflared; fi

# Copy scripts and set permissions
COPY scripts/entrypoint.sh /scripts/entrypoint.sh
COPY scripts/setup.py /scripts/setup.py
RUN chmod +x /scripts/entrypoint.sh /scripts/setup.py

# Copy service-specific configs
COPY config/cloudflared.yml /etc/cloudflared/config.yml

# Set default environment variables that can be overridden at runtime
ENV SERVICE_PORT=${DEFAULT_SERVICE_PORT} \
    SERVICE_PROTOCOL=${DEFAULT_SERVICE_PROTOCOL} \
    HOSTNAME=${DEFAULT_HOSTNAME} \
    ENABLE_CLOUDFLARE="false" \
    ENABLE_TAILSCALE="false" \
    TS_ACCEPT_DNS=false \
    TS_AUTH_ONCE=false \
    TS_DEST_IP="" \
    TS_HOSTNAME=${HOSTNAME} \
    TS_OUTBOUND_HTTP_PROXY_LISTEN="" \
    TS_ROUTES="" \
    TS_SOCKET="/var/run/tailscale/tailscaled.sock" \
    TS_SOCKS5_SERVER="" \
    TS_STATE_DIR="/var/lib/tailscale" \
    TS_USERSPACE=true \
    TS_EXTRA_ARGS="" \
    TS_TAILSCALED_EXTRA_ARGS=""

# Add documentation about configuration options
LABEL maintainer="HHF Technology <discourse@hhf.technology>"
LABEL version="1.0"
LABEL org.opencontainers.image.description="Secure service proxy with Cloudflare and Tailscale support" \
      org.opencontainers.image.documentation="Configuration Options:\n\
      SERVICE_PORT: The port your application listens on (default: 8080)\n\
      SERVICE_PROTOCOL: Protocol for your service (http, https, tcp, udp)\n\
      HOSTNAME: Service hostname for DNS\n\
      ENABLE_CLOUDFLARE: Set to 'true' to enable Cloudflare tunnel\n\
      ENABLE_TAILSCALE: Set to 'true' to enable Tailscale VPN"

ENTRYPOINT ["/scripts/entrypoint.sh"]
