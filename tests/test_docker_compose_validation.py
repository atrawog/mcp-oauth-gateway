"""Test Docker Compose Configuration Validation
Following CLAUDE.md - Testing configuration correctness.
"""

import os

import yaml


class TestDockerComposeValidation:
    """Validate Docker Compose configurations are complete and correct."""

    def test_mcp_fetch_traefik_labels_complete(self):
        """Test that mcp-fetch has all required Traefik labels."""
        # Read the docker-compose.yml file
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "mcp-fetch/docker-compose.yml"
        )

        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)

        # Get the mcp-fetch service configuration
        assert "services" in compose_config
        assert "mcp-fetch" in compose_config["services"]

        service = compose_config["services"]["mcp-fetch"]
        assert "labels" in service

        labels = service["labels"]

        # Convert list of labels to dict for easier checking
        label_dict = {}
        for label in labels:
            if isinstance(label, str) and "=" in label:
                key, value = label.split("=", 1)
                label_dict[key.strip().strip('"')] = value.strip().strip('"')

        # Check Traefik is enabled
        assert "traefik.enable" in label_dict
        assert label_dict["traefik.enable"] == "true"

        # Define required routers and their required labels
        routers = {
            "mcp-fetch": {
                "needs_auth": True,
                "path_rule": [
                    "PathPrefix(`/mcp`)",
                    "(Path(`/mcp`) || PathPrefix(`/mcp/`))",
                ],
            },
            "mcp-fetch-catchall": {
                "needs_auth": True,
                "path_rule": None,  # Host-only rule
            },
        }

        # Check each router has required labels
        for router_name, router_config in routers.items():
            prefix = f"traefik.http.routers.{router_name}"

            # Must have a rule
            assert f"{prefix}.rule" in label_dict, f"Router {router_name} missing rule!"

            # Check rule includes Host
            assert "Host(`fetch.${BASE_DOMAIN}`)" in label_dict[f"{prefix}.rule"], (
                f"Router {router_name} rule missing Host!"
            )

            # Check path rule if required
            if router_config["path_rule"]:
                # Accept any of the possible path rules
                rule_found = False
                if isinstance(router_config["path_rule"], list):
                    for path_rule in router_config["path_rule"]:
                        if path_rule in label_dict[f"{prefix}.rule"]:
                            rule_found = True
                            break
                else:
                    rule_found = (
                        router_config["path_rule"] in label_dict[f"{prefix}.rule"]
                    )

                assert rule_found, (
                    f"Router {router_name} rule missing expected path rule!"
                )

            # Must have a service assignment - THIS IS THE KEY CHECK!
            assert f"{prefix}.service" in label_dict, (
                f"Router {router_name} missing service assignment! This causes 404 errors!"  # TODO: Break long line
            )

            assert label_dict[f"{prefix}.service"] == "mcp-fetch", (
                f"Router {router_name} service should be 'mcp-fetch'!"
            )

            # Must have priority
            assert f"{prefix}.priority" in label_dict, (
                f"Router {router_name} missing priority!"
            )

            # Must have entrypoints
            assert f"{prefix}.entrypoints" in label_dict, (
                f"Router {router_name} missing entrypoints!"
            )

            # Must have TLS configuration
            assert f"{prefix}.tls.certresolver" in label_dict, (
                f"Router {router_name} missing TLS certresolver!"
            )

            # Check auth middleware if needed
            if router_config["needs_auth"]:
                assert f"{prefix}.middlewares" in label_dict, (
                    f"Router {router_name} missing auth middleware!"
                )
                assert "mcp-auth@docker" in label_dict[f"{prefix}.middlewares"], (
                    f"Router {router_name} should use mcp-auth middleware!"
                )

        # Check service definition exists
        assert (
            "traefik.http.services.mcp-fetch.loadbalancer.server.port" in label_dict
        ), "Missing service port definition!"

        assert (
            label_dict["traefik.http.services.mcp-fetch.loadbalancer.server.port"]
            == "3000"
        ), "Service port should be 3000!"

    def test_all_services_have_traefik_configuration(self):
        """Test that all services with Traefik enabled have complete configuration."""
        # List of services that should have Traefik configuration
        services_to_check = [
            ("auth/docker-compose.yml", "auth"),
            ("mcp-fetch/docker-compose.yml", "mcp-fetch"),
            ("traefik/docker-compose.yml", "traefik"),
        ]

        for compose_file, service_name in services_to_check:
            if service_name == "traefik":
                continue  # Traefik doesn't route to itself

            compose_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), compose_file
            )

            if not os.path.exists(compose_path):
                continue

            with open(compose_path) as f:
                compose_config = yaml.safe_load(f)

            if "services" not in compose_config:
                continue

            if service_name not in compose_config["services"]:
                continue

            service = compose_config["services"][service_name]

            if "labels" not in service:
                continue

            labels = service["labels"]
            label_dict = {}
            for label in labels:
                if isinstance(label, str) and "=" in label:
                    key, value = label.split("=", 1)
                    label_dict[key.strip().strip('"')] = value.strip().strip('"')

            # If Traefik is enabled, check for completeness
            if label_dict.get("traefik.enable") == "true":
                # Find all routers
                routers = set()
                for key in label_dict:
                    if key.startswith("traefik.http.routers.") and ".rule" in key:
                        router = key.split(".")[3]  # Extract router name
                        routers.add(router)

                # Check each router has a service assignment
                for router in routers:
                    assert f"traefik.http.routers.{router}.service" in label_dict, (
                        f"Service {service_name} router {router} missing service assignment!"  # TODO: Break long line
                    )

    def test_routing_priorities_are_correct(self):
        """Test that routing priorities follow the correct pattern."""
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "mcp-fetch/docker-compose.yml"
        )

        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)

        service = compose_config["services"]["mcp-fetch"]
        labels = service["labels"]

        # Convert to dict
        label_dict = {}
        for label in labels:
            if isinstance(label, str) and "=" in label:
                key, value = label.split("=", 1)
                label_dict[key.strip().strip('"')] = value.strip().strip('"')

        # Check priorities
        priorities = {
            "mcp-fetch": 2,  # Middle - path prefix
            "mcp-fetch-catchall": 1,  # Lowest - host only
        }

        for router, expected_priority in priorities.items():
            key = f"traefik.http.routers.{router}.priority"
            assert key in label_dict, f"Router {router} missing priority!"
            assert int(label_dict[key]) == expected_priority, (
                f"Router {router} has wrong priority: {label_dict[key]} (expected {expected_priority})"  # TODO: Break long line
            )
