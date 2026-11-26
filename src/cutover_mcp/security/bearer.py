"""Bearer-token gate for the HTTP transports.

With this set as the server's ``auth``, FastMCP answers any ``/mcp`` request that has no
``Authorization: Bearer <token>`` header with a 401 and ``WWW-Authenticate: Bearer`` before a
session exists. Custom routes such as ``/health`` stay open, and stdio has no HTTP layer.
"""

from __future__ import annotations

from fastmcp.server.auth import AccessToken, TokenVerifier

_CLIENT_ID = "cutover-api-token"


class RequireBearerToken(TokenVerifier):
    """Accepts any non-blank bearer token.

    The token is the caller's Cutover API token. Only the Cutover API can say whether it is
    valid, and which API that is depends on the Core-Url of each call, so it is checked there.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token.strip():
            return None
        return AccessToken(token=token, client_id=_CLIENT_ID, scopes=[])
