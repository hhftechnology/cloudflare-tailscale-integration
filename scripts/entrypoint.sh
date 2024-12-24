#!/bin/bash

log() {
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $1"
}

# Start setup process
log "Starting secure service setup..."
python3 /scripts/setup.py

# Create supervisor configuration dynamically based on enabled services
cat > /etc/supervisor/conf.d/services.conf << EOF
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
EOF

# Add Tailscale configuration if enabled
if [ "$ENABLE_TAILSCALE" = "true" ]; then
    cat >> /etc/supervisor/conf.d/services.conf << EOF

[program:tailscaled]
command=/usr/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock
autostart=true
autorestart=true
priority=10
EOF
fi

# Add Cloudflare configuration if enabled
if [ "$ENABLE_CLOUDFLARE" = "true" ]; then
    cat >> /etc/supervisor/conf.d/services.conf << EOF

[program:cloudflared]
command=/usr/local/bin/cloudflared tunnel run
autostart=true
autorestart=true
priority=20
EOF
fi

# Start supervisor
log "Starting supervisor with enabled services..."
exec supervisord -c /etc/supervisor/conf.d/services.conf