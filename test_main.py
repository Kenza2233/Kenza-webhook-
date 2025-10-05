import os
import json
import pytest
import main

# --- MOCK DATA & CONFIG ---
MOCK_CONFIG_DATA = {
    "accounts": [
        {"platform": "x", "url": "https://x.com/user_x", "last_seen_id": "111"}
    ]
}

# --- FIXTURES ---

@pytest.fixture
def client():
    """Create a Flask test client."""
    main.app.config['TESTING'] = True
    main.app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms

    # Create a temporary config file for each test
    with open(main.CONFIG_FILE, 'w') as f:
        json.dump(MOCK_CONFIG_DATA, f)

    with main.app.test_client() as client:
        yield client

    # Clean up the config file after the test
    if os.path.exists(main.CONFIG_FILE):
        os.remove(main.CONFIG_FILE)

# --- TESTS FOR WEB ROUTES ---

def test_index_page_loads(client):
    """Test that the index page loads and shows the monitored account."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Social Media Monitor" in response.data
    assert b"https://x.com/user_x" in response.data

def test_add_account_success(client):
    """Test adding a new, valid account."""
    response = client.post('/add', data={'url': 'https://www.instagram.com/nasa/'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Successfully added instagram account" in response.data

    # Check if config.json was updated
    config = main.load_config()
    assert len(config['accounts']) == 2
    assert config['accounts'][1]['url'] == 'https://www.instagram.com/nasa/'

def test_add_account_duplicate(client):
    """Test that adding a duplicate account shows an error."""
    response = client.post('/add', data={'url': 'https://x.com/user_x'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"This account is already being monitored" in response.data

    config = main.load_config()
    assert len(config['accounts']) == 1

def test_add_account_unknown_platform(client):
    """Test adding an account from an unsupported platform."""
    response = client.post('/add', data={'url': 'https://example.com/user'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Could not determine platform for URL" in response.data

def test_remove_account_success(client):
    """Test removing an existing account."""
    response = client.post('/remove', data={'url': 'https://x.com/user_x'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Successfully removed account" in response.data

    config = main.load_config()
    assert len(config['accounts']) == 0

def test_remove_account_not_found(client):
    """Test trying to remove an account that doesn't exist."""
    response = client.post('/remove', data={'url': 'https://x.com/nonexistent'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Could not find the account to remove" in response.data

# --- TESTS FOR HELPER FUNCTIONS ---

@pytest.mark.parametrize("url, expected_platform", [
    ("https://x.com/elonmusk", "x"),
    ("https://twitter.com/nasa", "x"),
    ("https://www.instagram.com/google/", "instagram"),
    ("https://www.tiktok.com/@zachking", "tiktok"),
    ("https://facebook.com/meta", "unknown"),
    ("invalid-url", "unknown"),
    ("", "unknown")
])
def test_get_platform_from_url(url, expected_platform):
    """Test the platform detection logic for various URLs."""
    assert main.get_platform_from_url(url) == expected_platform

# --- NOTE ON MONITORING TESTS ---
# The monitoring logic itself is already tested in the previous test suite.
# Since the functions (`check_for_new_x_post`, etc.) have not changed,
# and we've tested the web logic that modifies the config, we can be
# confident in the integration. Re-testing the scraper here would be redundant.