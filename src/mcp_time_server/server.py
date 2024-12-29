import asyncio
import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, available_timezones, ZoneInfoNotFoundError

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .exceptions import TimeZoneError, ConfigurationError


class TimeServer:
    """MCP Time Server implementation providing timezone-aware time information."""

    def __init__(self, default_timezone: str = "UTC") -> None:
        """Initialize the time server.
        
        Args:
            default_timezone: IANA timezone identifier (e.g. 'America/New_York')
            
        Raises:
            ConfigurationError: If the default timezone is invalid
        """
        try:
            self._default_tz = ZoneInfo(default_timezone)
            self._available_zones = available_timezones()
            
            # Initialize MCP server
            self.server = Server("mcp-time-server")
            self._setup_mcp_handlers()
            
        except ZoneInfoNotFoundError as e:
            raise ConfigurationError(f"Invalid default timezone: {default_timezone}") from e

    def _setup_mcp_handlers(self) -> None:
        """Configure MCP message handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available time-related tools."""
            return [
                types.Tool(
                    name="get_time",
                    description="Get current time in specified timezone",
                    parameters={
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string", 
                                "description": "IANA timezone identifier (e.g. 'America/New_York')"
                            }
                        },
                        "required": []
                    },
                    returns={
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "number"},
                            "iso_time": {"type": "string"},
                            "timezone": {"type": "string"},
                            "timezone_offset": {"type": "integer"},
                            "is_dst": {"type": "boolean"}
                        }
                    }
                ),
                types.Tool(
                    name="list_timezones",
                    description="List all available IANA timezone identifiers",
                    parameters={
                        "type": "object",
                        "properties": {},
                        "required": []
                    },
                    returns={
                        "type": "object",
                        "properties": {
                            "timezones": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "count": {"type": "integer"}
                        }
                    }
                )
            ]

        @self.server.invoke_tool()
        async def handle_invoke_tool(name: str, arguments: Dict[str, Any]) -> Any:
            """Handle tool invocations."""
            if name == "get_time":
                timezone = arguments.get("timezone", None)
                return await self._get_time(timezone)
            elif name == "list_timezones":
                return self._get_available_timezones()
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def _get_time(self, timezone: Optional[str] = None) -> Dict[str, Any]:
        """Get the current time in the specified timezone.
        
        Args:
            timezone: Optional IANA timezone identifier. Uses default if not specified.
            
        Returns:
            Dict containing time information
            
        Raises:
            TimeZoneError: If the specified timezone is invalid
        """
        try:
            tz = ZoneInfo(timezone) if timezone else self._default_tz
            if timezone and timezone not in self._available_zones:
                raise TimeZoneError(f"Unknown timezone: {timezone}")

            now = datetime.datetime.now(tz)
            utc_offset = now.utcoffset()
            if utc_offset is None:  # This should never happen with ZoneInfo
                raise TimeZoneError(f"Invalid timezone offset for {timezone}")

            offset_minutes = int(utc_offset.total_seconds() / 60)

            return {
                "timestamp": now.timestamp(),
                "iso_time": now.isoformat(),
                "timezone": str(tz),
                "timezone_offset": offset_minutes,
                "is_dst": now.dst() is not None and now.dst() != datetime.timedelta(0)
            }

        except ZoneInfoNotFoundError as e:
            raise TimeZoneError(f"Invalid timezone: {timezone}") from e

    def _get_available_timezones(self) -> Dict[str, Any]:
        """Get list of all available timezones.
        
        Returns:
            Dict containing list of timezones and count
        """
        return {
            "timezones": sorted(list(self._available_zones)),
            "count": len(self._available_zones)
        }

    async def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the MCP server using stdio transport.
        
        Args:
            host: Ignored for stdio transport
            port: Ignored for stdio transport
            
        Raises:
            ConfigurationError: If server cannot be started
        """
        try:
            # Initialize with stdio transport
            await mcp.server.stdio.serve(
                self.server,
                InitializationOptions(
                    capabilities=["tools"]  # Declare our capabilities
                )
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to start server: {e}") from e


def main() -> None:
    """Main entry point."""
    server = TimeServer()
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()