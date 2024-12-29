import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
import json

from mcp_time_server import TimeServer
from mcp_time_server.api import TimeServerAPI


@pytest.fixture
async def api_client():
    """Create a test client for the API."""
    time_server = TimeServer()
    api = TimeServerAPI(time_server)
    
    async with TestClient(TestServer(api.app)) as client:
        yield client


@pytest.mark.asyncio
async def test_get_time_default(api_client):
    """Test getting time in default timezone."""
    resp = await api_client.get('/')
    assert resp.status == 200
    
    data = await resp.json()
    assert 'timestamp' in data
    assert 'iso_time' in data
    assert 'timezone' in data
    assert data['timezone'] == 'UTC'


@pytest.mark.asyncio
async def test_get_time_specific_zone(api_client):
    """Test getting time in a specific timezone."""
    resp = await api_client.get('/time/America/New_York')
    assert resp.status == 200
    
    data = await resp.json()
    assert data['timezone'] == 'America/New_York'


@pytest.mark.asyncio
async def test_get_time_invalid_zone(api_client):
    """Test getting time with invalid timezone."""
    resp = await api_client.get('/time/Invalid/Zone')
    assert resp.status == 400
    
    data = await resp.json()
    assert 'error' in data


@pytest.mark.asyncio
async def test_list_zones(api_client):
    """Test listing available timezones."""
    resp = await api_client.get('/zones')
    assert resp.status == 200
    
    data = await resp.json()
    assert 'timezones' in data
    assert 'count' in data
    assert isinstance(data['timezones'], list)
    assert len(data['timezones']) > 0
    assert data['count'] == len(data['timezones'])


@pytest.mark.asyncio
async def test_health_check(api_client):
    """Test health check endpoint."""
    resp = await api_client.get('/health')
    assert resp.status == 200
    
    data = await resp.json()
    assert data['status'] == 'healthy'
    assert 'version' in data


@pytest.mark.asyncio
async def test_time_aliases(api_client):
    """Test that / and /time return the same data."""
    resp1 = await api_client.get('/')
    resp2 = await api_client.get('/time')
    
    assert resp1.status == 200
    assert resp2.status == 200
    
    data1 = await resp1.json()
    data2 = await resp2.json()
    
    # Compare structure (actual times will differ slightly)
    assert set(data1.keys()) == set(data2.keys())