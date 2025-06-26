from service import search_employee

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(search_employee(name="Dai"))
    print(result)
    print(type(result))