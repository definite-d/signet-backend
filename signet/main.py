from datetime import datetime

from jinja2 import Template
from fastapi import Depends, FastAPI, UploadFile, HTTPException, status
from pydantic import BaseModel

from .repo import FintechRepository
from .crypt import sign

app = FastAPI()


class FintechOnboardingRequest(BaseModel):
    name: str
    email: str
    file: UploadFile


class FintechGenerationRequest(BaseModel):
    api_key: str
    sender_account: int
    sender_bank: str
    receiver_account: int
    receiver_bank: str
    receiver_name: str
    amount: int
    time: datetime
    transaction_reference: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/fintech/onboarding")
async def fintech_onboarding(data: FintechOnboardingRequest):
    # Take the data and create a new fintech entry in the DB
    # Take the receipt and run it through an OCR model to get the text. Then through an ML model to turn that into the template.
    return {"name": data.name, "email": data.email, "file": data.file}


@app.post("/fintech/generation")
async def get_fintech_generation(
    data: FintechGenerationRequest, repo: FintechRepository = Depends()
):
    # Identify the fintech we're dealing with
    fintech = await repo.get_fintech(data.api_key)
    if not fintech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fintech not found"
        )
    # TODO: Ensure the fintech has the right permissions

    # Get the template
    template_text = fintech.template
    template = Template(template_text)

    # Populate the template with the data
    expected_ocr_text = template.render(
        sender_account=data.sender_account,
        sender_bank=data.sender_bank,
        receiver_account=data.receiver_account,
        receiver_bank=data.receiver_bank,
        receiver_name=data.receiver_name,
        amount=data.amount,
        time=data.time,
        transaction_reference=data.transaction_reference,
    ).encode()

    # Sign the filled in template text
    private_key = b""
    signature = sign(private_key, expected_ocr_text)

    # Identify the key indices for the fintech.

    # Add the key indices to the end of the signature payload

    # Generate the barcode from the payload.

    # Export the barcode as SVG or PNG, with the logomark
    return data


@app.get("/fintech/generation/transaction")
async def get_fintech_transaction(file: UploadFile):
    return {"file": file}
