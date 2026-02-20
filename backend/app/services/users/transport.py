from fastapi import Response, status
from fastapi.responses import JSONResponse
from fastapi_users.authentication.transport.bearer import BearerResponse, BearerTransport
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
class BearerRefreshResponse(BearerResponse):
    refresh_token: str


class RefreshAuthenticationBackend(AuthenticationBackend):
    def __init__(self, name, transport, get_strategy, get_refresh_strategy):
        super().__init__(name=name, transport=transport, get_strategy=get_strategy)
        self.get_refresh_strategy = get_refresh_strategy

    async def login(self, strategy, user):
        access_token = await strategy.write_token(user)
        refresh_strategy = self.get_refresh_strategy()
        refresh_token = await refresh_strategy.write_token(user)
        return await self.transport.get_login_response(access_token, refresh_token)

class BearerWithRefreshTransport(BearerTransport):
    
    def __init__(self, tokenUrl: str):
        super().__init__(tokenUrl=tokenUrl)
        
    async def get_login_response(self, token: str, refresh_token: str) -> Response:
        bearer_response = BearerRefreshResponse(
            access_token=token, 
            refresh_token=refresh_token, 
            token_type="bearer"
        )
        return JSONResponse(bearer_response.model_dump())  # ← fix here
    
    @staticmethod
    def get_openapi_login_responses_success() -> OpenAPIResponseType:
        return {
            status.HTTP_200_OK: {
                "model": BearerRefreshResponse,
                "content": {
                    "application/json": {
                        "example": {
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1"
                            "c2VyX2lkIjoiOTIyMWZmYzktNjQwZi00MzcyLTg2Z"
                            "DMtY2U2NDJjYmE1NjAzIiwiYXVkIjoiZmFzdGFwaS"
                            "11c2VyczphdXRoIiwiZXhwIjoxNTcxNTA0MTkzfQ."
                            "M10bjOe45I5Ncu_uXvOmVV8QxnL-nZfcH96U90JaocI",
                            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1"
                            "c2VyX2lkIjoiOTIyMWZmYzktNjQwZi00MzcyLTg2Z"
                            "DMtY2U2NDJjYmE1NjAzIiwiYXVkIjoiZmFzdGFwaS"
                            "11c2VyczphdXRoIiwiZXhwIjoxNTcxNTA0MTkzfQ."
                            "M10bjOe45I5Ncu_uXvOmVV8QxnL-nZfcH96U90JaocI",
                            "token_type": "bearer"
                        }
                    }
                },
            },
        }