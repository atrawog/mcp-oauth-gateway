#!/usr/bin/env python3
"""Simulate what happens with different Traefik routing configurations."""

def test_traefik_routing(path, rules):
    """Simulate Traefik routing decision."""
    print(f"\nTesting path: {path}")
    print("-" * 50)

    for rule_name, rule_config in rules.items():
        rule = rule_config["rule"]
        priority = rule_config.get("priority", 0)

        # Simulate rule matching
        host_match = "Host(`mcp-fetch.domain.com`)" in rule

        if "PathPrefix(`/mcp`)" in rule:
            path_match = path.startswith("/mcp")
        elif "Path(`/health`)" in rule:
            path_match = path == "/health"
        elif rule == "Host(`mcp-fetch.domain.com`)":
            # Host-only rule matches all paths on that host
            path_match = True
        else:
            path_match = False

        total_match = host_match and path_match

        print(f"Rule: {rule_name}")
        print(f"  Rule: {rule}")
        print(f"  Priority: {priority}")
        print(f"  Host match: {host_match}")
        print(f"  Path match: {path_match}")
        print(f"  Total match: {total_match}")

        if total_match:
            print("  ✓ This rule would handle the request!")

# Original configuration (missing PathPrefix)
print("\n" + "="*70)
print("ORIGINAL CONFIGURATION (BUG)")
print("="*70)

original_rules = {
    "mcp-fetch-health": {
        "rule": "Host(`mcp-fetch.domain.com`) && Path(`/health`)",
        "priority": 3
    },
    "mcp-fetch": {
        "rule": "Host(`mcp-fetch.domain.com`)",  # Missing PathPrefix!
        "priority": 2
    },
    "mcp-fetch-catchall": {
        "rule": "Host(`mcp-fetch.domain.com`)",
        "priority": 1
    }
}

# Test the problematic path
test_traefik_routing("/mcp", original_rules)

# Fixed configuration
print("\n" + "="*70)
print("FIXED CONFIGURATION")
print("="*70)

fixed_rules = {
    "mcp-fetch-health": {
        "rule": "Host(`mcp-fetch.domain.com`) && Path(`/health`)",
        "priority": 3
    },
    "mcp-fetch": {
        "rule": "Host(`mcp-fetch.domain.com`) && PathPrefix(`/mcp`)",  # Fixed!
        "priority": 2
    },
    "mcp-fetch-catchall": {
        "rule": "Host(`mcp-fetch.domain.com`)",
        "priority": 1
    }
}

test_traefik_routing("/mcp", fixed_rules)

# Test other paths
print("\n" + "="*70)
print("TESTING OTHER PATHS WITH FIXED CONFIG")
print("="*70)

for path in ["/", "/health", "/mcp/tools/list", "/random"]:
    test_traefik_routing(path, fixed_rules)
