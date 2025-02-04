import os

from decimal import Decimal

import httpx
import stripe

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import get_user_id
from openhands.server.services.github_service import GitHubService
from openhands.server.settings import GETSettingsModel, POSTSettingsModel, Settings
from openhands.server.shared import SettingsStoreImpl, config

# TODO: All this code needs to be moved to the deploy repo as it doesn't make sense in OSS.

LITE_LLM_API_URL = os.environ.get("LITE_LLM_API_URL", "https://llm-proxy.app.all-hands.dev")
LITE_LLM_API_KEY = os.environ.get("LITE_LLM_API_KEY", None)
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", None)
API_HOST = os.environ.get("API_DOMAIN", "http://localhost:3001")
# TODO: This needs to be taken from environment variables too.
PRICES = {
    #k.split("STRIPE_PRICE_")[1]: v
    #for k, v in os.environ.items()
    #if k.startswith("STRIPE_PRICE_")
    "25": "price_1Qk3elK5Ces1YVhflhgIflrx",
    "50": "price_1Qk2qwK5Ces1YVhfSbLbgNYg",
    "100": "price_1Qk2mZK5Ces1YVhfu8XNJuxU",
}

stripe.api_key = STRIPE_API_KEY
app = APIRouter(prefix='/api/billing')


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
async def get_credits(request: Request) -> GetCreditsResponse:
    user_id = get_user_id(request)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LITE_LLM_API_URL}/user/new?user_id={user_id}", headers={
            "x-goog-api-key": LITE_LLM_API_KEY,
        })
        response_json = response.json()
        # TODO: What if the user does not exist?
        max_budget = response_json['max_budget']
        spend = response_json['spend']
        credits = Decimal("{:.2f}".format(max_budget - spend))

    return GetCreditsResponse(credits=credits)


@app.post('/create-checkout-session')
async def create_checkout_session(body: CreateCheckoutSessionRequest) -> CreateCheckoutSessionResponse:
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                'price': PRICES[str(body.amount)],
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=API_HOST + '/api/billing/success',
        cancel_url=API_HOST + '/api/billing/cancel',
    )
    return CreateCheckoutSessionResponse(
        redirect_url=checkout_session.url
    )


@app.get('/success')
async def success_callback(request: Request):
    # TODO: Check the status of the session - I assume we get some sort of nonce code as a URL parameter
    # TODO: This should redirect back into the app with a message indicating that payment was successful
    return RedirectResponse(API_HOST) 


@app.get('/cancel')
async def cancel_callback(request: Request):
    # TODO: This should redirect back into the app with a message indicating that payment was cancelled
    return RedirectResponse(API_HOST)
