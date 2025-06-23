#!/usr/bin/env python3
"""Simulate what the validation test would report with missing service label."""

# Simulate the label dict without the service assignment
label_dict_broken = {
    "traefik.enable": "true",
    "traefik.http.routers.mcp-fetch.rule": "Host(`mcp-fetch.${BASE_DOMAIN}`) && PathPrefix(`/mcp`)",
    "traefik.http.routers.mcp-fetch.priority": "2",
    "traefik.http.routers.mcp-fetch.entrypoints": "websecure",
    "traefik.http.routers.mcp-fetch.tls.certresolver": "letsencrypt",
    "traefik.http.routers.mcp-fetch.middlewares": "mcp-auth@docker",
    # MISSING: 'traefik.http.routers.mcp-fetch.service': 'mcp-fetch',
    "traefik.http.services.mcp-fetch.loadbalancer.server.port": "3000",
}

# Check what the test would find
router_name = "mcp-fetch"
prefix = f"traefik.http.routers.{router_name}"

print("Checking router:", router_name)
print("-" * 50)

# Check for service assignment
if f"{prefix}.service" in label_dict_broken:
    print(f"✓ Router {router_name} has service assignment")
else:
    print(f"✗ Router {router_name} missing service assignment!")
    print("  This causes 404 errors because Traefik doesn't know where to route!")
    print("  The router will match requests but have no backend service.")

print("\nWhat happens in Traefik:")
print("1. Request arrives at https://mcp-fetch.domain.com/mcp")
print("2. Router 'mcp-fetch' matches (Host + PathPrefix rule)")
print("3. Traefik looks for the service to route to")
print("4. No service is assigned to this router!")
print("5. Traefik returns 404 Not Found")

print("\nThe fix:")
print('Add label: - "traefik.http.routers.mcp-fetch.service=mcp-fetch"')
