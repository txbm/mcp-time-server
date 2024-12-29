from aiohttp import web
import json
from typing import Dict, Any

from .server import TimeServer
from .exceptions import TimeZoneError, ConfigurationError


class TimeServerAPI:
    """HTTP API for the TimeServer."""

    def __init__(self, time_server: TimeServer) -> None:
        """Initialize the API with a TimeServer instance.

        Args:
            time_server: Configured TimeServer instance
        """
        self.time_server = time_server
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure API routes."""
        self.app.router.add_get("/", self.get_time)
        self.app.router.add_get("/time", self.get_time)  # alias for /
        self.app.router.add_get("/time/{timezone}", self.get_time_zone)
        self.app.router.add_get("/zones", self.list_zones)
        self.app.router.add_get("/health", self.health_check)

    async def get_time(self, request: web.Request) -> web.Response:
        """Get current time in default timezone.

        Returns:
            JSON response with time information
        """
        try:
            result = await self.time_server.get_time()
            return web.json_response(result)
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, status=500
            )

    async def get_time_zone(self, request: web.Request) -> web.Response:
        """Get current time in specified timezone.

        Args:
            request: HTTP request with timezone parameter

        Returns:
            JSON response with time information
        """
        timezone = request.match_info.get("timezone", "")
        try:
            result = await self.time_server.get_time(timezone)
            return web.json_response(result)
        except TimeZoneError as e:
            return web.json_response(
                {"error": str(e)}, status=400
            )
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, status=500
            )

    async def list_zones(self, request: web.Request) -> web.Response:
        """List all available timezones.

        Returns:
            JSON response with list of timezones
        """
        try:
            result = self.time_server.get_available_timezones()
            return web.json_response(result)
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, status=500
            )

    async def health_check(self, request: web.Request) -> web.Response:
        """Simple health check endpoint.

        Returns:
            JSON response with status information
        """
        return web.json_response({
            "status": "healthy",
            "version": "0.1.0"
        })

    async def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the API server.

        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        print(f"Starting API server at http://{host}:{port}")
        await site.start()

        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour