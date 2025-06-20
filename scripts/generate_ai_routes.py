#!/usr/bin/env python3
"""Generate Traefik routing labels for AI model hostnames"""

AI_MODELS = ["aria", "atlas", "cipher", "echo", "lyra", "nova", "prism", "sage", "verse", "zenith"]

def generate_routes_for_model(model: str) -> str:
    """Generate all required routes for a single AI model hostname"""
    return f"""      # {model.capitalize()}
      # Health check route - Priority 5 (high priority for specific path)
      - "traefik.http.routers.mcp-fetch-{model}-health.rule=Host(`mcp-fetch-{model}.${{BASE_DOMAIN}}`) && Path(`/health`)"
      - "traefik.http.routers.mcp-fetch-{model}-health.priority=5"
      - "traefik.http.routers.mcp-fetch-{model}-health.entrypoints=websecure"
      - "traefik.http.routers.mcp-fetch-{model}-health.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mcp-fetch-{model}-health.service=mcp-fetch"
      # No auth middleware - health check must be public!
      
      # OAuth discovery route - Priority 10 (highest priority)
      - "traefik.http.routers.mcp-fetch-{model}-oauth-discovery.rule=Host(`mcp-fetch-{model}.${{BASE_DOMAIN}}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
      - "traefik.http.routers.mcp-fetch-{model}-oauth-discovery.priority=10"
      - "traefik.http.routers.mcp-fetch-{model}-oauth-discovery.entrypoints=websecure"
      - "traefik.http.routers.mcp-fetch-{model}-oauth-discovery.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mcp-fetch-{model}-oauth-discovery.middlewares=oauth-discovery-rewrite@docker"
      - "traefik.http.routers.mcp-fetch-{model}-oauth-discovery.service=auth@docker"
      # No auth middleware - OAuth discovery must be public!
      
      # MCP route with auth - Priority 2
      - "traefik.http.routers.mcp-fetch-{model}.rule=Host(`mcp-fetch-{model}.${{BASE_DOMAIN}}`) && PathPrefix(`/mcp`)"
      - "traefik.http.routers.mcp-fetch-{model}.priority=2"
      - "traefik.http.routers.mcp-fetch-{model}.entrypoints=websecure"
      - "traefik.http.routers.mcp-fetch-{model}.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mcp-fetch-{model}.middlewares=mcp-auth@docker"
      - "traefik.http.routers.mcp-fetch-{model}.service=mcp-fetch"
      
      # Catch-all route with auth - Priority 1 (lowest)
      - "traefik.http.routers.mcp-fetch-{model}-catchall.rule=Host(`mcp-fetch-{model}.${{BASE_DOMAIN}}`)"
      - "traefik.http.routers.mcp-fetch-{model}-catchall.priority=1"
      - "traefik.http.routers.mcp-fetch-{model}-catchall.entrypoints=websecure"
      - "traefik.http.routers.mcp-fetch-{model}-catchall.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mcp-fetch-{model}-catchall.middlewares=mcp-auth@docker"
      - "traefik.http.routers.mcp-fetch-{model}-catchall.service=mcp-fetch"
"""

def main():
    print("# Additional AI model hostnames routing configuration")
    print("# Add these labels to the mcp-fetch service in docker-compose.yml")
    print()
    
    for model in AI_MODELS:
        print(generate_routes_for_model(model))

if __name__ == "__main__":
    main()