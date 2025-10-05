from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Navigate to the local server
        page.goto("http://127.0.0.1:5000")

        # 2. Check for the main heading and take an initial screenshot
        heading = page.get_by_role("heading", name="Social Media Monitor")
        expect(heading).to_be_visible()
        page.screenshot(path="jules-scratch/verification/01_initial_page.png")

        # 3. Fill out the form to add a new account
        url_input = page.get_by_placeholder("Enter profile URL")
        url_input.fill("https://www.instagram.com/google/")

        # 4. Click the submit button
        page.get_by_role("button", name="Add Account").click()

        # 5. Verify the success message and the new account in the list
        # Use a more robust locator to find the success flash message
        success_message = page.locator("li.success")
        expect(success_message).to_be_visible()
        expect(success_message).to_contain_text("Successfully added instagram account")

        # Use a specific locator to target only the link
        expect(page.get_by_role("link", name="https://www.instagram.com/google/")).to_be_visible()

        # 6. Take a final screenshot for visual verification
        page.screenshot(path="jules-scratch/verification/02_account_added.png")

        browser.close()
        print("Verification script completed and screenshots taken.")

if __name__ == "__main__":
    run_verification()