import os
import json
import pytest
import main
from unittest.mock import MagicMock

# --- MOCK DATA ---

MOCK_CONFIG = {
    "accounts": [
        {"platform": "x", "url": "https://x.com/user_x", "last_seen_id": "111"},
        {"platform": "instagram", "url": "https://instagram.com/user_ig", "last_seen_id": "222"},
        {"platform": "tiktok", "url": "https://tiktok.com/@user_tk", "last_seen_id": "333"}
    ]
}

MOCK_X_HTML = """
<html><body><article>
    <a href="/user_x/status/999">Post 999</a>
    <div>Latest X post content</div>
</article></body></html>
"""

MOCK_INSTAGRAM_HTML = """
<html><script type="application/ld+json">
{
  "mainEntityofPage": {
    "@graph": [{
      "mainEntity": [{
        "url": "https://www.instagram.com/p/888/",
        "caption": "Latest Instagram post content"
      }]
    }]
  }
}
</script></html>
"""

MOCK_TIKTOK_HTML = """
<html><script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">
{
  "__DEFAULT_SCOPE__": {
    "webapp.user-detail": {
      "itemlist": {
        "user-post": {
          "list": [{
            "id": "777",
            "desc": "Latest TikTok post content",
            "author": {"uniqueId": "user_tk"}
          }]
        }
      }
    }
  }
}
</script></html>
"""

# --- FIXTURES ---

@pytest.fixture
def mock_config_file(tmp_path):
    """Creates a temporary config file for testing."""
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(MOCK_CONFIG, f)
    return str(config_path)

# --- HELPER FUNCTIONS ---

def mock_requests_get(mocker, text_content):
    """Helper to mock requests.get to return specific content."""
    mock_response = MagicMock()
    mock_response.content = text_content.encode('utf-8')
    mock_response.raise_for_status = MagicMock()
    mocker.patch('requests.get', return_value=mock_response)

# --- TESTS ---

def test_load_and_save_config(tmp_path):
    """Test that we can load and save the JSON config correctly."""
    config_path = tmp_path / "test_config.json"
    main.CONFIG_FILE = str(config_path)

    # Test save
    main.save_config(MOCK_CONFIG)
    assert os.path.exists(config_path)

    # Test load
    loaded_config = main.load_config()
    assert loaded_config == MOCK_CONFIG

def test_check_for_new_x_post_success(mocker):
    """Test the X checker finds a new post."""
    mock_requests_get(mocker, MOCK_X_HTML)
    post_id, post_text, post_url = main.check_for_new_x_post(MOCK_CONFIG['accounts'][0])
    assert post_id == "999"
    assert "Latest X post content" in post_text
    assert post_url == "https://x.com/user_x/status/999"

def test_check_for_new_instagram_post_success(mocker):
    """Test the Instagram checker finds a new post."""
    mock_requests_get(mocker, MOCK_INSTAGRAM_HTML)
    post_id, post_text, post_url = main.check_for_new_instagram_post(MOCK_CONFIG['accounts'][1])
    assert post_id == "888"
    assert post_text == "Latest Instagram post content"
    assert post_url == "https://www.instagram.com/p/888/"

def test_check_for_new_tiktok_post_success(mocker):
    """Test the TikTok checker finds a new post."""
    mock_requests_get(mocker, MOCK_TIKTOK_HTML)
    post_id, post_text, post_url = main.check_for_new_tiktok_post(MOCK_CONFIG['accounts'][2])
    assert post_id == "777"
    assert post_text == "Latest TikTok post content"
    assert "user_tk/video/777" in post_url

def test_check_all_accounts_calls_correct_checkers(mocker, mock_config_file):
    """Verify that the main loop calls the correct function for each platform."""
    main.CONFIG_FILE = mock_config_file
    mock_x = mocker.patch('main.check_for_new_x_post', return_value=(None, None, None))
    mock_ig = mocker.patch('main.check_for_new_instagram_post', return_value=(None, None, None))
    mock_tk = mocker.patch('main.check_for_new_tiktok_post', return_value=(None, None, None))

    main.check_all_accounts()

    mock_x.assert_called_once()
    mock_ig.assert_called_once()
    mock_tk.assert_called_once()

def test_check_all_accounts_triggers_notification(mocker, mock_config_file):
    """Test that a new post triggers a Discord notification and config save."""
    main.CONFIG_FILE = mock_config_file
    # Let's say X has a new post, but others don't
    mocker.patch('main.check_for_new_x_post', return_value=("999", "New X Post", "http://x.com/999"))
    mocker.patch('main.check_for_new_instagram_post', return_value=("222", "Old IG Post", "http://ig.com/222"))
    mocker.patch('main.check_for_new_tiktok_post', return_value=("333", "Old TK Post", "http://tk.com/333"))

    mock_send_discord = mocker.patch('main.send_to_discord')
    mock_save_config = mocker.patch('main.save_config')

    main.check_all_accounts()

    mock_send_discord.assert_called_once()
    mock_save_config.assert_called_once()

    # Check that the config was updated correctly before saving
    args, _ = mock_save_config.call_args
    updated_config = args[0]
    assert updated_config['accounts'][0]['last_seen_id'] == "999" # X id updated
    assert updated_config['accounts'][1]['last_seen_id'] == "222" # IG id unchanged

def test_send_to_discord_formats_correctly(mocker):
    """Test that the discord payload is formatted correctly for a given platform."""
    mocker.patch('main.DISCORD_WEBHOOK_URL', 'http://fake-webhook.com')
    mock_post = mocker.patch('requests.post')

    test_account = MOCK_CONFIG['accounts'][1] # Instagram
    main.send_to_discord(test_account, "IG content", "http://ig.com/p/123")

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    embed = kwargs['json']['embeds'][0]

    assert "INSTAGRAM" in kwargs['json']['content']
    assert embed['author']['name'] == "user_ig"
    assert embed['color'] == 0xE1306C # Instagram color
    assert "IG content" in embed['description']