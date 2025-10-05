import os
import pytest
from main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_webhook_tiktok(client):
    """Test webhook for TikTok."""
    response = client.post('/webhook?platform=tiktok', json={'post_url': 'http://tiktok.com/post1'})
    assert response.status_code == 200
    assert response.json == {"status": "success"}

def test_webhook_instagram(client):
    """Test webhook for Instagram."""
    response = client.post('/webhook?platform=instagram', json={'post_url': 'http://instagram.com/post1'})
    assert response.status_code == 200
    assert response.json == {"status": "success"}

def test_webhook_x(client):
    """Test webhook for X."""
    response = client.post('/webhook?platform=x', json={'post_url': 'http://x.com/post1'})
    assert response.status_code == 200
    assert response.json == {"status": "success"}

def test_webhook_douyin(client):
    """Test webhook for Douyin."""
    response = client.post('/webhook?platform=douyin', json={'post_url': 'http://douyin.com/post1'})
    assert response.status_code == 200
    assert response.json == {"status": "success"}

def test_webhook_unsupported_platform(client):
    """Test webhook for an unsupported platform."""
    response = client.post('/webhook?platform=facebook', json={'post_url': 'http://facebook.com/post1'})
    assert response.status_code == 400
    assert response.json == {"status": "error", "message": "Unsupported platform"}

def test_save_post_url():
    """Test if the post URL is saved to the log file."""
    if os.path.exists('posts.log'):
        os.remove('posts.log')

    client = app.test_client()
    client.post('/webhook?platform=tiktok', json={'post_url': 'http://tiktok.com/test_post'})

    assert os.path.exists('posts.log')
    with open('posts.log', 'r') as f:
        content = f.read()
        assert "[TIKTOK] New post: http://tiktok.com/test_post\n" in content

    os.remove('posts.log')