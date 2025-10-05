from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    This endpoint receives webhooks from various platforms.
    """
    platform = request.args.get('platform')
    data = request.json

    if platform == 'tiktok':
        handle_tiktok(data)
    elif platform == 'instagram':
        handle_instagram(data)
    elif platform == 'x':
        handle_x(data)
    elif platform == 'douyin':
        handle_douyin(data)
    else:
        return jsonify({"status": "error", "message": "Unsupported platform"}), 400

    return jsonify({"status": "success"}), 200

def handle_tiktok(data):
    """Handles TikTok webhook data."""
    post_url = data.get('post_url')
    if post_url:
        save_post_url('tiktok', post_url)

def handle_instagram(data):
    """Handles Instagram webhook data."""
    post_url = data.get('post_url')
    if post_url:
        save_post_url('instagram', post_url)

def handle_x(data):
    """Handles X (Twitter) webhook data."""
    post_url = data.get('post_url')
    if post_url:
        save_post_url('x', post_url)

def handle_douyin(data):
    """Handles Douyin webhook data."""
    post_url = data.get('post_url')
    if post_url:
        save_post_url('douyin', post_url)

def save_post_url(platform, url):
    """Saves the post URL to a log file."""
    with open('posts.log', 'a') as f:
        f.write(f"[{platform.upper()}] New post: {url}\n")

if __name__ == '__main__':
    app.run(debug=True, port=5000)