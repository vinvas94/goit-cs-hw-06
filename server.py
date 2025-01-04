import asyncio
from aiohttp import web
import os
import json
import datetime
import websockets

# Define routes for handling different HTTP requests
async def handle_index(request):
    return web.FileResponse('index.html')

async def handle_message(request):
    return web.FileResponse('message.html')

async def handle_static(request):
    filename = request.match_info['filename']
    return web.FileResponse(os.path.join('static', filename))

async def handle_logo(request):
    return web.FileResponse('logo.png')

async def handle_style(request):
    return web.FileResponse('style.css')

async def handle_history(request):
    return web.FileResponse('history.html')

# Route for handling sending messages
async def handle_send_message(request):
    data = await request.post()
    message_data = {
        'date': datetime.datetime.now().isoformat(),
        'username': data['username'],
        'message': data['message']
    }
    await send_to_socket_server(message_data)
    return web.Response(text="Message sent successfully!")

# Function to send data to the WebSocket server
async def send_to_socket_server(message_data):
    uri = "ws://websocket_server:5000"  
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(message_data))
    except Exception as e:
        print(f"Error sending message to WebSocket server: {e}")

# Route for retrieving messages
async def handle_get_messages(request):
    try:
        with open('storage/data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []
    return web.json_response(data)

# Route for handling 404 errors
async def handle_404_error(request):
    return web.FileResponse('error.html', status=404)

# Create the application and define routes
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/message', handle_message)
app.router.add_get('/static/{filename}', handle_static)
app.router.add_get('/logo.png', handle_logo)
app.router.add_get('/get_messages', handle_get_messages)
app.router.add_get('/history', handle_history)
app.router.add_post('/send_message', handle_send_message)
app.router.add_get('/{tail:.*}', handle_404_error)

# Run the application
if __name__ == '__main__':
    web.run_app(app, port=3000)
