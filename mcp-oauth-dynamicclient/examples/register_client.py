"""
Example of registering a new OAuth client
"""

import asyncio
import json

import httpx


async def register_client():
    # Server URL
    base_url = "https://auth.your-domain.com"  # Replace with your domain

    # Client registration data
    registration_data = {
        "redirect_uris": ["https://your-app.com/callback", "http://localhost:8080/callback"],
        "client_name": "My Test Application",
        "client_uri": "https://your-app.com",
        "logo_uri": "https://your-app.com/logo.png",
        "scope": "openid profile email",
        "contacts": ["admin@your-app.com"],
        "tos_uri": "https://your-app.com/terms",
        "policy_uri": "https://your-app.com/privacy",
    }

    async with httpx.AsyncClient() as client:
        try:
            # Register the client
            response = await client.post(
                f"{base_url}/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 201:
                result = response.json()
                print("✅ Client registered successfully!")
                print(f"Client ID: {result['client_id']}")
                print(f"Client Secret: {result['client_secret']}")
                print("\nFull response:")
                print(json.dumps(result, indent=2))

                # Save credentials to file
                with open("oauth_credentials.json", "w") as f:
                    json.dump(result, f, indent=2)
                print("\n📝 Credentials saved to oauth_credentials.json")
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(register_client())
