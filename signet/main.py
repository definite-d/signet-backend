from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from base64 import b64encode

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from .repo import FintechRepository
from .models import FintechGenerationRequest
from .crypt import get_private_key, sign

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


def signet_encode(data: bytes):
    encoded_data = b64encode(data)
    return encoded_data
    

def signet_encrypt(
    data: bytes, key_size: int = 2048, hash_algorithm: hashes.HashAlgorithm = hashes.SHA256()
) -> bytes:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    encrypted_data = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(algorithm=hash_algorithm),
            salt=b"",
        ),
    )
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hash_algorithm),
            algorithm=hash_algorithm,
            label=None,
        ),
    )
    return encrypted_data

@app.post("/fintech/transaction/new")
async def sign_new_transaction_with_signet(
    data: FintechGenerationRequest, repo: FintechRepository = Depends()
):
    # Identify the fintech we're dealing with
    fintech = await repo.get_fintech(data.api_key)
    if not fintech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fintech not found"
        )
    # TODO: Ensure the fintech has the right permissions

    encoded_data = signet_encode(data.model_dump())

    # Sign the filled-in template text
    signature = sign(get_private_key(), encoded_data).hex()

    encrypted = signet_encrypt(encoded_data + signature)

    # Generate barcode from payload
    code: bytes = generate_qr_code(str(payload), data.format)

    # Export the barcode (SVG or raster)
    return StreamingResponse(
        code,
        media_type=f"image/{data.format}{'+xml' if data.format == 'svg' else ''}",
    )


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
