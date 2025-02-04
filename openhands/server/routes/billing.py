from decimal import Decimal
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import get_user_id
from openhands.server.services.github_service import GitHubService
from openhands.server.settings import GETSettingsModel, POSTSettingsModel, Settings
from openhands.server.shared import SettingsStoreImpl, config

app = APIRouter(prefix='/api/billing')

# TODO: All this code needs to be moved to the deploy repo as it doesn't make sense in OSS.

class GetCreditsResponse(BaseModel):
    credits: Decimal = Decimal("0")


class CreateCheckoutSessionRequest(BaseModel):
    amount: int


class CreateCheckoutSessionResponse(BaseModel):
    redirect_url: str


class GetSessionStatusResponse(BaseModel):
    status: str
    customer_email: str


@app.get('/credits')
async def get_credits() -> GetCreditsResponse:
    return GetCreditsResponse(credits=Decimal("123.65"))


@app.post('/create-checkout-session')
async def create_checkout_session(body: CreateCheckoutSessionRequest) -> CreateCheckoutSessionResponse:
    print(f"TODO: Extract price from body: {body}")
    return CreateCheckoutSessionRequest(
        # TODO: We should redirect into stripe here with this URL as a callback
        redirect_url="http://localhost:3001/api/billing/callback?success=true&session_id=mock-session-id"
    )


@app.get('/session-status')
async def get_session_status(session_id: str) -> GetSessionStatusResponse:
    return GetSessionStatusResponse(status="OK", customer_email="foo@bar.com")


@app.get('/callback')
async def callback(request: Request):
    # TODO: This should redirect back into the app.
    # It could present a problem in dev mode as we need to determine which url / port is required
    return RedirectResponse("https://localhost:3001") 
