import requests
from bs4 import BeautifulSoup
import schedule
import time
import os
import json

# --- CONFIGURATION ---
CONFIG_FILE = "config.json"
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', 'YOUR_DISCORD_WEBHOOK_URL_HERE')

def load_config():
    """Loads the configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it.")
        return None
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config_data):
    """Saves the updated configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)

def check_for_new_x_post(account):
    """
    Checks for new posts on a specific X profile.
    Returns a tuple: (post_id, post_text, post_url) or (None, None, None)
    """
    print(f"Checking X account: {account['url']}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(account['url'], headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        latest_post_element = soup.find('article')

        if not latest_post_element:
            print(f"Could not find any posts for {account['url']}. The page structure might have changed.")
            return None, None, None

        post_link_tag = latest_post_element.find('a', href=lambda href: href and '/status/' in href)
        if not post_link_tag or not post_link_tag.has_attr('href'):
            print(f"Could not find the post link for {account['url']}. The page structure might have changed.")
            return None, None, None

        post_url = f"https://x.com{post_link_tag['href']}"
        post_id = post_url.split('/status/')[-1].split('?')[0]
        post_text = latest_post_element.get_text(separator=' ', strip=True)

        return post_id, post_text, post_url

    except requests.RequestException as e:
        print(f"Error fetching {account['url']}: {e}")
    except Exception as e:
        print(f"An error occurred while checking {account['url']}: {e}")
    return None, None, None

def check_for_new_instagram_post(account):
    """
    Checks for new posts on an Instagram profile.
    NOTE: This is very fragile and likely to break if Instagram changes its layout.
    """
    print(f"Checking Instagram account: {account['url']}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(account['url'], headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        # Instagram often embeds data in a specific script tag. This is a best-effort attempt to find it.
        script_tag = soup.find('script', type='application/ld+json')
        if not script_tag:
            print(f"Could not find data script tag for {account['url']}. Instagram may be blocking the request.")
            return None, None, None

        data = json.loads(script_tag.string)
        # The data structure can change, so we navigate it carefully.
        graph = data.get('mainEntityofPage', {}).get('@graph', [])
        if not graph or not isinstance(graph, list) or len(graph) == 0:
            return None, None, None

        latest_post = graph[0].get('mainEntity', [{}])[0]
        if not latest_post:
            return None, None, None

        post_url = latest_post.get('url')
        if not post_url:
            return None, None, None

        post_id = post_url.split('/')[-2]
        post_text = latest_post.get('caption', 'No caption found.')

        return post_id, post_text, post_url

    except requests.RequestException as e:
        print(f"Error fetching {account['url']}: {e}")
    except (json.JSONDecodeError, AttributeError, IndexError, KeyError) as e:
        print(f"Error parsing Instagram data for {account['url']}: {e}. The page structure has likely changed.")
    return None, None, None

def check_for_new_tiktok_post(account):
    """
    Checks for new posts on a TikTok profile.
    NOTE: This is extremely fragile and likely to break.
    """
    print(f"Checking TikTok account: {account['url']}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(account['url'], headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__')
        if not script_tag:
            print(f"Could not find data script tag for {account['url']}. TikTok may be blocking the request.")
            return None, None, None

        data = json.loads(script_tag.string)
        item_list_key = list(data['__DEFAULT_SCOPE__']['webapp.user-detail']['itemlist'].keys())[0]
        latest_post = data['__DEFAULT_SCOPE__']['webapp.user-detail']['itemlist'][item_list_key]['list'][0]

        post_id = latest_post.get('id')
        post_text = latest_post.get('desc', 'No caption found.')
        author_unique_id = latest_post.get('author', {}).get('uniqueId', 'unknown')
        post_url = f"https://www.tiktok.com/@{author_unique_id}/video/{post_id}"

        return post_id, post_text, post_url

    except requests.RequestException as e:
        print(f"Error fetching {account['url']}: {e}")
    except (json.JSONDecodeError, AttributeError, IndexError, KeyError) as e:
        print(f"Error parsing TikTok data for {account['url']}: {e}. The page structure has likely changed.")
    return None, None, None

def check_all_accounts():
    """
    Iterates through all accounts in the config and checks for new posts.
    """
    print("\n--- Running scheduled check for all accounts ---")
    config = load_config()
    if not config or 'accounts' not in config:
        print("Config is invalid or has no accounts.")
        return

    for i, account in enumerate(config['accounts']):
        post_id, post_text, post_url = None, None, None

        platform = account.get('platform')
        if platform == 'x':
            post_id, post_text, post_url = check_for_new_x_post(account)
        elif platform == 'instagram':
            post_id, post_text, post_url = check_for_new_instagram_post(account)
        elif platform == 'tiktok':
            post_id, post_text, post_url = check_for_new_tiktok_post(account)

        if post_id and post_id != account.get('last_seen_id'):
            print(f"NEW POST FOUND for {account['url']}! ID: {post_id}")
            send_to_discord(account, post_text, post_url)
            config['accounts'][i]['last_seen_id'] = post_id
        else:
            print(f"No new posts for {account['url']}.")

    save_config(config)
    print("--- Check complete ---\n")

def send_to_discord(account, post_text, post_url):
    """
    Sends a message to the configured Discord webhook.
    """
    if not DISCORD_WEBHOOK_URL or 'YOUR_DISCORD_WEBHOOK_URL_HERE' in DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not configured. Skipping notification.")
        return

    if len(post_text) > 2000:
        post_text = post_text[:2000] + "..."

    platform_colors = {
        "x": 0x1DA1F2,
        "instagram": 0xE1306C,
        "tiktok": 0x000000,
    }

    data = {
        "content": f"New post from **{account.get('platform', 'Unknown').upper()}**!",
        "embeds": [{
            "description": post_text,
            "author": {
                "name": account.get('url', 'Unknown').rstrip('/').split('/')[-1],
                "url": account.get('url'),
            },
            "fields": [{
                "name": "Post Link",
                "value": f"[Click here to view]({post_url})"
            }],
            "color": platform_colors.get(account.get('platform'), 0x777777)
        }]
    }

    try:
        result = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        result.raise_for_status()
        print("Successfully sent notification to Discord.")
    except requests.RequestException as e:
        print(f"Error sending to Discord: {e}")

def main():
    """
    Main function to schedule and run the checking job.
    """
    print("Starting the multi-platform post checker...")
    # Schedule the job to run every 5 minutes.
    schedule.every(5).minutes.do(check_all_accounts)

    # Run the check once immediately at the start.
    check_all_accounts()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()