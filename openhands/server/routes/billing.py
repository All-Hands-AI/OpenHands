import json
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
from openhands.server.shared import SettingsStoreImpl, config, file_store

# TODO: All this code needs to be moved to the deploy repo as it doesn't make sense in OSS.

LITE_LLM_API_URL = os.environ.get("LITE_LLM_API_URL", "https://llm-proxy.app.all-hands.dev")
LITE_LLM_API_KEY = os.environ.get("LITE_LLM_API_KEY", None)
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", None)
API_HOST = os.environ.get("API_DOMAIN", "http://localhost:3001")
# TODO: This needs to be taken from environment variables too. As we set these up in stripe)
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
        response = await client.get(f"{LITE_LLM_API_URL}/user/info?user_id={user_id}", headers={
            "x-goog-api-key": LITE_LLM_API_KEY,
        })
        response_json = response.json()
        # TODO: What if the user does not exist?
        user_info = response_json['user_info']
        max_budget = user_info['max_budget']
        spend = user_info['spend']
        credits = Decimal("{:.2f}".format(max_budget - spend))

    return GetCreditsResponse(credits=credits)


@app.post('/create-checkout-session')
async def create_checkout_session(body: CreateCheckoutSessionRequest, request: Request) -> CreateCheckoutSessionResponse:
    user_id = get_user_id(request)
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
    #TODO: Store the session id, price, and user before proceeding. (In case of unknown errors, we will need to be able to link these)
    # Ugly hack - when we move this over to deploy we'll use the actual values
    file_store.write("tims_ugly_hack.json", json.dumps({
        "checkout_session_id": checkout_session.id,
        "user_id": user_id
    }))
    return CreateCheckoutSessionResponse(
        redirect_url=checkout_session.url
    )


@app.get('/success')
async def success_callback(request: Request):
    # Hack - retrieve from storage when we move this to deploy project
    session_data = json.loads(file_store.read("tims_ugly_hack.json"))
    checkout_session_id = session_data['checkout_session_id']
    stripe_session = stripe.checkout.Session.retrieve(checkout_session_id)
    if stripe_session["status"] == "complete":
        async with httpx.AsyncClient() as client:
            user_id = get_user_id(request)
            response = await client.get(f"{LITE_LLM_API_URL}/user/info?user_id={user_id}", headers={
                "x-goog-api-key": LITE_LLM_API_KEY,
            })
            response.raise_for_status()
            response_json = response.json()
            # TODO: We are going to need to alter this calculation. Stripe is storing values in cents, which I think makes sense
            new_max_budget = response_json['user_info']['max_budget'] + stripe_session['amount_total'] / 100
            response = await client.post(f"{LITE_LLM_API_URL}/user/update", headers={
                "x-goog-api-key": LITE_LLM_API_KEY,
            }, json={
                "user_id": user_id,
                "max_budget": new_max_budget,
            })
            response.raise_for_status()
            # TODO: Store transaction status     

    # TODO: This should redirect back into the app with a message indicating that payment was successful
    return RedirectResponse(API_HOST) 


@app.get('/cancel')
async def cancel_callback(session_id: str):
    # TODO: This should redirect back into the app with a message indicating that payment was cancelled
    return RedirectResponse(API_HOST)
