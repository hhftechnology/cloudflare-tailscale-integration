# Secure Service Proxy

A flexible Docker image that provides secure access to your services through Cloudflare Tunnel and/or Tailscale VPN.

## Quick Start

```bash
# Run with default settings
docker run -e ENABLE_CLOUDFLARE=true -e CLOUDFLARED_TOKEN=your_token your-image

# Run with custom port
docker run -e SERVICE_PORT=3000 -e ENABLE_TAILSCALE=true -e TAILSCALE_AUTHKEY=your_key your-image
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SERVICE_PORT | 8080 | Port your application listens on |
| SERVICE_PROTOCOL | http | Protocol (http, https, tcp, udp) |
| HOSTNAME | secure-service | Service hostname for DNS |
| ENABLE_CLOUDFLARE | false | Enable Cloudflare tunnel |
| ENABLE_TAILSCALE | false | Enable Tailscale VPN |

### Required Tokens (based on enabled services)

- For Cloudflare: Set CLOUDFLARED_TOKEN
- For Tailscale: Set TAILSCALE_AUTHKEY

## Docker Compose Example

```yaml
services:
  secure-proxy:
    image: your-image
    environment:
      - SERVICE_PORT=3000
      - ENABLE_CLOUDFLARE=true
      - CLOUDFLARED_TOKEN=${CLOUDFLARED_TOKEN}
    cap_add:
      - NET_ADMIN  # Required for Tailscale if enabled
```

## Security Considerations

- The container needs NET_ADMIN capability when using Tailscale
- Tokens should be provided through environment variables or secrets
- At least one security service (Cloudflare or Tailscale) should be enabled

## Building Custom Images

You can customize the default settings when building:

```bash
docker build \
  --build-arg DEFAULT_SERVICE_PORT=3000 \
  --build-arg DEFAULT_HOSTNAME=myapp \
  .
```