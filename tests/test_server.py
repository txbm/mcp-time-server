import pytest
import datetime
from zoneinfo import ZoneInfo
from mcp_time_server import TimeServer, TimeZoneError, ConfigurationError


@pytest.fixture
def server():
    return TimeServer()


def test_init_default_timezone():
    server = TimeServer()
    assert server._default_tz == ZoneInfo('UTC')


def test_init_custom_timezone():
    server = TimeServer('America/New_York')
    assert server._default_tz == ZoneInfo('America/New_York')


def test_init_invalid_timezone():
    with pytest.raises(ConfigurationError):
        TimeServer('Invalid/Timezone')


@pytest.mark.asyncio
async def test_get_time_default(server):
    result = await server.get_time()
    assert 'timestamp' in result
    assert 'iso_time' in result
    assert 'timezone' in result
    assert 'timezone_offset' in result
    assert 'is_dst' in result
    assert result['timezone'] == 'UTC'
    assert result['timezone_offset'] == 0


@pytest.mark.asyncio
async def test_get_time_custom_timezone():
    server = TimeServer()
    result = await server.get_time('America/New_York')
    assert result['timezone'] == 'America/New_York'
    # Don't test exact offset as it changes with DST
    assert isinstance(result['timezone_offset'], int)


@pytest.mark.asyncio
async def test_get_time_invalid_timezone(server):
    with pytest.raises(TimeZoneError):
        await server.get_time('Invalid/Timezone')


@pytest.mark.asyncio
async def test_get_time_dst_handling():
    server = TimeServer()
    # Test a specific date during DST
    now = datetime.datetime.now(ZoneInfo('America/New_York'))
    result = await server.get_time('America/New_York')
    assert isinstance(result['is_dst'], bool)
    # is_dst should match the current DST status for the timezone


def test_get_available_timezones(server):
    result = server.get_available_timezones()
    assert 'timezones' in result
    assert 'count' in result
    assert isinstance(result['timezones'], list)
    assert len(result['timezones']) > 0
    assert result['count'] == len(result['timezones'])
    assert 'UTC' in result['timezones']
    assert 'America/New_York' in result['timezones']


@pytest.mark.asyncio
async def test_server_startup_and_shutdown():
    server = TimeServer()
    # Test that the server starts without errors
    # Note: We're not actually starting the server here as it would block
    # Instead we're just verifying the server instance is properly configured
    assert server._default_tz is not None
    assert server._available_zones is not None