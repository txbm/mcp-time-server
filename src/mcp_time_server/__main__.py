import asyncio
from argparse import ArgumentParser
from .server import TimeServer
from .api import TimeServerAPI


def main() -> None:
    """Main entry point for the MCP Time Server."""
    parser = ArgumentParser(description='MCP Time Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host address to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    parser.add_argument('--timezone', default='UTC', help='Default timezone')
    
    args = parser.parse_args()
    
    # Initialize the time server with the specified timezone
    time_server = TimeServer(default_timezone=args.timezone)
    
    # Create the API server
    api_server = TimeServerAPI(time_server)
    
    try:
        print(f"Starting MCP Time Server with default timezone: {args.timezone}")
        print(f"Available endpoints:")
        print(f"  GET /           - Get current time in default timezone")
        print(f"  GET /time       - Get current time in default timezone")
        print(f"  GET /time/:zone - Get current time in specified timezone")
        print(f"  GET /zones      - List all available timezones")
        print(f"  GET /health     - Server health check")
        
        asyncio.run(api_server.serve(host=args.host, port=args.port))
    except KeyboardInterrupt:
        print('\nServer stopped')
    except Exception as e:
        print(f'Error: {e}')
        exit(1)


if __name__ == '__main__':
    main()