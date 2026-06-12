
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from .prompts import return_instructions_transaction

from google.adk.auth.auth_schemes import OpenIdConnectWithConfig
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools.openapi_tool.auth.auth_helpers import openid_url_to_scheme_credential
import dotenv
dotenv.load_dotenv()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# credential_dict = {
#     "client_id": GOOGLE_CLIENT_ID,
#     "client_secret": GOOGLE_CLIENT_SECRET,
# }
# auth_scheme, auth_credential = openid_url_to_scheme_credential(
#     openid_url="http://localhost:8080/.well-known/oauth-authorization-server",
#     credential_dict=credential_dict,
#     scopes=os.environ.get(
#     "REQUIRED_SCOPES",
#     "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
# ).split(),
# )

# Automatic OAuth discovery - just works!
# mcp_toolset = MCPToolset(
#     connection_params=StreamableHTTPConnectionParams(
#         url=os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp"),
#     ),
#     auth_scheme=OAuth2(
#         flows=OAuthFlows(
#             clientCredentials=OAuthFlowClientCredentials(
#                 tokenUrl="",  # Empty - automatically discovered
#                 scopes={"api:read": "Read access"}
#             )
#         )
#     ),
#     auth_credential=oauth2_credential,
#     # ✅ No auth_discovery needed - automatically enabled!
# )


auth_scheme = OpenIdConnectWithConfig(
    # The URL of the IDP's authorization endpoint where the user is redirected to log in.
    authorization_endpoint="http://localhost:8080/authorize",
    # The URL of the IDP's token endpoint where the authorization code is exchanged for tokens.
    token_endpoint="http://localhost:8080/token",
    # The scopes (permissions) your application requests from the IDP.
    # 'openid' is standard for OIDC. 'profile' and 'email' request user profile info.
    scopes= os.environ.get(
    "REQUIRED_SCOPES",
    "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
).split()
)

# # Define the Authentication Credentials for your specific application.
# # This object holds the client identifier and secret that your application uses
# # to identify itself to the IDP during the OAuth2 flow.
# # !! SECURITY WARNING: Avoid hardcoding secrets in production code. !!
# # !! Use environment variables or a secret management system instead. !!
auth_credential = AuthCredential(
  auth_type=AuthCredentialTypes.OPEN_ID_CONNECT,
  oauth2=OAuth2Auth(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
  )
)

transaction_agent = LlmAgent(
    model=os.getenv("TRANSACTION_AGENT_MODEL", "gemini-2.5-flash"),
    name="transaction_agent",
    instruction=return_instructions_transaction(),
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp")
            ),
            auth_scheme=auth_scheme,
            auth_credential=auth_credential,
            tool_filter=['make_transaction', 'credit_card_payment']
        )
    ],
)

# from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, Oauth2Credentials # Example types
# # ... other imports

# async def get_tools_with_oauth_async(mcp_url, access_token):
#     # Example: Manually passing an obtained access token
#     tools, exit_stack = await MCPToolset.from_server(
#         connection_params=SseServerParams(url=mcp_url),
#         auth_scheme="Bearer",
#         auth_credential=access_token # The token obtained from the OAuth flow
#     )
#     return tools, exit_stack

