"""
Model Context Protocol (MCP) framework for GitHub Graph Explorer
"""
import json
import asyncio
from enum import Enum
from typing import Any, Dict, Callable, Awaitable, Optional, List, Union

class ResponseStatus(str, Enum):
    """Response status codes for MCP server responses"""
    OK = "ok"
    BAD_REQUEST = "bad_request"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    NOT_FOUND = "not_found"

class Request:
    """
    Represents a request sent to the MCP server.
    """
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a request object.
        
        Args:
            data: The request data as a dictionary
        """
        self.data = data
        
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get a parameter from the request.
        
        Args:
            name: The name of the parameter
            default: The default value if the parameter doesn't exist
            
        Returns:
            The parameter value or the default
        """
        return self.data.get(name, default)
        
class Response:
    """
    Represents a response from the MCP server.
    """
    def __init__(self, status: ResponseStatus, body: Dict[str, Any]):
        """
        Initialize a response object.
        
        Args:
            status: The response status
            body: The response body as a dictionary
        """
        self.status = status
        self.body = body
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary.
        
        Returns:
            A dictionary representation of the response
        """
        return {
            "status": self.status.value,
            "body": self.body
        }
        
    def to_json(self) -> str:
        """
        Convert the response to a JSON string.
        
        Returns:
            A JSON string representation of the response
        """
        return json.dumps(self.to_dict())

class Server:
    """
    Base MCP server class.
    """
    def __init__(self):
        """
        Initialize an MCP server.
        """
        self.handlers = {}
        
    def register_handler(self, command: str, 
                         handler: Callable[[Request], Awaitable[Response]]) -> None:
        """
        Register a handler for a command.
        
        Args:
            command: The command name
            handler: The handler function
        """
        self.handlers[command] = handler
        
    async def handle_request(self, data: Dict[str, Any]) -> Response:
        """
        Handle a request.
        
        Args:
            data: The request data as a dictionary
            
        Returns:
            A response object
        """
        try:
            command = data.get("command")
            
            if not command:
                return Response(
                    status=ResponseStatus.BAD_REQUEST,
                    body={"error": "Missing command parameter"}
                )
                
            if command not in self.handlers:
                return Response(
                    status=ResponseStatus.NOT_FOUND,
                    body={"error": f"Command '{command}' not found"}
                )
                
            handler = self.handlers[command]
            request = Request(data)
            return await handler(request)
            
        except Exception as e:
            return Response(
                status=ResponseStatus.INTERNAL_SERVER_ERROR,
                body={"error": f"Error handling request: {str(e)}"}
            )
            
    async def serve(self, host: str = "localhost", port: int = 8080) -> None:
        """
        Start the MCP server.
        
        Args:
            host: The host to listen on
            port: The port to listen on
        """
        async def handle_client(reader, writer):
            """Handle a client connection"""
            addr = writer.get_extra_info('peername')
            print(f"Client connected: {addr}")
            
            while True:
                try:
                    # Read data
                    data = await reader.readline()
                    if not data:
                        break
                        
                    # Parse request
                    request_data = json.loads(data.decode())
                    
                    # Handle request
                    response = await self.handle_request(request_data)
                    
                    # Send response
                    writer.write(response.to_json().encode() + b'\n')
                    await writer.drain()
                    
                except json.JSONDecodeError:
                    response = Response(
                        status=ResponseStatus.BAD_REQUEST,
                        body={"error": "Invalid JSON"}
                    ).to_json().encode() + b'\n'
                    writer.write(response)
                    await writer.drain()
                    break
                    
                except ConnectionError:
                    break
                    
                except Exception as e:
                    response = Response(
                        status=ResponseStatus.INTERNAL_SERVER_ERROR,
                        body={"error": f"Server error: {str(e)}"}
                    ).to_json().encode() + b'\n'
                    writer.write(response)
                    await writer.drain()
                    break
            
            # Close the connection
            writer.close()
            await writer.wait_closed()
            print(f"Client disconnected: {addr}")
            
        # Start the server
        server = await asyncio.start_server(
            handle_client,
            host,
            port
        )
        
        async with server:
            print(f"Server started on {host}:{port}")
            await server.serve_forever()


class Client:
    """
    MCP client for connecting to an MCP server.
    """
    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        Initialize an MCP client.
        
        Args:
            host: The host to connect to
            port: The port to connect to
        """
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        
    async def connect(self) -> None:
        """Connect to the MCP server"""
        self.reader, self.writer = await asyncio.open_connection(
            self.host, 
            self.port
        )
        
    async def disconnect(self) -> None:
        """Disconnect from the MCP server"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            
    async def send_request(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a request to the MCP server.
        
        Args:
            command: The command to send
            params: The parameters to send
            
        Returns:
            The response as a dictionary
        """
        if not self.writer:
            await self.connect()
            
        # Create request data
        request_data = {"command": command}
        if params:
            request_data.update(params)
            
        # Send request
        request_json = json.dumps(request_data).encode() + b'\n'
        self.writer.write(request_json)
        await self.writer.drain()
        
        # Read response
        response_data = await self.reader.readline()
        if not response_data:
            raise ConnectionError("Connection closed by server")
            
        # Parse response
        response = json.loads(response_data.decode())
        return response