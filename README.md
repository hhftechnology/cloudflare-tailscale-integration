# Secure Access Gateway with Cloudflare and Tailscale

This Docker image provides a secure access gateway that integrates both Cloudflare Tunnels and Tailscale for flexible and secure access to your services. You can use either or both technologies simultaneously to create a secure, zero-trust access layer for your applications.

## Features

- Cloudflare Tunnel integration for secure public access
- Tailscale VPN integration for private network access
- Support for multiple port forwarding
- Docker-compose ready
- Easy configuration through environment variables
- Automatic service discovery and configuration

## Prerequisites

Before using this image, you'll need:

1. A Cloudflare account (if using Cloudflare Tunnels)
2. A Tailscale account (if using Tailscale)
3. Docker and Docker Compose installed on your host
4. Basic understanding of networking and Docker concepts

## Environment Variables

### Core Configuration
```env
# Feature Flags
ENABLE_CLOUDFLARE=true|false
ENABLE_TAILSCALE=true|false

# Cloudflare Configuration
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
# OR
CLOUDFLARE_TUNNEL_ID=your-tunnel-id

# Tailscale Configuration
TAILSCALE_AUTH_KEY=tskey-auth-xxxxx-xxxxxxxxxxxxx
TAILSCALE_HOSTNAME=your-preferred-hostname
TARGET_PORTS=3000,8080,9000  # Ports to forward via Tailscale
```

### Optional Tailscale Settings
```env
TAILSCALE_ACCEPT_DNS=true|false
TAILSCALE_ACCEPT_ROUTES=true|false
TAILSCALE_ADVERTISE_EXIT_NODE=true|false
TAILSCALE_ADVERTISE_ROUTES=
TAILSCALE_SSH=true|false
```

## Usage Examples

### Example 1: Basic Web Application with Cloudflare Only

This example shows how to expose a simple web application through Cloudflare Tunnel.

```yaml
services:
  secure-proxy:
    image: hhftechnology/cloudflare-tailscale-integration:latest
    environment:
      - ENABLE_CLOUDFLARE=true
      - ENABLE_TAILSCALE=false
      - CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
    volumes:
      - ./cloudflared:/etc/cloudflared
    restart: unless-stopped

  webapp:
    image: nginx:alpine
    expose:
      - "80"
```

### Example 2: Internal Service with Tailscale Only

This example demonstrates using Tailscale for private access to an internal dashboard.

```yaml
version: '3'
services:
  secure-proxy:
    image: hhftechnology/cloudflare-tailscale-integration:latest
    cap_add:
      - NET_ADMIN
    environment:
      - ENABLE_CLOUDFLARE=false
      - ENABLE_TAILSCALE=true
      - TAILSCALE_AUTH_KEY=tskey-auth-xxxxx-xxxxxxxxxxxxx
      - TAILSCALE_HOSTNAME=internal-dashboard
      - TARGET_PORTS=3000
    volumes:
      - ./data/tailscale:/var/lib/tailscale
    devices:
      - /dev/net/tun:/dev/net/tun

  dashboard:
    image: grafana/grafana
    expose:
      - "3000"
```

### Example 3: Split Access - Public Website and Private Admin Panel

This example shows how to use both Cloudflare and Tailscale to provide different access methods for different components.

```yaml
services:
  secure-proxy:
    image: hhftechnology/cloudflare-tailscale-integration:latest
    cap_add:
      - NET_ADMIN
    environment:
      - ENABLE_CLOUDFLARE=true
      - ENABLE_TAILSCALE=true
      - CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
      - TAILSCALE_AUTH_KEY=tskey-auth-xxxxx-xxxxxxxxxxxxx
      - TAILSCALE_HOSTNAME=admin-portal
      - TARGET_PORTS=8080
    volumes:
      - ./data/tailscale:/var/lib/tailscale
      - ./data/cloudflared:/etc/cloudflared
    devices:
      - /dev/net/tun:/dev/net/tun

  website:
    image: nginx:alpine
    expose:
      - "80"  # Exposed via Cloudflare

  admin:
    image: adminer
    expose:
      - "8080"  # Exposed via Tailscale
```

### Example 4: Multi-Service Development Environment

This example creates a development environment with multiple services accessible through Tailscale.

```yaml
services:
  secure-proxy:
    image: hhftechnology/cloudflare-tailscale-integration:latest
    cap_add:
      - NET_ADMIN
    environment:
      - ENABLE_CLOUDFLARE=false
      - ENABLE_TAILSCALE=true
      - TAILSCALE_AUTH_KEY=tskey-auth-xxxxx-xxxxxxxxxxxxx
      - TAILSCALE_HOSTNAME=dev-environment
      - TARGET_PORTS=3000,8080,5432,6379
    volumes:
      - ./data/tailscale:/var/lib/tailscale
    devices:
      - /dev/net/tun:/dev/net/tun

  frontend:
    image: node:alpine
    working_dir: /app
    command: npm start
    expose:
      - "3000"

  backend:
    image: python:alpine
    command: python manage.py runserver 0.0.0.0:8080
    expose:
      - "8080"

  db:
    image: postgres:alpine
    expose:
      - "5432"

  redis:
    image: redis:alpine
    expose:
      - "6379"
```

### Example 5: Hybrid Cloud Application

This example demonstrates a hybrid cloud setup where some services are public and others are private.

```yaml
services:
  secure-proxy:
    image: hhftechnology/cloudflare-tailscale-integration:latest
    cap_add:
      - NET_ADMIN
    environment:
      - ENABLE_CLOUDFLARE=true
      - ENABLE_TAILSCALE=true
      - CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
      - TAILSCALE_AUTH_KEY=tskey-auth-xxxxx-xxxxxxxxxxxxx
      - TAILSCALE_HOSTNAME=hybrid-app
      - TARGET_PORTS=9000,5432
    volumes:
      - ./data/tailscale:/var/lib/tailscale
      - ./data/cloudflared:/etc/cloudflared
    devices:
      - /dev/net/tun:/dev/net/tun

  api:
    image: node:alpine
    expose:
      - "80"  # Public API via Cloudflare

  management:
    image: portainer/portainer-ce
    expose:
      - "9000"  # Private management via Tailscale

  database:
    image: postgres:alpine
    expose:
      - "5432"  # Private database access via Tailscale
```

### Example 6: Microservices with Mixed Access

This example shows a microservices architecture with different access patterns for different services.

```yaml
version: '3'
services:
  secure-proxy:
    image: hhftechnology/cloudflare-tailscale-integration:latest
    cap_add:
      - NET_ADMIN
    environment:
      - ENABLE_CLOUDFLARE=true
      - ENABLE_TAILSCALE=true
      - CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
      - TAILSCALE_AUTH_KEY=tskey-auth-xxxxx-xxxxxxxxxxxxx
      - TAILSCALE_HOSTNAME=microservices
      - TARGET_PORTS=8080,9090,3000,5432
    volumes:
      - ./data/tailscale:/var/lib/tailscale
      - ./data/cloudflared:/etc/cloudflared
    devices:
      - /dev/net/tun:/dev/net/tun

  gateway:
    image: nginx:alpine
    expose:
      - "80"  # Public API Gateway via Cloudflare

  auth-service:
    image: node:alpine
    expose:
      - "8080"  # Private auth service via Tailscale

  metrics:
    image: prom/prometheus
    expose:
      - "9090"  # Private metrics via Tailscale

  admin-dashboard:
    image: grafana/grafana
    expose:
      - "3000"  # Private dashboard via Tailscale

  database:
    image: postgres:alpine
    expose:
      - "5432"  # Private database via Tailscale
```

## Network Architecture

When using both Cloudflare Tunnels and Tailscale, the secure-proxy container acts as a gateway:

1. Cloudflare Tunnel provides secure public access to services marked for public exposure
2. Tailscale provides private, encrypted access to services marked for internal use
3. The proxy automatically handles routing and network isolation

## Security Considerations

1. Always use strong authentication keys and tokens
2. Regularly rotate your Cloudflare and Tailscale credentials
3. Monitor access logs and usage patterns
4. Keep the Docker image and all services updated
5. Follow the principle of least privilege when exposing services

## Troubleshooting

### Common Issues

1. Connection Issues:
```bash
# Check Tailscale status
docker exec secure-proxy tailscale status

# Check Cloudflare tunnel status
docker exec secure-proxy cloudflared tunnel info

# View logs
docker logs secure-proxy
```

2. Port Forwarding Issues:
```bash
# Check iptables rules
docker exec secure-proxy iptables -t nat -L PREROUTING

# Verify network interfaces
docker exec secure-proxy ip addr show
```

## Support

For issues, feature requests, or contributions, please visit our GitHub repository:
[https://github.com/hhftechnology/cloudflare-tailscale-integration](https://github.com/hhftechnology/cloudflare-tailscale-integration)

## License

MIT License - See LICENSE file for details