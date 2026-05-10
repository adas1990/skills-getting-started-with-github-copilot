import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Arrange: Create a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: Reset activities to known state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        }
    })
    yield
    # Cleanup after test


class TestRootEndpoint:
    """Test GET / endpoint"""
    
    def test_root_redirect(self, client):
        """Arrange: Request root endpoint
           Act: Call GET /
           Assert: Verify redirect to static file"""
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivitiesEndpoint:
    """Test GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Arrange: Activities in memory
           Act: Call GET /activities
           Assert: Verify all activities returned"""
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert data["Chess Club"]["max_participants"] == 12
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_get_activities_structure(self, client):
        """Arrange: Known activity structure
           Act: Call GET /activities
           Assert: Verify correct fields in response"""
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Arrange: Valid activity and email
           Act: Sign up for activity
           Assert: Verify signup succeeds and participant added"""
        # Arrange
        activity_name = "Programming Class"
        email = "john@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_email(self, client):
        """Arrange: Student already signed up
           Act: Attempt duplicate signup
           Assert: Verify 400 error returned"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Arrange: Activity does not exist
           Act: Try to sign up for nonexistent activity
           Assert: Verify 404 error returned"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_with_special_chars_in_email(self, client):
        """Arrange: Email with special characters
           Act: Sign up with complex email
           Assert: Verify signup succeeds"""
        # Arrange
        activity_name = "Programming Class"
        email = "john.doe+test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Test DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_unregister_success(self, client):
        """Arrange: Participant signed up for activity
           Act: Unregister participant
           Assert: Verify participant removed"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        assert email in activities[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_not_signed_up(self, client):
        """Arrange: Participant not signed up
           Act: Try to unregister
           Assert: Verify 404 error returned"""
        # Arrange
        activity_name = "Programming Class"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Arrange: Activity does not exist
           Act: Try to unregister from nonexistent activity
           Assert: Verify 404 error returned"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_with_special_chars_in_email(self, client):
        """Arrange: Participant with special chars in email
           Act: Unregister with complex email
           Assert: Verify unregister succeeds"""
        # Arrange
        activity_name = "Programming Class"
        email = "john.doe+test@mergington.edu"
        activities[activity_name]["participants"].append(email)
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
