from sqlalchemy import delete, select, update
from sqlalchemy.exc import NoResultFound
from secrets import token_hex

from .db import Fintech, get_session
from .settings import settings


class FintechRepository:
    @staticmethod
    def _create_api_key():
        return f"sgnt_{token_hex(settings.API_KEY_LENGTH)}"

    async def get_fintech(self, api_key: str) -> Fintech | None:
        async with get_session() as session:
            result = await session.execute(
                select(Fintech).where(Fintech.api_key == api_key)
            )
            return result.scalar_one_or_none()

    async def create_fintech(self, data: dict) -> Fintech:
        async with get_session() as session:
            fintech = Fintech(**data)
            session.add(fintech)
            await session.commit()
            await session.refresh(fintech)
            return fintech

    async def update_fintech(self, api_key: str, data: dict) -> Fintech | None:
        async with get_session() as session:
            result = await session.execute(
                select(Fintech).where(Fintech.api_key == api_key)
            )
            fintech = result.scalar_one_or_none()
            if not fintech:
                return None
            for key, value in data.items():
                setattr(fintech, key, value)
            await session.commit()
            await session.refresh(fintech)
            return fintech

    async def delete_fintech(self, api_key: str) -> bool:
        async with get_session() as session:
            result = await session.execute(
                select(Fintech).where(Fintech.api_key == api_key)
            )
            fintech = result.scalar_one_or_none()
            if not fintech:
                return False
            await session.delete(fintech)
            await session.commit()
            return True


if __name__ == "__main__":
    print(FintechRepository._create_api_key())
