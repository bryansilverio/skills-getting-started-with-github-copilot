from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_data_without_caching(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client):
    # Arrange
    email = "new.student@mergington.edu"
    signup_url = "/activities/Chess%20Club/signup"

    # Act
    response = client.post(signup_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    signup_url = "/activities/Chess%20Club/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    signup_url = "/activities/Unknown%20Club/signup"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    unregister_url = "/activities/Chess%20Club/signup"

    # Act
    response = client.delete(unregister_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    unregister_url = "/activities/Unknown%20Club/signup"
    email = "student@mergington.edu"

    # Act
    response = client.delete(unregister_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_nonparticipant(client):
    # Arrange
    unregister_url = "/activities/Chess%20Club/signup"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(unregister_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
