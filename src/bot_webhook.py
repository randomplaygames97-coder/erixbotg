from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post('/webhook')
async def webhook(request: Request):
    json_payload = await request.json()
    # Process your webhook payload here
    print(json_payload)
    return JSONResponse(content={'status': 'success'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)