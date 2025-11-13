from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import FintechGenerationRequest

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/fintech/transaction/new")
async def sign_new_transaction_with_signet(data: FintechGenerationRequest):
    signature


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
