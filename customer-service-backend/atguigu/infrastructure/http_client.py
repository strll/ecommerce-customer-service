import asyncio
from httpx import AsyncClient

http_client: AsyncClient | None = None

def init_http_client():
    global http_client
    http_client = AsyncClient(timeout=10.0)

async def close_http_client():
    global http_client
    if http_client:
        await http_client.aclose()

async def main():
    init_http_client()

    try:
        response = await http_client.get(url="http://192.168.200.148:18081/users/u1001/orders")
        # 必须加括号调用方法
        print(response.json())
    finally:
        # 养成好习惯，执行完毕后释放资源
        await close_http_client()

if __name__ == "__main__":
    asyncio.run(main())