from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi_standalone_docs import StandaloneDocs

from .crypt import secure_pack
from .db import init_db
from .models import FintechGenerationRequest
from .qr import generate_qr_code
from .repo import FintechRepository


@asynccontextmanager
async def lifespan(_app: FastAPI):
    StandaloneDocs(_app)
    await init_db()
    yield


app = FastAPI(title="Signet API", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/fintech/transaction/new")
async def new_seal(data: FintechGenerationRequest, repo: FintechRepository = Depends()):
    # Identify the fintech we're dealing with
    fintech = await repo.get_fintech(data.api_key)
    if not fintech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fintech not found"
        )
    # TODO: Ensure the fintech has the right permissions

    # Securely craft the payload
    payload = secure_pack(data.model_dump())

    # Generate barcode from payload
    code: bytes = generate_qr_code(str(payload), data.format)

    # Export the barcode (SVG or raster)
    return StreamingResponse(
        code,
        media_type=f"image/{data.format}{'+xml' if data.format == 'svg' else ''}",
    )


origins = ["*"]

app.add_middleware(
    CORSMiddleware,  # ty: ignore
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
