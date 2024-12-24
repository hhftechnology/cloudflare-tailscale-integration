#!/usr/bin/env python3

import os
import subprocess
import json
import time
import logging
import sys
from typing import List, Dict, Optional
from pathlib import Path

# Configure logging with a consistent format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TailscaleSetup:
    """
    Handles the configuration and setup of Tailscale networking.
    Manages all Tailscale-specific parameters and their implementation.
    """
    def __init__(self):
        # Basic Tailscale configuration
        self.hostname = os.environ.get('TS_HOSTNAME', os.environ.get('HOSTNAME', 'secure-service'))
        self.auth_key = os.environ.get('TAILSCALE_AUTHKEY')
        self.state_dir = os.environ.get('TS_STATE_DIR', '/var/lib/tailscale')
        self.socket = os.environ.get('TS_SOCKET', '/var/run/tailscale/tailscaled.sock')
        
        # Feature flags and advanced settings
        self.accept_dns = os.environ.get('TS_ACCEPT_DNS', 'false').lower() == 'true'
        self.auth_once = os.environ.get('TS_AUTH_ONCE', 'false').lower() == 'true'
        self.dest_ip = os.environ.get('TS_DEST_IP', '')
        self.routes = os.environ.get('TS_ROUTES', '')
        self.userspace = os.environ.get('TS_USERSPACE', 'true').lower() == 'true'
        
        # Proxy configurations
        self.outbound_http_proxy = os.environ.get('TS_OUTBOUND_HTTP_PROXY_LISTEN', '')
        self.socks5_server = os.environ.get('TS_SOCKS5_SERVER', '')
        
        # Extra arguments for fine-tuning
        self.extra_args = os.environ.get('TS_EXTRA_ARGS', '').split()
        self.tailscaled_extra_args = os.environ.get('TS_TAILSCALED_EXTRA_ARGS', '').split()

    def build_tailscaled_command(self) -> List[str]:
        """
        Constructs the tailscaled command with all configured options.
        Returns:
            List[str]: Complete command for starting tailscaled
        """
        cmd = ['/usr/sbin/tailscaled']
        
        # Add standard parameters
        cmd.extend(['--state', self.state_dir])
        cmd.extend(['--socket', self.socket])
        
        # Add userspace mode if enabled
        if self.userspace:
            cmd.append('--userspace-networking')
        
        # Add any extra tailscaled arguments
        if self.tailscaled_extra_args:
            cmd.extend(self.tailscaled_extra_args)
            
        return cmd

    def build_tailscale_up_command(self) -> List[str]:
        """
        Constructs the tailscale up command with all configured options.
        Returns:
            List[str]: Complete command for tailscale up
        """
        cmd = ['tailscale', 'up']
        
        # Add authentication key
        if self.auth_key:
            cmd.extend(['--authkey', self.auth_key])
        
        # Add hostname
        if self.hostname:
            cmd.extend(['--hostname', self.hostname])
            
        # Add DNS acceptance if configured
        if self.accept_dns:
            cmd.append('--accept-dns')
            
        # Add routes if configured
        if self.routes:
            cmd.extend(['--advertise-routes', self.routes])
            
        # Add destination IP if configured
        if self.dest_ip:
            cmd.extend(['--dest-ip', self.dest_ip])
            
        # Add proxy configurations if set
        if self.outbound_http_proxy:
            cmd.extend(['--outbound-http-proxy-listen', self.outbound_http_proxy])
        if self.socks5_server:
            cmd.extend(['--socks5-server', self.socks5_server])
            
        # Add any extra arguments
        if self.extra_args:
            cmd.extend(self.extra_args)
            
        return cmd

    def setup_tailscale(self):
        """
        Sets up Tailscale with all configured options.
        Raises:
            ValueError: If required configuration is missing
            subprocess.CalledProcessError: If a command fails
        """
        if not self.auth_key and not self.auth_once:
            raise ValueError("TAILSCALE_AUTHKEY is required when Tailscale is enabled and TS_AUTH_ONCE is false")

        # Ensure state directory exists
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)

        # Start tailscaled with configured options
        tailscaled_cmd = self.build_tailscaled_command()
        try:
            subprocess.Popen(tailscaled_cmd)
            logger.info("Started tailscaled service")
            
            # Wait for tailscaled to start
            time.sleep(5)
            
            # If auth_once is true, check if already authenticated
            if self.auth_once:
                try:
                    status = subprocess.run(
                        ['tailscale', 'status'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if "Logged in" in status.stdout:
                        logger.info("Already logged in, skipping authentication")
                        return
                except subprocess.CalledProcessError:
                    logger.info("Not logged in, proceeding with authentication")
            
            # Run tailscale up with all configured options
            up_cmd = self.build_tailscale_up_command()
            subprocess.run(up_cmd, check=True)
            
            logger.info("Tailscale setup completed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup Tailscale: {str(e)}")
            raise

class CloudflareSetup:
    """
    Handles the configuration and setup of Cloudflare tunnels.
    Manages tunnel creation and configuration.
    """
    def __init__(self):
        self.token = os.environ.get('CLOUDFLARED_TOKEN')
        self.hostname = os.environ.get('HOSTNAME', 'secure-service')
        self.tunnel_name = os.environ.get('TUNNEL_NAME', f"tunnel-{self.hostname}")
        self.service_port = os.environ.get('SERVICE_PORT', '8080')
        self.service_protocol = os.environ.get('SERVICE_PROTOCOL', 'http')

    def create_config(self) -> Dict:
        """
        Creates the Cloudflare tunnel configuration.
        Returns:
            Dict: Complete tunnel configuration
        """
        return {
            "tunnel": self.tunnel_name,
            "credentials-file": "/etc/cloudflared/credentials.json",
            "ingress": [
                {
                    "hostname": self.hostname,
                    "service": f"{self.service_protocol}://localhost:{self.service_port}",
                    "originRequest": {
                        "noTLSVerify": False,
                        "connectTimeout": "10s",
                        "keepAliveTimeout": "30s"
                    }
                },
                {
                    "service": "http_status:404"
                }
            ],
            "logfile": "/var/log/cloudflared.log",
            "loglevel": "info"
        }

    def setup_cloudflare(self):
        """
        Sets up Cloudflare tunnel with the provided configuration.
        Raises:
            ValueError: If required configuration is missing
            subprocess.CalledProcessError: If a command fails
        """
        if not self.token:
            raise ValueError("CLOUDFLARED_TOKEN is required when Cloudflare tunnel is enabled")
        
        logger.info("Setting up Cloudflare tunnel...")
        
        # Ensure config directory exists
        Path("/etc/cloudflared").mkdir(parents=True, exist_ok=True)
        
        # Create and save configuration
        config = self.create_config()
        config_path = "/etc/cloudflared/config.yml"
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created Cloudflare configuration at {config_path}")
        
        # Create tunnel
        try:
            subprocess.run(['cloudflared', 'tunnel', 'create', self.tunnel_name], check=True)
            logger.info(f"Created Cloudflare tunnel: {self.tunnel_name}")
        except subprocess.CalledProcessError as e:
            if 'already exists' not in str(e):
                logger.error(f"Failed to create Cloudflare tunnel: {str(e)}")
                raise
            logger.warning(f"Tunnel '{self.tunnel_name}' already exists, continuing...")

class SecureServiceSetup:
    """
    Main setup class that orchestrates both Tailscale and Cloudflare configurations.
    """
    def __init__(self):
        self.enable_cloudflare = os.environ.get('ENABLE_CLOUDFLARE', 'false').lower() == 'true'
        self.enable_tailscale = os.environ.get('ENABLE_TAILSCALE', 'false').lower() == 'true'
        
        if not (self.enable_cloudflare or self.enable_tailscale):
            logger.warning("Neither Cloudflare nor Tailscale is enabled!")
        
        self.cloudflare = CloudflareSetup() if self.enable_cloudflare else None
        self.tailscale = TailscaleSetup() if self.enable_tailscale else None

    def run(self):
        """
        Runs the complete setup process for enabled services.
        """
        try:
            if self.enable_cloudflare:
                logger.info("Starting Cloudflare setup...")
                self.cloudflare.setup_cloudflare()
                
            if self.enable_tailscale:
                logger.info("Starting Tailscale setup...")
                self.tailscale.setup_tailscale()
                
            logger.info("Setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        setup = SecureServiceSetup()
        setup.run()
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during setup: {str(e)}")
        sys.exit(1)