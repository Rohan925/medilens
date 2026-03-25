from services.medicine_service import get_medicine_data


async def search_medicine(name: str):
    return await get_medicine_data(name)
