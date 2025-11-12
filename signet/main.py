from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from pydantic import BaseModel

from .crypt import get_private_key, sign
from .qr import generate_qr_code
from .render import render_with_positions
from .repo import FintechRepository


@asynccontextmanager
async def lifespan(_app: FastAPI):
    StandaloneDocs(_app)
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


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
    amount: Annotated[float, Field(..., gt=0)]
    time: datetime
    transaction_reference: str
    format: Literal["svg", "png", "jpg", "webp"]


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

    # Render and record variable positions
    rendered_text, positions = render_with_positions(
        fintech.template,
        sender_account=data.sender_account,
        sender_bank=data.sender_bank,
        receiver_account=data.receiver_account,
        receiver_bank=data.receiver_bank,
        receiver_name=data.receiver_name,
        amount=data.amount,
        time=data.time,
        transaction_reference=data.transaction_reference,
    )

    expected_ocr_text = rendered_text.encode()

    # Sign the filled-in template text
    signature = sign(get_private_key(), expected_ocr_text)

    # Identify key indices for the fintech
    key_indices = {
        "receiver_bank": positions.get("receiver_bank"),
        "receiver_account": positions.get("receiver_account"),
    }

    # Append indices to signature payload
    payload = {
        "signature": signature,
        "indices": key_indices,
    }

    # Generate barcode from payload
    code = generate_qr_code(payload, format)

    # Export the barcode (SVG or PNG) with the logomark
    return code


@app.get("/fintech/generation/transaction")
async def get_fintech_transaction(file: UploadFile):
    return {"file": file}
