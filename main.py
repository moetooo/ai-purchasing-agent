import uvicorn
from app.api.routes import router
from app.db.seed import seed_database
from fastapi import FastAPI

app = FastAPI(title="AI Purchasing Agent API")
app.include_router(router)

@app.on_event("startup")
def startup_event():
    seed_database()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
