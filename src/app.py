from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from routes import chat

app = FastAPI()

app.include_router(router=chat.router)

@app.get("/health")
def health():
    return JSONResponse(content={"status": "OK"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True)