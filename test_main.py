import pytest
from fastapi.testclient import TestClient
from fastapi import Request, Form
import json
import main

client = TestClient(main.app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type")


myData = {
    "location_input": "Shoreview, Minnesota",
    "time_start": "1:00",
    "user_lat": "1",
    "user_long": "1",
    "user_city": "Shoreview",
    "user_state": "Minnesota",
}
def test_get_data():
    response = client.post("/", data=myData)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type")


@pytest.mark.parametrize(
    "feels_like_f, expected_result",
    [
        (float("-inf"), 1),
        (0, 1),
        (1, 2),
        (30, 3),
        (40, 4),
        (50, 5),
        (60, 4),
        (73, 3),
        (80, 2),
        (90, 1),
        (float("inf"), 1),
    ],
)
def test_score_weather(feels_like_f, expected_result):
    """Test edge cases for score calculation"""
    assert main.score_weather(feels_like_f, 0, 0) == expected_result
    assert main.score_weather(feels_like_f, 80, 0) == expected_result
