from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/consumer/uuv/trajectory")
async def uuv_trajectory(request: Request):
    json = await request.json()
    print("The consumer received JSON data: ")
    print(json)
    return JSONResponse({"message": "Placeholder"}, 200)