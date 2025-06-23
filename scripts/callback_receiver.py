#!/usr/bin/env python3
"""Simple HTTP server to receive OAuth callbacks for token generation
This runs on localhost to capture the authorization code.
"""

import asyncio

from aiohttp import web
from aiohttp import web_runner


class CallbackReceiver:
    def __init__(self, port: int = 8080):
        self.port = port
        self.auth_code = None
        self.state = None
        self.error = None

    async def callback_handler(self, request):
        """Handle OAuth callback."""
        query_params = dict(request.query)

        if "error" in query_params:
            self.error = query_params["error"]
            error_description = query_params.get("error_description", "")
            return web.Response(
                text=f"❌ OAuth Error: {self.error}\n{error_description}\n\nYou can close this window.",
                content_type="text/plain",
            )

        if "code" in query_params:
            self.auth_code = query_params["code"]
            self.state = query_params.get("state")

            return web.Response(
                text=f"✅ Authorization code received!\n\nCode: {self.auth_code}\n\nYou can close this window.",
                content_type="text/plain",
            )

        return web.Response(
            text="❌ No authorization code received\n\nYou can close this window.",
            content_type="text/plain",
        )

    async def start_server(self):
        """Start the callback receiver server."""
        app = web.Application()
        app.router.add_get("/callback", self.callback_handler)

        runner = web_runner.AppRunner(app)
        await runner.setup()

        site = web_runner.TCPSite(runner, "localhost", self.port)
        await site.start()

        print(f"🔗 Callback receiver started on http://localhost:{self.port}/callback")
        return runner

    async def wait_for_callback(self, timeout=300):
        """Wait for OAuth callback."""
        print("⏳ Waiting for OAuth callback...")

        for _ in range(timeout):
            if self.auth_code or self.error:
                break
            await asyncio.sleep(1)

        if self.error:
            raise Exception(f"OAuth error: {self.error}")

        if not self.auth_code:
            raise Exception("Timeout waiting for OAuth callback")

        return self.auth_code


async def main():
    """Test the callback receiver."""
    receiver = CallbackReceiver()
    runner = await receiver.start_server()

    try:
        print("Visit: http://localhost:8080/callback?code=test_code&state=test_state")
        auth_code = await receiver.wait_for_callback(30)
        print(f"Received code: {auth_code}")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
