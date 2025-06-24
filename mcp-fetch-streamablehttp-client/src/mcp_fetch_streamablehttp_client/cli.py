"""Command-line interface for MCP fetch client."""

import asyncio
import json
import logging
import os
from typing import Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.logging import RichHandler
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .client import MCPFetchClient
from .exceptions import MCPError

console = Console()


def setup_logging(verbose: bool):
    """Set up logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """MCP Fetch Client - Pure Python client for MCP fetch servers."""
    setup_logging(verbose)


@cli.command()
@click.option(
    "--server-url",
    default="http://localhost:3000",
    envvar="MCP_SERVER_URL",
    help="MCP server URL",
)
@click.option(
    "--token",
    envvar="MCP_ACCESS_TOKEN",
    help="Bearer token for authentication",
)
async def info(server_url: str, token: Optional[str]):
    """Get server information and capabilities."""
    async with MCPFetchClient(server_url, access_token=token) as client:
        try:
            result = await client.initialize()
            
            # Display server info
            console.print("\n[bold]Server Information[/bold]")
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Key", style="cyan")
            info_table.add_column("Value")
            
            server_info = result.get("serverInfo", {})
            info_table.add_row("Name", server_info.get("name", "Unknown"))
            info_table.add_row("Version", server_info.get("version", "Unknown"))
            info_table.add_row("Protocol Version", result.get("protocolVersion", "Unknown"))
            
            console.print(info_table)
            
            # Display capabilities
            console.print("\n[bold]Capabilities[/bold]")
            capabilities = result.get("capabilities", {})
            if capabilities:
                console.print(JSON(json.dumps(capabilities, indent=2)))
            else:
                console.print("[dim]No capabilities reported[/dim]")
                
        except MCPError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()


@cli.command()
@click.argument("url")
@click.option(
    "--server-url",
    default="http://localhost:3000",
    envvar="MCP_SERVER_URL",
    help="MCP server URL",
)
@click.option(
    "--token",
    envvar="MCP_ACCESS_TOKEN",
    help="Bearer token for authentication",
)
@click.option(
    "-m", "--method",
    default="GET",
    help="HTTP method to use",
)
@click.option(
    "-H", "--header",
    multiple=True,
    help="HTTP header to include (format: 'Name: Value')",
)
@click.option(
    "-d", "--data",
    help="Request body data",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output raw JSON response",
)
async def fetch(
    url: str,
    server_url: str,
    token: Optional[str],
    method: str,
    header: tuple,
    data: Optional[str],
    json_output: bool,
):
    """Fetch a URL using the MCP server."""
    # Parse headers
    headers = {}
    for h in header:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()
    
    async with MCPFetchClient(server_url, access_token=token) as client:
        try:
            await client.initialize()
            result = await client.fetch(
                url=url,
                method=method,
                headers=headers if headers else None,
                body=data,
            )
            
            if json_output:
                console.print_json(result.model_dump_json())
                return
            
            # Display response info
            console.print(f"\n[bold]Response from {url}[/bold]")
            console.print(f"Status: {result.status}")
            console.print(f"MIME Type: {result.mimeType or 'Unknown'}")
            
            # Display headers if any
            if result.headers:
                console.print("\n[bold]Headers:[/bold]")
                for key, value in result.headers.items():
                    console.print(f"  {key}: {value}")
            
            # Display content
            if result.text:
                console.print("\n[bold]Content:[/bold]")
                
                # Use syntax highlighting for known types
                if result.mimeType and "json" in result.mimeType:
                    try:
                        parsed = json.loads(result.text)
                        console.print(JSON(json.dumps(parsed, indent=2)))
                    except json.JSONDecodeError:
                        console.print(result.text)
                elif result.mimeType and ("html" in result.mimeType or "xml" in result.mimeType):
                    syntax = Syntax(result.text, "html", theme="monokai", line_numbers=True)
                    console.print(syntax)
                else:
                    console.print(Panel(result.text, title="Response Body"))
            elif result.blob:
                console.print(f"\n[bold]Binary content:[/bold] {len(result.blob)} bytes (base64 encoded)")
                
        except MCPError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()


@cli.command()
@click.option(
    "--server-url",
    default="http://localhost:3000",
    envvar="MCP_SERVER_URL",
    help="MCP server URL",
)
@click.option(
    "--token",
    envvar="MCP_ACCESS_TOKEN",
    help="Bearer token for authentication",
)
async def tools(server_url: str, token: Optional[str]):
    """List available tools on the server."""
    async with MCPFetchClient(server_url, access_token=token) as client:
        try:
            await client.initialize()
            tools = await client.list_tools()
            
            if not tools:
                console.print("[dim]No tools available[/dim]")
                return
            
            console.print(f"\n[bold]Available Tools ({len(tools)})[/bold]\n")
            
            for tool in tools:
                console.print(f"[cyan]{tool.get('name', 'Unknown')}[/cyan]")
                if desc := tool.get("description"):
                    console.print(f"  {desc}")
                if params := tool.get("inputSchema"):
                    console.print("  [dim]Parameters:[/dim]")
                    console.print(JSON(json.dumps(params, indent=2)))
                console.print()
                
        except MCPError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()


@cli.command()
@click.argument("tool_name")
@click.option(
    "--server-url",
    default="http://localhost:3000",
    envvar="MCP_SERVER_URL",
    help="MCP server URL",
)
@click.option(
    "--token",
    envvar="MCP_ACCESS_TOKEN",
    help="Bearer token for authentication",
)
@click.option(
    "-a", "--arg",
    multiple=True,
    help="Tool argument in format 'key=value'",
)
@click.option(
    "--json-args",
    help="Tool arguments as JSON string",
)
async def call(
    tool_name: str,
    server_url: str,
    token: Optional[str],
    arg: tuple,
    json_args: Optional[str],
):
    """Call a tool on the server."""
    # Parse arguments
    arguments = {}
    
    if json_args:
        try:
            arguments = json.loads(json_args)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON arguments: {e}[/red]")
            raise click.Abort()
    else:
        for a in arg:
            if "=" in a:
                key, value = a.split("=", 1)
                # Try to parse as JSON first, otherwise use as string
                try:
                    arguments[key] = json.loads(value)
                except json.JSONDecodeError:
                    arguments[key] = value
    
    async with MCPFetchClient(server_url, access_token=token) as client:
        try:
            await client.initialize()
            result = await client.call_tool(tool_name, arguments)
            
            console.print(f"\n[bold]Tool Result: {tool_name}[/bold]")
            if isinstance(result, dict):
                console.print(JSON(json.dumps(result, indent=2)))
            else:
                console.print(result)
                
        except MCPError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()


def main():
    """Main entry point for the CLI."""
    # Handle async commands with click
    def async_command(f):
        def wrapper(*args, **kwargs):
            return asyncio.run(f(*args, **kwargs))
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        return wrapper
    
    # Patch async commands
    for name, cmd in cli.commands.items():
        if asyncio.iscoroutinefunction(cmd.callback):
            cmd.callback = async_command(cmd.callback)
    
    cli()


if __name__ == "__main__":
    main()