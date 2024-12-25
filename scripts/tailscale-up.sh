#!/bin/bash
set -e

# Wait for tailscaled to start
sleep 5

# Check if auth key is provided
if [ -z "${TAILSCALE_AUTH_KEY}" ]; then
    echo "Error: TAILSCALE_AUTH_KEY is not set"
    exit 1
fi

echo "Starting Tailscale authentication..."
TAILSCALE_UP_FLAGS=(
    --auth-key="${TAILSCALE_AUTH_KEY}"
    --hostname="${TAILSCALE_HOSTNAME:-$(hostname)}"
    --accept-dns=${TAILSCALE_ACCEPT_DNS:-true}
    --accept-routes=${TAILSCALE_ACCEPT_ROUTES:-false}
    --advertise-exit-node=${TAILSCALE_ADVERTISE_EXIT_NODE:-false}
    --ssh=${TAILSCALE_SSH:-false}
)

# Add advertise-routes if specified
if [ -n "${TAILSCALE_ADVERTISE_ROUTES}" ]; then
    TAILSCALE_UP_FLAGS+=(--advertise-routes="${TAILSCALE_ADVERTISE_ROUTES}")
fi

# Try to authenticate with retries
MAX_RETRIES=3
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Authentication attempt $i of $MAX_RETRIES..."
    
    if tailscale up "${TAILSCALE_UP_FLAGS[@]}" 2>&1; then
        echo "Tailscale authentication successful!"
        
        # Wait for connection to be fully established
        for ((j=1; j<=10; j++)); do
            if tailscale status | grep -q "authenticated"; then
                echo "Tailscale connection confirmed!"
                exit 0
            fi
            echo "Waiting for connection to establish... ($j/10)"
            sleep 2
        done
    fi
    
    echo "Retrying in 5 seconds..."
    sleep 5
done

echo "Failed to authenticate after $MAX_RETRIES attempts"
exit 1