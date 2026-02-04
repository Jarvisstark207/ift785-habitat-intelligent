"""Tests API pour les endpoints"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Nettoyer cache
for key in list(sys.modules.keys()):
    if key == 'app' or key.startswith('app.'):
        del sys.modules[key]

from app import app

@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


class TestDashboardEndpoints:
    """Tests endpoints dashboard"""
    
    def test_get_dashboard_data_success(self, client):
        """Test GET /api/data retourne données"""
        response = client.get("/api/data")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'global' in data
        assert 'locations' in data
        assert 'alerts' in data
        assert 'recent' in data
    
    def test_get_dashboard_data_has_global_stats(self, client):
        """Test données globales présentes"""
        response = client.get("/api/data")
        data = response.json()
        
        global_stats = data['global']
        assert 'total_consumption' in global_stats
        assert 'occupied_rooms' in global_stats
        assert 'avg_temp' in global_stats


class TestHistoryEndpoints:
    """Tests endpoints historique"""
    
    def test_get_history_without_filters(self, client):
        """Test GET /api/data/history sans filtres"""
        response = client.get("/api/data/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'filters' in data
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_history_with_location_filter(self, client):
        """Test filtrage par location"""
        response = client.get("/api/data/history?location=salon")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['filters']['location'] == "salon"
    
    def test_get_history_with_sensor_type_filter(self, client):
        """Test filtrage par type de capteur"""
        response = client.get("/api/data/history?sensor_type=temperature")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['filters']['sensor_type'] == "temperature"
    
    def test_get_history_with_limit(self, client):
        """Test limitation du nombre de résultats"""
        response = client.get("/api/data/history?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data['data']) <= 5
    
    def test_get_hourly_stats_success(self, client):
        """Test GET /api/stats/hourly"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/stats/hourly?date={today}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'date' in data
        assert 'hourly_stats' in data
        assert isinstance(data['hourly_stats'], list)
    
    def test_get_hourly_stats_with_location(self, client):
        """Test stats horaires avec filtre location"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/stats/hourly?location=salon&date={today}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['location'] == "salon"


class TestAlertEndpoints:
    """Tests endpoints alertes"""
    
    def test_get_alert_config_success(self, client):
        """Test GET /api/alerts/config"""
        response = client.get("/api/alerts/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'temperature' in data
        assert 'consumption' in data
        assert 'min' in data['temperature']
        assert 'max' in data['temperature']

    def test_post_alert_config_success(self, client):
        """Test POST /api/alerts/config"""
        response = client.post("/api/alerts/config", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'ok'
        assert 'message' in data
    
    def test_get_active_alerts_success(self, client):
        """Test GET /api/alerts/active"""
        response = client.get("/api/alerts/active")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'alerts' in data
        assert isinstance(data['alerts'], list)
        assert data['count'] == len(data['alerts'])
