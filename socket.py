import asyncio
import json
import websockets
from motor.motor_asyncio import AsyncIOMotorClient
import os

class WebSocketServer:
    """
    This class represents a WebSocket server that handles connections,
    broadcasts messages, and interacts with a MongoDB database for storage.
    """

    def __init__(self, uri):
        """
        Initializes the server with the connection URI and sets up essential attributes.
        """
        self.uri = uri
        self.clients = set()  # Set to store connected clients

        # Connect to MongoDB
        self.client = AsyncIOMotorClient('mongodb://mongodb:27017')
        self.db = self.client.messages_db  # Access the "messages_db" database

        self.data_file_path = 'storage/data.json'  # Path to the data storage file
        self.init_data_file()  # Initialize the data file if it doesn't exist

    def init_data_file(self):
        """
        Checks if the data file exists and creates a new one with an empty list if not.
        """
        if not os.path.exists(self.data_file_path):
            with open(self.data_file_path, 'w') as file:
                json.dump([], file)  # Write an empty list to the file

    async def ws_handler(self, ws):
        """
        Handles a new WebSocket connection, adds it to the client set,
        calls the distribute method for message handling, and removes it on disconnect.
        """
        self.clients.add(ws)
        try:
            await self.distribute(ws)
        finally:
            if ws in self.clients:
                self.clients.remove(ws)

    async def distribute(self, ws):
        """
        Listens for incoming messages from a connected client.
        - Parses the message data.
        - Saves the message to the MongoDB database.
        - Saves a copy (without the "_id" field) to the data file.
        - Broadcasts the message to all connected clients.
        """
        async for message in ws:
            message_data = json.loads(message)

            # Save message to MongoDB
            await self.db.messages.insert_one(message_data)

            # Save message data (excluding "_id") to JSON file
            self.save_to_json_file(message_data)

            # Broadcast message to all connected clients
            await self.broadcast(message_data)

    def save_to_json_file(self, message_data):
        """
        Creates a copy of the message data without the "_id" field (MongoDB generated)
        and saves it to the data file in JSON format.
        """
        data_to_save = {k: v for k, v in message_data.items() if k != '_id'}
        with open(self.data_file_path, 'r+') as file:
            data = json.load(file)
            if isinstance(data, list):
                data.append(data_to_save)
            else:
                data = [data_to_save]
            file.seek(0)
            json.dump(data, file, indent=4)  # Save with indentation for readability

    async def broadcast(self, message_data):
        """
        Sends the message data to all currently connected clients in a safe manner.
        - Creates a copy of the client set to avoid modification issues.
        - Attempts to send the message to each client.
        - Removes disconnected clients from the set.
        """
        clients_copy = set(self.clients)
        for client in clients_copy:
            try:
                await client.send(json.dumps(message_data))
            except Exception as e:
                print(f"Failed to send message to a client: {e}")
                self.clients.remove(client)

    async def main(self):
        """
        Starts the WebSocket server by serving connections at the specified URI and port.
        """
        async with websockets.serve(self.ws_handler, "0.0.0.0", 5000):
            await asyncio.Future()  # This future never completes, keeping the server running

if __name__ == "__main__":
    server = WebSocketServer('ws://localhost:5000')
