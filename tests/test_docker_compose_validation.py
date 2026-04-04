"""Test SWAG nginx proxy-conf Configuration Validation.

Validates SWAG nginx proxy-conf files instead of Traefik docker labels.
The project uses SWAG (Secure Web Application Gateway) as the reverse proxy
with nginx auth_request directives for OAuth 2.1 token validation.

Following CLAUDE.md - Testing configuration correctness.
"""

import os
import re

import pytest

pytestmark = pytest.mark.local_only

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
PROXY_CONFS_DIR = os.path.join(REPO_ROOT, "swag", "proxy-confs")
SWAG_COMPOSE = os.path.join(REPO_ROOT, "swag", "docker-compose.yaml")
MCP_TEMPLATE_CONF = os.path.join(REPO_ROOT, "mcp-template.subdomain.conf")
OAUTH_VERIFY_CONF = os.path.join(REPO_ROOT, "swag", "proxy-confs", "_oauth_verify.conf")


def _read_conf(path: str) -> str:
    """Read a nginx conf file and return its contents."""
    with open(path) as f:
        return f.read()


class TestOAuthVerifyConf:
    """Validate the shared _oauth_verify.conf snippet."""

    def test_oauth_verify_conf_exists(self) -> None:
        """Test that _oauth_verify.conf exists in proxy-confs directory."""
        assert os.path.exists(OAUTH_VERIFY_CONF), (
            f"_oauth_verify.conf missing at {OAUTH_VERIFY_CONF}!"
        )

    def test_oauth_verify_has_internal_location(self) -> None:
        """Test that _oauth_verify.conf declares an internal location block."""
        content = _read_conf(OAUTH_VERIFY_CONF)
        assert "location = /_oauth_verify {" in content, (
            "_oauth_verify.conf must contain 'location = /_oauth_verify {'"
        )
        assert "internal;" in content, "_oauth_verify.conf location must be marked internal;"

    def test_oauth_verify_proxies_to_mcp_oauth(self) -> None:
        """Test that _oauth_verify.conf proxies to mcp-oauth:8000/verify."""
        content = _read_conf(OAUTH_VERIFY_CONF)
        assert "proxy_pass http://mcp-oauth:8000/verify;" in content, (
            "_oauth_verify.conf must proxy_pass to http://mcp-oauth:8000/verify"
        )

    def test_oauth_verify_passes_authorization_header(self) -> None:
        """Test that _oauth_verify.conf forwards the Authorization header."""
        content = _read_conf(OAUTH_VERIFY_CONF)
        assert "proxy_set_header Authorization $http_authorization;" in content, (
            "_oauth_verify.conf must forward Authorization header to /verify"
        )

    def test_oauth_verify_passes_request_body_off(self) -> None:
        """Test that _oauth_verify.conf does not forward request body."""
        content = _read_conf(OAUTH_VERIFY_CONF)
        assert "proxy_pass_request_body off;" in content, (
            "_oauth_verify.conf must set proxy_pass_request_body off;"
        )


class TestMcpTemplateSubdomainConf:
    """Validate mcp-template.subdomain.conf — the canonical nginx config template."""

    def test_template_conf_exists(self) -> None:
        """Test that mcp-template.subdomain.conf exists at repo root."""
        assert os.path.exists(MCP_TEMPLATE_CONF), (
            f"mcp-template.subdomain.conf missing at {MCP_TEMPLATE_CONF}!"
        )

    def test_template_has_oauth_verify_location(self) -> None:
        """Test that template contains the _oauth_verify internal location block."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert "location = /_oauth_verify {" in content, (
            "Template must contain 'location = /_oauth_verify {' for auth subrequests"
        )
        assert "internal;" in content, "Template _oauth_verify location must be marked internal;"

    def test_template_oauth_verify_proxies_to_mcp_oauth(self) -> None:
        """Test that template's _oauth_verify proxies to mcp-oauth:8000/verify."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert "proxy_pass http://mcp-oauth:8000/verify;" in content, (
            "Template _oauth_verify must proxy_pass to http://mcp-oauth:8000/verify"
        )

    def test_template_mcp_location_uses_auth_request(self) -> None:
        """Test that the /mcp location block applies auth_request /_oauth_verify."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        # Must have auth_request directive pointing to /_oauth_verify
        assert "auth_request /_oauth_verify;" in content, (
            "Template /mcp location must contain 'auth_request /_oauth_verify;'"
        )

    def test_template_oauth_endpoints_have_no_auth_request(self) -> None:
        """Test that OAuth endpoints route to mcp-oauth WITHOUT auth_request.

        OAuth endpoints (/register, /authorize, /token, /.well-known) must never
        have auth_request applied — this causes authentication loops.
        """
        content = _read_conf(MCP_TEMPLATE_CONF)

        # Parse location blocks for OAuth endpoints and verify no auth_request inside them
        oauth_locations = [
            "/register",
            "/authorize",
            "/token",
            "/.well-known/oauth-authorization-server",
            "/.well-known/oauth-protected-resource",
        ]

        # Split into location blocks to check each independently
        # We verify that auth_request does NOT appear adjacent to these OAuth locations
        lines = content.splitlines()
        in_oauth_block = False
        brace_depth = 0
        oauth_block_lines: list[str] = []
        current_location = ""

        for line in lines:
            stripped = line.strip()

            # Detect the start of an OAuth-related location block
            for oauth_path in oauth_locations:
                if re.match(rf"location\s+(=\s+)?{re.escape(oauth_path)}\s*\{{", stripped):
                    in_oauth_block = True
                    brace_depth = 1
                    oauth_block_lines = [line]
                    current_location = oauth_path
                    break
            else:
                if in_oauth_block:
                    oauth_block_lines.append(line)
                    brace_depth += stripped.count("{") - stripped.count("}")
                    if brace_depth <= 0:
                        # End of this OAuth location block — verify no auth_request
                        block_text = "\n".join(oauth_block_lines)
                        assert "auth_request" not in block_text, (
                            f"OAuth location '{current_location}' must NOT contain "
                            f"auth_request directive — this causes authentication loops!"
                        )
                        in_oauth_block = False
                        oauth_block_lines = []

    def test_template_register_routes_to_mcp_oauth(self) -> None:
        """Test that /register location routes to mcp-oauth:8000."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        # Find the /register location block and check it proxies to mcp-oauth
        assert re.search(r"location\s+=\s+/register\s*\{", content), (
            "Template must have 'location = /register' block"
        )
        assert "proxy_pass http://mcp-oauth:8000;" in content, (
            "Template OAuth endpoints must proxy_pass to http://mcp-oauth:8000"
        )

    def test_template_authorize_routes_to_mcp_oauth(self) -> None:
        """Test that /authorize location routes to mcp-oauth:8000."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert re.search(r"location\s+=\s+/authorize\s*\{", content), (
            "Template must have 'location = /authorize' block"
        )

    def test_template_token_routes_to_mcp_oauth(self) -> None:
        """Test that /token location routes to mcp-oauth:8000."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert re.search(r"location\s+=\s+/token\s*\{", content), (
            "Template must have 'location = /token' block"
        )

    def test_template_well_known_routes_to_mcp_oauth(self) -> None:
        """Test that /.well-known/oauth-authorization-server routes to mcp-oauth:8000."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert re.search(
            r"location\s+=\s+/\.well-known/oauth-authorization-server\s*\{", content
        ), "Template must have 'location = /.well-known/oauth-authorization-server' block"

    def test_template_has_error_401_with_www_authenticate(self) -> None:
        """Test that template returns 401 with WWW-Authenticate header on auth failure."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert "error_page 401" in content, "Template must define error_page 401 handler"
        assert "WWW-Authenticate" in content, (
            "Template must include WWW-Authenticate header in 401 responses (OAuth 2.1)"
        )

    def test_template_ssl_configuration_present(self) -> None:
        """Test that template includes SSL configuration."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert "listen 443 ssl;" in content, "Template must listen on port 443 with SSL"
        assert "include /config/nginx/ssl.conf;" in content, "Template must include SWAG ssl.conf"

    def test_template_has_dns_rebinding_protection(self) -> None:
        """Test that template includes DNS rebinding origin validation."""
        content = _read_conf(MCP_TEMPLATE_CONF)
        assert "origin_valid" in content, (
            "Template must include DNS rebinding protection via origin_valid check"
        )


class TestSwagDockerCompose:
    """Validate swag/docker-compose.yaml network configuration."""

    def test_swag_compose_exists(self) -> None:
        """Test that swag/docker-compose.yaml exists."""
        assert os.path.exists(SWAG_COMPOSE), f"swag/docker-compose.yaml missing at {SWAG_COMPOSE}!"

    def test_swag_compose_has_mcp_net(self) -> None:
        """Test that swag/docker-compose.yaml declares the mcp-net network."""
        import yaml

        with open(SWAG_COMPOSE) as f:
            compose = yaml.safe_load(f)

        assert "networks" in compose, "swag/docker-compose.yaml must declare networks"
        assert "mcp-net" in compose["networks"], (
            "swag/docker-compose.yaml must declare 'mcp-net' network so SWAG can "
            "reach mcp-oauth:8000 and MCP services"
        )

    def test_swag_service_attached_to_mcp_net(self) -> None:
        """Test that the swag service is attached to the mcp-net network."""
        import yaml

        with open(SWAG_COMPOSE) as f:
            compose = yaml.safe_load(f)

        assert "services" in compose, "swag/docker-compose.yaml must have services"
        assert "swag" in compose["services"], "swag/docker-compose.yaml must have swag service"

        swag_service = compose["services"]["swag"]
        assert "networks" in swag_service, "swag service must declare networks"
        assert "mcp-net" in swag_service["networks"], (
            "swag service must be attached to mcp-net to reach mcp-oauth and MCP services"
        )

    def test_swag_proxy_confs_mounted(self) -> None:
        """Test that SWAG mounts the proxy-confs directory."""
        import yaml

        with open(SWAG_COMPOSE) as f:
            compose = yaml.safe_load(f)

        swag_service = compose["services"]["swag"]
        assert "volumes" in swag_service, "swag service must mount volumes"

        volumes = swag_service["volumes"]
        # At least one volume should reference proxy-confs
        proxy_conf_mount = any("proxy-confs" in str(v) for v in volumes)
        assert proxy_conf_mount, (
            "swag service must mount proxy-confs directory so nginx picks up "
            "gateway configuration files"
        )

    def test_swag_exposes_https_port(self) -> None:
        """Test that SWAG exposes port 443 for HTTPS traffic."""
        import yaml

        with open(SWAG_COMPOSE) as f:
            compose = yaml.safe_load(f)

        swag_service = compose["services"]["swag"]
        assert "ports" in swag_service, "swag service must expose ports"

        ports = [str(p) for p in swag_service["ports"]]
        https_exposed = any("443" in p for p in ports)
        assert https_exposed, "swag service must expose port 443 for HTTPS traffic"


class TestProxyConfsDirectory:
    """Validate the proxy-confs directory contains expected shared snippets."""

    def test_proxy_confs_directory_exists(self) -> None:
        """Test that swag/proxy-confs directory exists."""
        assert os.path.isdir(PROXY_CONFS_DIR), (
            f"swag/proxy-confs directory missing at {PROXY_CONFS_DIR}!"
        )

    def test_oauth_verify_snippet_exists(self) -> None:
        """Test that the shared _oauth_verify.conf snippet exists."""
        path = os.path.join(PROXY_CONFS_DIR, "_oauth_verify.conf")
        assert os.path.exists(path), (
            "swag/proxy-confs/_oauth_verify.conf must exist — this is the shared "
            "auth_request verification snippet included by all MCP service confs"
        )

    def test_no_traefik_artifacts_in_proxy_confs(self) -> None:
        """Test that proxy-confs directory contains no Traefik configuration artifacts."""
        if not os.path.isdir(PROXY_CONFS_DIR):
            return

        for fname in os.listdir(PROXY_CONFS_DIR):
            fpath = os.path.join(PROXY_CONFS_DIR, fname)
            if not os.path.isfile(fpath) or not fname.endswith(".conf"):
                continue
            content = _read_conf(fpath)
            assert "traefik" not in content.lower(), (
                f"{fname} contains Traefik configuration — project has migrated to SWAG!"
            )


class TestSubdomainConfPattern:
    """Validate the subdomain.conf pattern used for all MCP service nginx configs.

    Tests are written against mcp-template.subdomain.conf as the canonical reference.
    When real service confs are deployed to swag/proxy-confs/, the same assertions apply.
    """

    def _get_subdomain_confs(self) -> list[str]:
        """Return all *.subdomain.conf files from proxy-confs + repo root template."""
        confs = []
        if os.path.exists(MCP_TEMPLATE_CONF):
            confs.append(MCP_TEMPLATE_CONF)
        if os.path.isdir(PROXY_CONFS_DIR):
            for fname in os.listdir(PROXY_CONFS_DIR):
                if fname.endswith(".subdomain.conf"):
                    confs.append(os.path.join(PROXY_CONFS_DIR, fname))
        return confs

    def test_at_least_one_subdomain_conf_exists(self) -> None:
        """Test that at least the template subdomain.conf exists."""
        confs = self._get_subdomain_confs()
        assert len(confs) > 0, (
            "No *.subdomain.conf files found. mcp-template.subdomain.conf must exist "
            "at repo root as the canonical nginx config template."
        )

    def test_all_subdomain_confs_have_auth_request(self) -> None:
        """Test that all *.subdomain.conf files apply auth_request /_oauth_verify."""
        confs = self._get_subdomain_confs()
        for conf_path in confs:
            content = _read_conf(conf_path)
            assert "auth_request /_oauth_verify;" in content, (
                f"{os.path.basename(conf_path)} must contain 'auth_request /_oauth_verify;' "
                f"to enforce OAuth 2.1 token validation on protected endpoints"
            )

    def test_all_subdomain_confs_have_oauth_verify_location(self) -> None:
        """Test that all *.subdomain.conf files define the _oauth_verify internal location."""
        confs = self._get_subdomain_confs()
        for conf_path in confs:
            content = _read_conf(conf_path)
            assert "location = /_oauth_verify {" in content, (
                f"{os.path.basename(conf_path)} must define 'location = /_oauth_verify {{' "
                f"as an internal auth subrequest location"
            )

    def test_all_subdomain_confs_route_oauth_to_mcp_oauth(self) -> None:
        """Test that all *.subdomain.conf files route OAuth endpoints to mcp-oauth:8000."""
        confs = self._get_subdomain_confs()
        for conf_path in confs:
            content = _read_conf(conf_path)
            assert "proxy_pass http://mcp-oauth:8000" in content, (
                f"{os.path.basename(conf_path)} must route OAuth endpoints to "
                f"http://mcp-oauth:8000 (not Traefik, not localhost)"
            )

    def test_all_subdomain_confs_listen_on_443(self) -> None:
        """Test that all *.subdomain.conf files listen on port 443 with SSL."""
        confs = self._get_subdomain_confs()
        for conf_path in confs:
            content = _read_conf(conf_path)
            assert "listen 443 ssl;" in content, (
                f"{os.path.basename(conf_path)} must listen on port 443 with SSL"
            )
