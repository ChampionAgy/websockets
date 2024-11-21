from starlette.websockets import WebSocketDisconnect
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import websockets
from fastapi import FastAPI, WebSocket
import asyncio
import threading
import uvicorn
import json

connected_clients = set()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins or specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods or specify allowed methods
    allow_headers=["*"],  # Allow all headers or specify allowed headers
)

class_name = ""
temperature = 0.0
pH = 0.0
water_level = 0
healthy = 0
unhealthy = 0

all_values = {"class_name": class_name,
	      "healthy": healthy, 
	      "unhealthy": unhealthy, 
	      "water_level": water_level, 
	      "ph":pH, 
	      "temperature":temperature}



@app.post("/update_class")
async def update_class(request: Request):
    global class_name
    data = await request.json()
   
    all_data = data.get('result')  # main request containing all the data
    
    healthy = all_data.get('healthy')
    unhealthy = all_data.get('unhealthy')
    water_level = all_data.get('water_level')
    pH = all_data.get('ph')
    temperature = all_data.get('temperature')
    class_name = all_data.get('class_name')

    all_values.update({"class_name": class_name,
                       "healthy": healthy,
                       "unhealthy": unhealthy,
                       "water_level": water_level,
                       "ph": pH,
                       "temperature": temperature})
    return "update received"


@app.get("/")
def root():
    return "Server is running"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Just to keep the connection alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        await websocket.close()

@app.websocket("/ws/values")
async def classes_server(websocket: WebSocket):
    global class_name, all_values
    # Add the new client to the set of connected clients
    connected_clients.add(websocket)
    try:
        # Continuously send updates to the client
        while True:
            # Increment the counter
            # counter += 1
            # Send the counter value to all connected clients
            if connected_clients:  # Check if there are any connected clients
                if all_values is not None:
                    data = json.dumps(all_values)
                    #message = class_name
                    # await asyncio.wait([client.send(message) for client in connected_clients])
                    await asyncio.gather(
                        *[asyncio.create_task(client.send(data)) for client in connected_clients]
                    )
            # Wait for a second before sending the next update
            await asyncio.sleep(1)
    except websockets.ConnectionClosed:
        # Remove the client if the connection is closed
        connected_clients.remove(websocket)



# Start the FastAPI server
def start_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=2234)

# Start the WebSocket server
async def start_websocket_server():
    async with websockets.serve(classes_server, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

async def main():
    # Run both servers
    loop = asyncio.get_event_loop()
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.start()
    await start_websocket_server()

# Run the main function in the existing event loop
if __name__ == "__main__":
    asyncio.run(main())


# # The main function to start the WebSocket server
# async def main():
#     server = await websockets.serve(classes_server, "0.0.0.0", 8765)
#     await server.wait_closed()
#     print('running server')
    
   
# def start_server():
#     uvicorn.run(app, host="0.0.0.0", port=2234)

# threading.Thread(target=start_server).start()

# asyncio.run(main())
