#!/usr/bin/env python3
"""Simple HTTP server to receive OAuth callbacks for token generation.

This runs on localhost to capture the authorization code.
"""

import asyncio

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route


class CallbackReceiver:
    def __init__(self, port: int = 8080):
        self.port = port
        self.auth_code = None
        self.state = None
        self.error = None
        self._server: uvicorn.Server | None = None

    async def callback_handler(self, request: Request) -> PlainTextResponse:
        """Handle OAuth callback."""
        query_params = dict(request.query_params)

        if "error" in query_params:
            self.error = query_params["error"]
            error_description = query_params.get("error_description", "")
            return PlainTextResponse(
                f"❌ OAuth Error: {self.error}\n{error_description}\n\nYou can close this window."
            )

        if "code" in query_params:
            self.auth_code = query_params["code"]
            self.state = query_params.get("state")
            return PlainTextResponse(
                f"✅ Authorization code received!\n\nCode: {self.auth_code}\n\nYou can close this window."
            )

        return PlainTextResponse("❌ No authorization code received\n\nYou can close this window.")

    async def start_server(self) -> None:
        """Start the callback receiver server."""
        app = Starlette(routes=[Route("/callback", self.callback_handler)])
        config = uvicorn.Config(app, host="localhost", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        asyncio.create_task(self._server.serve())
        print(f"🔗 Callback receiver started on http://localhost:{self.port}/callback")

    async def wait_for_callback(self, timeout: int = 300) -> str:
        """Wait for OAuth callback."""
        print("⏳ Waiting for OAuth callback...")

        for _ in range(timeout):
            if self.auth_code or self.error:
                break
            await asyncio.sleep(1)

        if self._server:
            self._server.should_exit = True

        if self.error:
            raise Exception(f"OAuth error: {self.error}")
        if not self.auth_code:
            raise Exception("Timeout waiting for OAuth callback")

        return self.auth_code


async def main():
    """Test the callback receiver."""
    receiver = CallbackReceiver()
    await receiver.start_server()

    try:
        print("Visit: http://localhost:8080/callback?code=test_code&state=test_state")
        auth_code = await receiver.wait_for_callback(30)
        print(f"Received code: {auth_code}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
