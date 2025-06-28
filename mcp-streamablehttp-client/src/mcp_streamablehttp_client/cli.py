"""Command-line interface for MCP Streamable HTTP-to-stdio client."""

import asyncio
import json
import logging
import sys
from datetime import UTC
from pathlib import Path
from uuid import uuid4

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from .config import Settings
from .oauth import OAuthClient
from .proxy import StreamableHttpToStdioProxy


console = Console()


def setup_logging(level: str) -> None:
    """Configure logging with rich output."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=[RichHandler(console=console, show_time=True, show_path=False, rich_tracebacks=True)],
    )


@click.command()
@click.option(
    "--env-file",
    type=click.Path(exists=False, path_type=Path),
    default=".env",
    help="Path to .env file with configuration",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level",
)
@click.option("--server-url", help="Override MCP server URL from .env")
@click.option("--reset-auth", is_flag=True, help="Clear stored credentials and re-authenticate")
@click.option("--test-auth", is_flag=True, help="Test authentication and exit")
@click.option(
    "-t",
    "--token",
    is_flag=True,
    help="Check OAuth token status, refresh if expired/expiring, and test with server",
)
@click.option(
    "-c",
    "--command",
    help=(
        "Execute a specific MCP tool and exit. Examples: 'fetch https://example.com', "
        "'search query text', 'read_file path=/tmp/file.txt'"
    ),
)
@click.option(
    "--get-client-info",
    is_flag=True,
    help="Get current client registration information (RFC 7592)",
)
@click.option(
    "--update-client",
    help="Update client registration (RFC 7592). Format: field=value,field2=value2",
)
@click.option(
    "--delete-client",
    is_flag=True,
    help="Delete client registration (RFC 7592). This is PERMANENT!",
)
@click.option(
    "--raw",
    help=('Send raw JSON-RPC request to MCP server. Example: --raw \'{"method": "tools/list", "params": {}}\''),
)
@click.option("--list-tools", is_flag=True, help="List all available MCP tools")
@click.option("--list-resources", is_flag=True, help="List all available MCP resources")
@click.option("--list-prompts", is_flag=True, help="List all available MCP prompts")
def main(
    env_file: Path,
    log_level: str,
    server_url: str,
    reset_auth: bool,
    test_auth: bool,
    token: bool,
    command: str,
    get_client_info: bool,
    update_client: str,
    delete_client: bool,
    raw: str,
    list_tools: bool,
    list_resources: bool,
    list_prompts: bool,
) -> None:
    """MCP Streamable HTTP-to-stdio client with OAuth support.

    This tool proxies MCP requests from stdio to an HTTP server,
    handling OAuth authentication automatically.

    On first run, it will guide you through the OAuth setup process.
    Credentials are stored securely for automatic authentication in future runs.

    Use --command/-c to execute a single MCP tool call and exit,
    or run without arguments for continuous stdio proxy mode.
    """
    # Load environment variables
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try to find .env in parent directories
        current = Path.cwd()
        while current != current.parent:
            candidate = current / ".env"
            if candidate.exists():
                load_dotenv(candidate)
                break
            current = current.parent

    # Setup logging
    setup_logging(log_level)
    logging.getLogger(__name__)

    try:
        # Load settings
        settings = Settings()

        # Override server URL if provided
        if server_url:
            settings.mcp_server_url = server_url

        # Clear credentials if requested
        if reset_auth:
            console.print("[yellow]Clearing stored credentials...[/yellow]")
            # Clear from environment/settings only - no credential files per CLAUDE.md!
            settings.oauth_access_token = None
            settings.oauth_refresh_token = None
            settings.oauth_client_id = None
            settings.oauth_client_secret = None
            console.print("[green]✓[/green] Credentials cleared")
            console.print("[dim]Note: To fully reset, clear MCP_CLIENT_* variables from .env[/dim]")

        # Run async main
        asyncio.run(
            async_main(
                settings,
                test_auth,
                token,
                command,
                get_client_info,
                update_client,
                delete_client,
                raw,
                list_tools,
                list_resources,
                list_prompts,
            ),
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


async def async_main(
    settings: Settings,
    test_auth: bool,
    token: bool,
    command: str,
    get_client_info: bool,
    update_client: str,
    delete_client: bool,
    raw: str,
    list_tools: bool,
    list_resources: bool,
    list_prompts: bool,
) -> None:
    """Async main function."""
    logger = logging.getLogger(__name__)

    # Handle RFC 7592 client management commands
    if get_client_info or update_client or delete_client:
        await handle_client_management(settings, get_client_info, update_client, delete_client)
        return

    # Check and refresh tokens if requested
    if token:
        await check_and_refresh_tokens(settings)
        return

    # Handle raw protocol requests
    if raw:
        await execute_raw_protocol(settings, raw)
        return

    # Handle listing commands
    if list_tools:
        await execute_list_command(settings, "tools/list")
        return

    if list_resources:
        await execute_list_command(settings, "resources/list")
        return

    if list_prompts:
        await execute_list_command(settings, "prompts/list")
        return

    # Execute command if requested
    if command:
        await execute_mcp_command(settings, command)
        return

    # Test authentication if requested
    if test_auth:
        console.print("\n[cyan]Testing OAuth authentication...[/cyan]")
        async with OAuthClient(settings) as oauth:
            try:
                token = await oauth.ensure_authenticated()
                console.print("[green]✓[/green] Authentication successful!")
                console.print(f"[dim]Access token: {token[:20]}...[/dim]")

                # Test connection to MCP server
                async with StreamableHttpToStdioProxy(settings) as proxy:
                    console.print("\n[cyan]Testing MCP server connection...[/cyan]")
                    test_request = {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "mcp-streamablehttp-client-test",
                                "version": "0.1.0",
                            },
                        },
                        "id": "test-1",
                    }

                    response = await proxy._handle_request(test_request)

                    if "error" in response:
                        console.print(f"[red]✗[/red] Server error: {response['error']}")
                    else:
                        console.print("[green]✓[/green] Server connection successful!")
                        if "result" in response:
                            server_info = response["result"].get("serverInfo", {})
                            console.print(
                                f"[dim]Server: {server_info.get('name', 'Unknown')} "
                                f"v{server_info.get('version', 'Unknown')}[/dim]",
                            )

            except Exception as e:
                console.print(f"[red]✗[/red] Authentication failed: {e}")
                sys.exit(1)
        return

    # Normal proxy operation
    logger.info("Starting MCP Streamable HTTP-to-stdio client")
    logger.info(f"Server URL: {settings.mcp_server_url}")

    try:
        async with StreamableHttpToStdioProxy(settings) as proxy:
            # Log successful start to stderr so it doesn't interfere with stdio
            sys.stderr.write("MCP Streamable HTTP-to-stdio client ready\n")
            sys.stderr.flush()

            # Run the proxy
            await proxy.run()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise


async def check_and_refresh_tokens(settings: Settings) -> None:
    """Check OAuth token status and refresh if needed."""
    from datetime import datetime

    console.print("\n[cyan]OAuth Token Status Check[/cyan]")
    console.print("=" * 40)

    # NO CREDENTIAL FILES! Everything comes from .env!

    # Check if OAuth endpoints are discovered
    if not settings.oauth_token_url:
        console.print("[yellow]⚠️  OAuth endpoints not discovered yet[/yellow]")
        console.print("\n[cyan]Discovering OAuth configuration...[/cyan]")

        async with OAuthClient(settings) as oauth:
            try:
                await oauth.discover_oauth_configuration()
                console.print("[green]✓[/green] OAuth endpoints discovered")
            except Exception as e:
                console.print(f"[red]✗[/red] Discovery failed: {e}")
                sys.exit(1)
    else:
        console.print("[green]✓[/green] OAuth endpoints configured")
        console.print(f"[dim]  Authorization: {settings.oauth_authorization_url}[/dim]")
        console.print(f"[dim]  Token: {settings.oauth_token_url}[/dim]")
        if settings.oauth_device_auth_url:
            console.print(f"[dim]  Device: {settings.oauth_device_auth_url}[/dim]")
        if settings.oauth_registration_url:
            console.print(f"[dim]  Registration: {settings.oauth_registration_url}[/dim]")

    # Check client registration
    console.print("\n[cyan]Client Registration:[/cyan]")
    if settings.oauth_client_id:
        console.print(f"[green]✓[/green] Client registered: {settings.oauth_client_id}")
        if settings.oauth_client_secret:
            console.print(f"[dim]  Secret: {settings.oauth_client_secret[:8]}...[/dim]")

        # Check RFC 7592 management credentials
        if settings.registration_access_token:
            console.print("[green]✓[/green] RFC 7592 management enabled")
            console.print(f"[dim]  Management token: {settings.registration_access_token[:20]}...[/dim]")
            if settings.registration_client_uri:
                console.print(f"[dim]  Management URI: {settings.registration_client_uri}[/dim]")
        else:
            console.print("[yellow]⚠️  No RFC 7592 management credentials[/yellow]")
            console.print("[dim]  Client registered before RFC 7592 support[/dim]")
    else:
        console.print("[yellow]⚠️  No client credentials found[/yellow]")

    # Check access token
    console.print("\n[cyan]Access Token:[/cyan]")
    if settings.oauth_access_token:
        token_preview = (
            settings.oauth_access_token[:20] + "..."
            if len(settings.oauth_access_token) > 20
            else settings.oauth_access_token
        )
        console.print(f"[green]✓[/green] Token exists: {token_preview}")

        # Check expiration
        if settings.oauth_token_expires_at:
            now = datetime.now(UTC)
            expires_at = settings.oauth_token_expires_at
            time_left = expires_at - now

            if time_left.total_seconds() > 0:
                if time_left.total_seconds() < 300:  # Less than 5 minutes
                    console.print(f"[yellow]⚠️  Expires soon: {expires_at.isoformat()}Z[/yellow]")
                    console.print(f"[dim]  Time left: {int(time_left.total_seconds())} seconds[/dim]")
                else:
                    hours_left = time_left.total_seconds() / 3600
                    console.print(f"[green]✓[/green] Valid until: {expires_at.isoformat()}Z")
                    console.print(f"[dim]  Time left: {hours_left:.1f} hours[/dim]")
            else:
                console.print(f"[red]✗[/red] Token expired: {expires_at.isoformat()}Z")
                console.print(f"[dim]  Expired {abs(int(time_left.total_seconds()))} seconds ago[/dim]")
        else:
            console.print("[yellow]⚠️  No expiration info (assuming valid)[/yellow]")
    else:
        console.print("[red]✗[/red] No access token found")

    # Check refresh token
    console.print("\n[cyan]Refresh Token:[/cyan]")
    if settings.oauth_refresh_token:
        refresh_preview = (
            settings.oauth_refresh_token[:20] + "..."
            if len(settings.oauth_refresh_token) > 20
            else settings.oauth_refresh_token
        )
        console.print(f"[green]✓[/green] Refresh token available: {refresh_preview}")
    else:
        console.print("[yellow]⚠️  No refresh token available[/yellow]")

    # Determine if we need to refresh or re-authenticate
    needs_refresh = False
    needs_auth = False

    if not settings.oauth_access_token:
        needs_auth = True
    elif settings.oauth_token_expires_at:
        time_until_expiry = settings.oauth_token_expires_at - datetime.now(UTC)
        if time_until_expiry.total_seconds() <= 0:
            if settings.oauth_refresh_token:
                needs_refresh = True
            else:
                needs_auth = True
        elif time_until_expiry.total_seconds() < 300:  # Less than 5 minutes
            needs_refresh = True

    # Perform refresh or authentication if needed
    if needs_refresh:
        console.print("\n[cyan]Refreshing access token...[/cyan]")
        async with OAuthClient(settings) as oauth:
            try:
                await oauth.refresh_token()
                console.print("[green]✓[/green] Token refreshed successfully!")

                # Show new token info
                new_token_preview = settings.oauth_access_token[:20] + "..."
                console.print(f"[dim]  New token: {new_token_preview}[/dim]")

                if settings.oauth_token_expires_at:
                    console.print(f"[dim]  New expiry: {settings.oauth_token_expires_at.isoformat()}Z[/dim]")

            except Exception as e:
                console.print(f"[red]✗[/red] Token refresh failed: {e}")
                console.print("[yellow]⚠️  You may need to re-authenticate with --reset-auth[/yellow]")
                sys.exit(1)

    elif needs_auth:
        console.print("\n[yellow]Authentication required[/yellow]")
        if not settings.oauth_client_id:
            console.print("[cyan]Registering OAuth client...[/cyan]")

        async with OAuthClient(settings) as oauth:
            try:
                await oauth.ensure_authenticated()
                console.print("[green]✓[/green] Authentication completed successfully!")
            except Exception as e:
                console.print(f"[red]✗[/red] Authentication failed: {e}")
                sys.exit(1)
    else:
        console.print("\n[green]✓[/green] All tokens are valid and current!")

    # Final status summary
    console.print("\n[cyan]Summary:[/cyan]")
    console.print("[green]✓[/green] OAuth endpoints: discovered")
    console.print("[green]✓[/green] Client registration: complete")
    console.print("[green]✓[/green] Access token: valid")
    if settings.oauth_refresh_token:
        console.print("[green]✓[/green] Refresh token: available")

    # Test token with actual server
    console.print("\n[cyan]Testing token with server...[/cyan]")
    try:
        async with StreamableHttpToStdioProxy(settings) as proxy:
            test_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-streamablehttp-client-token-test",
                        "version": "0.1.0",
                    },
                },
                "id": "token-test",
            }

            response = await proxy._handle_request(test_request)

            if "error" in response:
                console.print(f"[red]✗[/red] Server rejected token: {response['error']}")
                sys.exit(1)
            else:
                console.print("[green]✓[/green] Token accepted by server!")
                server_info = response.get("result", {}).get("serverInfo", {})
                if server_info:
                    console.print(
                        f"[dim]  Server: {server_info.get('name', 'Unknown')} "
                        f"v{server_info.get('version', 'Unknown')}[/dim]",
                    )

    except Exception as e:
        console.print(f"[red]✗[/red] Server test failed: {e}")
        sys.exit(1)

    console.print("\n[green]🎉 All token checks passed![/green]")

    # Save credentials to .env file
    from pathlib import Path

    env_file = Path(".env")

    def save_env_var(key: str, value: str):
        """Save or update an environment variable in .env file."""
        lines = []
        found = False

        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        lines.append(f"{key}={value}\n")
                        found = True
                    else:
                        lines.append(line)

        if not found:
            lines.append(f"\n{key}={value}\n")

        with open(env_file, "w") as f:
            f.writelines(lines)

    # Save to .env
    console.print("\n[cyan]💾 Saving credentials to .env...[/cyan]")
    save_env_var("MCP_CLIENT_ACCESS_TOKEN", settings.oauth_access_token)
    console.print("   ✅ Saved MCP_CLIENT_ACCESS_TOKEN")

    if settings.oauth_refresh_token and settings.oauth_refresh_token != "None":  # noqa: S105
        save_env_var("MCP_CLIENT_REFRESH_TOKEN", settings.oauth_refresh_token)
        console.print("   ✅ Saved MCP_CLIENT_REFRESH_TOKEN")

    if settings.oauth_client_id:
        save_env_var("MCP_CLIENT_ID", settings.oauth_client_id)
        console.print("   ✅ Saved MCP_CLIENT_ID")

    if settings.oauth_client_secret:
        save_env_var("MCP_CLIENT_SECRET", settings.oauth_client_secret)
        console.print("   ✅ Saved MCP_CLIENT_SECRET")

    if settings.registration_access_token:
        save_env_var("MCP_CLIENT_REGISTRATION_TOKEN", settings.registration_access_token)
        console.print("   ✅ Saved MCP_CLIENT_REGISTRATION_TOKEN")

    if settings.registration_client_uri:
        save_env_var("MCP_CLIENT_REGISTRATION_URI", settings.registration_client_uri)
        console.print("   ✅ Saved MCP_CLIENT_REGISTRATION_URI")

    # Print MCP client environment variables in a format that can be captured
    # Only output credentials, not endpoints (which are auto-discovered)
    print("\n# MCP Client Environment Variables")
    print(f"export MCP_CLIENT_ACCESS_TOKEN={settings.oauth_access_token}")
    if settings.oauth_refresh_token and settings.oauth_refresh_token != "None":  # noqa: S105
        print(f"export MCP_CLIENT_REFRESH_TOKEN={settings.oauth_refresh_token}")
    if settings.oauth_client_id:
        print(f"export MCP_CLIENT_ID={settings.oauth_client_id}")
    if settings.oauth_client_secret:
        print(f"export MCP_CLIENT_SECRET={settings.oauth_client_secret}")
    if settings.registration_access_token:
        print(f"export MCP_CLIENT_REGISTRATION_TOKEN={settings.registration_access_token}")
    if settings.registration_client_uri:
        print(f"export MCP_CLIENT_REGISTRATION_URI={settings.registration_client_uri}")

    # Print success message
    console.print("\n[green]✅ MCP client credentials saved to .env![/green]")


async def execute_mcp_command(settings: Settings, command: str) -> None:
    """Execute a specific MCP command via the proxy."""
    console.print(f"\n[cyan]Executing MCP command: {command}[/cyan]")

    # Parse command - expect format like "fetch https://example.com"
    parts = command.strip().split(maxsplit=1)
    if len(parts) < 1:
        console.print("[red]Error:[/red] Invalid command format")
        console.print("[dim]Examples:[/dim]")
        console.print("[dim]  --command 'fetch https://example.com'[/dim]")
        console.print("[dim]  --command 'search my query text'[/dim]")
        console.print("[dim]  --command 'read_file /path/to/file'[/dim]")
        console.print('[dim]  --command \'mytool {"param1": "value", "param2": 123}\'[/dim]')
        console.print("[dim]  --command 'anytool key1=value1 key2=123'[/dim]")
        sys.exit(1)

    tool_name = parts[0]

    try:
        async with StreamableHttpToStdioProxy(settings) as proxy:
            console.print("\n[cyan]1. Connecting to server...[/cyan]")

            # Step 1: Initialize
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-streamablehttp-client-test",
                        "version": "0.1.0",
                    },
                },
                "id": "init-1",
            }

            init_response = await proxy._handle_request(init_request)

            if "error" in init_response:
                console.print(f"[red]✗[/red] Initialization failed: {init_response['error']}")
                sys.exit(1)

            console.print("[green]✓[/green] Server initialized successfully")

            # Step 2: List available tools
            console.print("\n[cyan]2. Listing available tools...[/cyan]")

            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "list-1",
            }

            tools_response = await proxy._handle_request(tools_request)

            if "error" in tools_response:
                console.print(f"[red]✗[/red] Tools listing failed: {tools_response['error']}")
                sys.exit(1)

            available_tools = tools_response.get("result", {}).get("tools", [])
            tool_names = [tool["name"] for tool in available_tools]

            tools_list = ", ".join(tool_names)
            console.print(f"[green]✓[/green] Found {len(available_tools)} tools: {tools_list}")

            # Check if requested tool exists
            if tool_name not in tool_names:
                console.print(f"[red]✗[/red] Tool '{tool_name}' not available")
                console.print(f"[dim]Available tools: {', '.join(tool_names)}[/dim]")
                sys.exit(1)

            # Step 3: Execute the command
            console.print(f"\n[cyan]3. Calling tool '{tool_name}'...[/cyan]")

            # Parse arguments based on tool type
            tool_args = parse_tool_arguments(tool_name, parts[1] if len(parts) > 1 else "")

            call_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": tool_args},
                "id": "call-1",
            }

            console.print(f"[dim]Request: {call_request}[/dim]")

            call_response = await proxy._handle_request(call_request)

            if "error" in call_response:
                console.print(f"[red]✗[/red] Tool execution failed: {call_response['error']}")
                sys.exit(1)

            result = call_response.get("result", {})
            content = result.get("content", [])

            console.print("[green]✓[/green] Tool call completed successfully!")

            # Display results
            console.print("\n[cyan]4. Results:[/cyan]")

            if isinstance(content, list):
                for i, item in enumerate(content, 1):
                    if isinstance(item, dict):
                        item_type = item.get("type", "unknown")
                        if item_type == "text":
                            text = item.get("text", "")
                            # Truncate long responses
                            if len(text) > 500:
                                text = text[:500] + "...\n[truncated]"
                            console.print(f"[dim]Response {i} (text):[/dim]")
                            console.print(text)
                        elif item_type == "resource":
                            console.print(f"[dim]Response {i} (resource):[/dim]")
                            console.print(f"URI: {item.get('resource', {}).get('uri', 'N/A')}")
                            if "text" in item:
                                text = item["text"][:500] + ("..." if len(item["text"]) > 500 else "")
                                console.print(text)
                        else:
                            console.print(f"[dim]Response {i} ({item_type}):[/dim]")
                            console.print(str(item))
                    else:
                        console.print(f"[dim]Response {i}:[/dim]")
                        console.print(str(item))
            else:
                console.print(str(content))

            console.print("\n[green]🎉 Command executed successfully![/green]")

    except Exception as e:
        console.print(f"[red]✗[/red] Command execution failed: {e}")
        if "--log-level DEBUG" not in sys.argv:
            console.print("[dim]Run with --log-level DEBUG for more details[/dim]")
        sys.exit(1)


def parse_tool_arguments(tool_name: str, arg_string: str) -> dict:
    """Parse tool arguments in a generic, flexible way."""
    args = {}

    if not arg_string:
        # Provide reasonable defaults based on tool name
        if tool_name == "fetch":
            args["url"] = "https://httpbin.org/json"
        elif "search" in tool_name.lower():
            args["query"] = "test query"
        elif "read" in tool_name.lower():
            args["path"] = "/tmp/test.txt"  # noqa: S108
        elif "write" in tool_name.lower():
            args["path"] = "/tmp/test.txt"  # noqa: S108
            args["content"] = "test content"
        return args

    arg_string = arg_string.strip()

    # Try JSON parsing first (most flexible)
    if arg_string.startswith("{") and arg_string.endswith("}"):
        try:
            import json

            return json.loads(arg_string)
        except json.JSONDecodeError:
            pass

    # Try key=value parsing
    if "=" in arg_string:
        parts = arg_string.split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                # Try to parse value as JSON if it looks like JSON
                if value.startswith(("[", "{", '"')) or value in (
                    "true",
                    "false",
                    "null",
                ):
                    try:
                        import json

                        args[key] = json.loads(value)
                    except json.JSONDecodeError:
                        args[key] = value
                # Try to convert to appropriate type
                elif value.isdigit():
                    args[key] = int(value)
                elif value.replace(".", "", 1).isdigit():
                    args[key] = float(value)
                else:
                    args[key] = value
        return args

    # Smart parsing based on tool name patterns
    if tool_name == "echo":
        # For echo tool, the argument is called "message"
        args["message"] = arg_string

    elif tool_name == "fetch" or "fetch" in tool_name.lower():
        # For fetch tools, first argument is usually URL
        args["url"] = arg_string

    elif "search" in tool_name.lower():
        # For search tools, treat as query
        args["query"] = arg_string

    elif "read" in tool_name.lower() and "file" in tool_name.lower():
        # For file reading tools
        args["path"] = arg_string

    elif "write" in tool_name.lower() and "file" in tool_name.lower():
        # For file writing tools, try to split path and content
        parts = arg_string.split(maxsplit=1)
        args["path"] = parts[0]
        if len(parts) > 1:
            args["content"] = parts[1]
        else:
            args["content"] = "test content"

    # Generic fallback - try common parameter names
    elif arg_string.startswith(("http://", "https://")):
        args["url"] = arg_string
    elif arg_string.startswith("/"):
        args["path"] = arg_string
    elif len(arg_string.split()) > 3:  # Looks like a sentence
        args["query"] = arg_string
    else:
        # Use the most generic parameter names
        args["input"] = arg_string

    return args


async def handle_client_management(
    settings: Settings,
    get_client_info: bool,
    update_client: str,
    delete_client: bool,
) -> None:
    """Handle RFC 7592 client registration management commands."""
    console.print("\n[cyan]Client Registration Management (RFC 7592)[/cyan]")
    console.print("=" * 45)

    # Create OAuth client
    async with OAuthClient(settings) as oauth:
        # Ensure we have registration credentials
        if not settings.registration_access_token or not settings.registration_client_uri:
            console.print("[red]Error:[/red] No RFC 7592 management credentials found.")
            console.print("[dim]Client must be registered with RFC 7592 support.[/dim]")

            # Check if we have client_id but missing management creds
            if settings.oauth_client_id:
                console.print("\n[yellow]Client is registered but missing management credentials.[/yellow]")
                console.print("[dim]This can happen if the client was registered before RFC 7592 support.[/dim]")
                console.print("[dim]Consider re-registering with --reset-auth to get management capabilities.[/dim]")
            sys.exit(1)

        try:
            if get_client_info:
                # Get current client configuration
                console.print("\n[cyan]Fetching client registration...[/cyan]")
                config = await oauth.get_client_configuration()

                console.print("\n[green]✓[/green] Client configuration retrieved!")
                console.print("\n[bold]Client Registration Details:[/bold]")

                # Display key fields
                console.print(f"  Client ID: {config.get('client_id', 'N/A')}")
                console.print(f"  Client Name: {config.get('client_name', 'N/A')}")
                console.print(f"  Scope: {config.get('scope', 'N/A')}")

                if "redirect_uris" in config:
                    console.print(f"  Redirect URIs: {', '.join(config['redirect_uris'])}")

                if "grant_types" in config:
                    console.print(f"  Grant Types: {', '.join(config['grant_types'])}")

                if "client_id_issued_at" in config:
                    issued_at = config["client_id_issued_at"]
                    from datetime import datetime

                    dt = datetime.fromtimestamp(issued_at, tz=UTC)
                    console.print(f"  Issued At: {dt.isoformat()}Z")

                if "client_secret_expires_at" in config:
                    expires_at = config["client_secret_expires_at"]
                    if expires_at == 0:
                        console.print("  Expires: Never (eternal client)")
                    else:
                        dt = datetime.fromtimestamp(expires_at, tz=UTC)
                        console.print(f"  Expires: {dt.isoformat()}Z")

                # Show raw JSON for debugging
                console.print("\n[dim]Full configuration (JSON):[/dim]")
                import json

                console.print(json.dumps(config, indent=2))

            elif update_client:
                # Parse update string
                console.print(f"\n[cyan]Parsing update request: {update_client}[/cyan]")

                updates = {}
                for pair in update_client.split(","):
                    if "=" not in pair:
                        console.print(f"[red]Error:[/red] Invalid format: {pair}")
                        console.print("[dim]Expected format: field=value,field2=value2[/dim]")
                        sys.exit(1)

                    key, value = pair.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Handle array fields
                    if key in [
                        "redirect_uris",
                        "grant_types",
                        "response_types",
                        "contacts",
                    ]:
                        # Split by semicolon for arrays
                        if ";" in value:
                            updates[key] = [v.strip() for v in value.split(";")]
                        else:
                            updates[key] = [value]
                    else:
                        updates[key] = value

                console.print("\n[cyan]Updates to apply:[/cyan]")
                for k, v in updates.items():
                    console.print(f"  {k}: {v}")

                # Confirm before updating
                console.print("\n[yellow]This will update your client registration.[/yellow]")
                console.print("Continue? [y/N]: ", end="")
                if input().strip().lower() != "y":
                    console.print("[dim]Update cancelled.[/dim]")
                    return

                # Perform update
                console.print("\n[cyan]Updating client registration...[/cyan]")
                updated = await oauth.update_client_configuration(updates)

                console.print("[green]✓[/green] Client registration updated!")

                # Show what changed
                console.print("\n[bold]Updated fields:[/bold]")
                for key in updates:
                    if key in updated:
                        console.print(f"  {key}: {updated[key]}")

                # Save new client_secret if it changed
                if "client_secret" in updated and updated["client_secret"] != settings.oauth_client_secret:
                    console.print("\n[yellow]⚠️  Client secret was rotated by server![/yellow]")
                    console.print("[dim]Updating .env file with new secret...[/dim]")

                    from pathlib import Path

                    env_file = Path(".env")

                    def save_env_var(key: str, value: str):
                        """Save or update an environment variable in .env file."""
                        lines = []
                        found = False

                        if env_file.exists():
                            with open(env_file) as f:
                                for line in f:
                                    if line.strip().startswith(f"{key}="):
                                        lines.append(f"{key}={value}\n")
                                        found = True
                                    else:
                                        lines.append(line)

                        if not found:
                            lines.append(f"\n{key}={value}\n")

                        with open(env_file, "w") as f:
                            f.writelines(lines)

                    save_env_var("MCP_CLIENT_SECRET", updated["client_secret"])
                    console.print("[green]✓[/green] New client secret saved to .env")

            elif delete_client:
                # Confirm deletion
                console.print("\n[red]⚠️  WARNING: This will PERMANENTLY delete your client registration![/red]")
                console.print("[dim]You will need to re-register to use this service again.[/dim]")
                console.print("\nClient to delete:")
                console.print(f"  Client ID: {settings.oauth_client_id}")
                console.print(f"  Client Name: {settings.client_name}")

                console.print(
                    "\n[red]Are you SURE you want to delete this client? Type 'DELETE' to confirm:[/red] ",
                    end="",
                )
                confirmation = input().strip()

                if confirmation != "DELETE":
                    console.print("[dim]Deletion cancelled.[/dim]")
                    return

                # Perform deletion
                console.print("\n[cyan]Deleting client registration...[/cyan]")
                await oauth.delete_client_registration()

                console.print("\n[green]✓[/green] Client registration deleted successfully!")
                console.print("[dim]All credentials have been cleared from memory.[/dim]")
                console.print("[dim]You may want to remove MCP_CLIENT_* variables from .env[/dim]")

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
            sys.exit(1)


async def execute_raw_protocol(settings: Settings, raw_request: str) -> None:
    """Execute a raw JSON-RPC protocol request."""
    import json

    console.print("\n[cyan]Executing raw protocol request[/cyan]")

    try:
        # Parse the raw request
        request = json.loads(raw_request)

        # Add required fields if missing
        if "jsonrpc" not in request:
            request["jsonrpc"] = "2.0"
        if "id" not in request and request.get("method") not in ["notifications/initialized"]:
            request["id"] = str(uuid4())

        async with StreamableHttpToStdioProxy(settings) as proxy:
            # Initialize first if needed
            if request.get("method") != "initialize":
                console.print("[dim]Initializing connection...[/dim]")
                init_request = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "mcp-streamablehttp-client-raw",
                            "version": "0.1.0",
                        },
                    },
                    "id": "init-raw",
                }
                init_response = await proxy._handle_request(init_request)
                if "error" in init_response:
                    console.print(f"[red]Initialization failed:[/red] {init_response['error']}")
                    sys.exit(1)

            # Execute the raw request
            console.print(f"[dim]Request: {json.dumps(request, indent=2)}[/dim]")
            response = await proxy._handle_request(request)

            # Output the response as JSON
            print(json.dumps(response, indent=2))

    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


async def execute_list_command(settings: Settings, method: str) -> None:
    """Execute a list command (tools/list, resources/list, prompts/list)."""
    console.print(f"\n[cyan]Listing {method.split('/')[0]}...[/cyan]")

    try:
        async with StreamableHttpToStdioProxy(settings) as proxy:
            # Initialize first
            console.print("[dim]Initializing connection...[/dim]")
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-streamablehttp-client-list",
                        "version": "0.1.0",
                    },
                },
                "id": "init-list",
            }

            init_response = await proxy._handle_request(init_request)
            if "error" in init_response:
                console.print(f"[red]Initialization failed:[/red] {init_response['error']}")
                sys.exit(1)

            # Execute the list request
            list_request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": {},
                "id": "list-1",
            }

            response = await proxy._handle_request(list_request)

            if "error" in response:
                console.print(f"[red]Error:[/red] {response['error']}")
                sys.exit(1)

            # Format and display the results
            result = response.get("result", {})
            items_key = method.split("/")[0]  # "tools", "resources", or "prompts"
            items = result.get(items_key, [])

            console.print(f"\n[green]Found {len(items)} {items_key}:[/green]")

            for item in items:
                if isinstance(item, dict):
                    name = item.get("name", "Unknown")
                    description = item.get("description", "")
                    console.print(f"\n[bold]{name}[/bold]")
                    if description:
                        console.print(f"  [dim]{description}[/dim]")

                    # Show additional details based on type
                    if items_key == "tools" and "inputSchema" in item:
                        schema = item["inputSchema"]
                        if "properties" in schema:
                            console.print("  [dim]Parameters:[/dim]")
                            for param, details in schema["properties"].items():
                                param_type = details.get("type", "any")
                                required = param in schema.get("required", [])
                                req_marker = " [red]*[/red]" if required else ""
                                console.print(f"    - {param} ({param_type}){req_marker}")

                    elif items_key == "resources" and "uri" in item:
                        console.print(f"  [dim]URI: {item['uri']}[/dim]")

                    elif items_key == "prompts" and "arguments" in item:
                        args = item["arguments"]
                        if args:
                            console.print("  [dim]Arguments:[/dim]")
                            for arg in args:
                                arg_name = arg.get("name", "Unknown")
                                arg_desc = arg.get("description", "")
                                required = arg.get("required", False)
                                req_marker = " [red]*[/red]" if required else ""
                                console.print(f"    - {arg_name}{req_marker}: {arg_desc}")
                else:
                    console.print(f"  - {item}")

            # Also output as JSON for programmatic use
            print("\n" + json.dumps(response, indent=2))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
