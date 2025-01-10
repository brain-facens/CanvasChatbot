from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from routes import chat

app = FastAPI(
    title="Canvas Chatbot",
    description="API para interação com o chatbot do Canvas LMS",
    version="1.0.0",
    contact={
        "name": "Eduardo Weber Maldaner",
        "email": "eduardo.maldaner@facens.br",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/swagger",
    redoc_url="/redoc"
)

app.include_router(router=chat.router)

@app.get("/health")
def health():
    return JSONResponse(content={"status": "OK"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True)