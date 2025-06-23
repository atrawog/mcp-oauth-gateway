#!/usr/bin/env python3
"""Demo script showing the simplicity of the new mcp-http-stdio configuration.

This demonstrates how the tool now only needs the MCP server URL,
and automatically discovers everything else.
"""

import os
import subprocess
import tempfile


def main():
    print("🚀 MCP HTTP-to-stdio Demo")
    print("=" * 40)

    # Get MCP server URL from user
    server_url = input("Enter your MCP server URL: ").strip()
    if not server_url:
        server_url = "https://mcp-fetch.example.com/mcp"
        print(f"Using default: {server_url}")

    # Create temporary .env file with just the server URL
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(f"MCP_SERVER_URL={server_url}\n")
        env_file = f.name

    print("\n📝 Created config file with just:")
    print(f"   MCP_SERVER_URL={server_url}")

    print("\n🔍 Testing OAuth discovery and command execution...")

    try:
        # Test authentication discovery
        print("\n1️⃣ Testing authentication...")
        result = subprocess.run([
            "mcp-http-stdio",
            "--test-auth",
            "--env-file", env_file,
            "--log-level", "INFO"
        ], check=False, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ OAuth configuration discovered successfully!")
            print("✅ Authentication test passed!")

            # Test token management
            print("\n2️⃣ Testing token management...")
            token_result = subprocess.run([
                "mcp-http-stdio",
                "--token",
                "--env-file", env_file,
                "--log-level", "INFO"
            ], check=False, capture_output=True, text=True, timeout=30)

            if token_result.returncode == 0:
                print("✅ Token management working!")
                print("✅ Token validation and refresh successful!")
            else:
                print("⚠️  Token management had issues:")
                print(token_result.stderr)

            # Test command execution
            print("\n3️⃣ Testing command execution...")
            cmd_result = subprocess.run([
                "mcp-http-stdio",
                "--command", "fetch https://httpbin.org/json",
                "--env-file", env_file,
                "--log-level", "INFO"
            ], check=False, capture_output=True, text=True, timeout=30)

            if cmd_result.returncode == 0:
                print("✅ Command execution successful!")
                print("✅ Fetch tool working correctly!")
            else:
                print("⚠️  Command execution had issues:")
                print(cmd_result.stderr)
        else:
            print("❌ Authentication test failed:")
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("⏱️  Test timed out (may require manual authorization)")
    except FileNotFoundError:
        print("❌ mcp-http-stdio not found. Please install first:")
        print("   pip install -e .")
    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Clean up
        os.unlink(env_file)

    print("\n🎉 That's it! The tool automatically:")
    print("   • Discovered OAuth endpoints from the server")
    print("   • Handled client registration")
    print("   • Managed all authentication flows")
    print("   • Executed MCP commands seamlessly")
    print("   • No manual configuration needed!")
    print("\n💡 Try these commands:")
    print("   mcp-http-stdio --token  # Check and refresh tokens")
    print("   mcp-http-stdio --command 'fetch https://example.com'")
    print("   mcp-http-stdio -c 'search my query'")
    print("   mcp-http-stdio -t  # Short form for token check")

if __name__ == "__main__":
    main()
