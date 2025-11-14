from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .settings import settings


# =========================
# Other Models
# =========================
class Seal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: Annotated[float, Field(alias="amount", gt=0.0)]
    timestamp: Annotated[datetime, Field(alias="timestamp")]
    transaction_reference: Annotated[str, Field(alias="transactionReference")]
    sender_account_number: Annotated[
        str,
        Field(alias="senderAccountNumber", min_length=10, max_length=10),
    ]
    sender_name: Annotated[str, Field(alias="senderName")]
    sender_bank_code: Annotated[str, Field(alias="senderBankCode", min_length=6)]
    receiver_account_number: Annotated[
        str,
        Field(alias="receiverAccountNumber", min_length=10, max_length=10),
    ]
    receiver_name: Annotated[str, Field(alias="receiverName")]
    receiver_bank_code: Annotated[str, Field(alias="receiverBankCode", min_length=6)]

    @field_validator("timestamp")
    @classmethod
    def check_timestamp_not_past(cls, ts: datetime) -> datetime:
        if ts and ts.astimezone(settings.TZ) < datetime.now(settings.TZ):
            raise ValueError("timestamp cannot be in the past")
        return ts


# =========================
# Request Models
# =========================
class FintechGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    api_key: Annotated[
        str,
        Field(
            ...,
            alias="apiKey",
            pattern=rf"sgnt-fak-[a-zA-Z0-9]{{{settings.API_KEY_LENGTH * 2}}}",
            title="API key",
        ),
    ]
    format: Annotated[Literal["svg", "png", "jpeg", "webp"], Field()]
    image_width: Annotated[int, Field(..., alias="imageWidth", gt=0)]
    transaction_data: Annotated["Seal", Field(alias="transactionData")]
    pdf417_columns: Annotated[int, Field(6, alias="pdf417Columns", gt=0)]


if __name__ == "__main__":
    # TODO: remove later; just for testing
    print(
        Seal(
            amount=3.23,
            timestamp=datetime(2025, 11, 14, 1, 19, 0),
            transaction_reference="1234",
            sender_account_number="1921689292",
            sender_bank_code="233434",
            sender_name="asdfasdf",
            receiver_name="asdfasdf",
            receiver_account_number="2839429892",
            receiver_bank_code="234234",
        ).model_dump_json(by_alias=True)
    )
