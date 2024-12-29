import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.models.models as models
from app.database.database import engine
from app.views.sign_views import router as sing_router
from app.views.contract_views import router as contract_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",  # Common React dev server port
    "http://localhost:5173",  # Add this line for Vite
    "http://10.10.3.71",  # Add this line for your backend IP
]
# http://10.10.3.71:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(sing_router)
app.include_router(contract_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Backend!"}

# if __name__ == '__main__':
#     uvicorn.run("main:app", reload=True)

if __name__ == '__main__':

    # uvicorn.run("main:app", reload=True, host="0.0.0.0")
    uvicorn.run("main:app", reload=True)

