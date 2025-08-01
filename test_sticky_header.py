import asyncio
from playwright.async_api import async_playwright, TimeoutError

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(30000)

        try:
            # Go to the login page
            await page.goto("https://ambient-decoder-467517-h8.nn.r.appspot.com/login")
            
            # Instruct the user to log in
            print("=======================================================================")
            print(" A browser window has been opened. Please log in now.")
            print(" 🚀 一个浏览器窗口已经打开，请您立即登录。")
            print("=======================================================================")

            # Wait for the user to log in and navigate to the inventory page
            inventory_url = "https://ambient-decoder-467517-h8.nn.r.appspot.com/cell-storage/inventory"
            print(f"Script is waiting for you to arrive at the inventory page...")
            await page.wait_for_url(inventory_url, timeout=120000) # 2-minute timeout

            print("\nOK: Inventory page loaded. Resuming automated test...")

            # Click the "View All" button
            print("Clicking 'View All' button to load all data...")
            view_all_button_selector = 'a.btn:has-text("View All")'
            await page.click(view_all_button_selector)
            print("OK: Clicked 'View All'. Waiting for data to load...")

            # Wait for the network to be idle, indicating that the data has loaded
            await page.wait_for_load_state('networkidle')
            print("OK: All data loaded.")

            # Define selectors
            search_results_header_selector = ".search-results-table-container thead th"
            table_container_selector = ".search-results-table-container"
            
            print("Waiting for search results table header...")
            await page.wait_for_selector(search_results_header_selector)
            print("OK: Search results table header is visible.")

            header_element = page.locator(search_results_header_selector).first
            container_element = page.locator(table_container_selector)

            print("Scrolling down to test sticky behavior...")
            await page.evaluate(f"document.querySelector('{table_container_selector}').scrollTop = 500")
            await page.wait_for_timeout(1000) # Wait for rendering
            print("OK: Scrolled down 500px inside the table container.")

            # After scrolling, the header's top should be very close to the container's top.
            scrolled_header_box = await header_element.bounding_box()
            scrolled_header_top = scrolled_header_box['y'] if scrolled_header_box else -1

            scrolled_container_box = await container_element.bounding_box()
            scrolled_container_top = scrolled_container_box['y'] if scrolled_container_box else -1
            
            print(f"After scroll: Container top: {scrolled_container_top:.2f}px, Header top: {scrolled_header_top:.2f}px")
            
            # The header's top position should be almost equal to the container's top position.
            if scrolled_header_top is not None and abs(scrolled_header_top - scrolled_container_top) < 5:
                 print(f"✅ TEST PASSED: Header stuck correctly at the top of its container.")
            else:
                 print(f"❌ TEST FAILED: Header did not stick correctly. Expected: ~{scrolled_container_top:.2f}px, Got: {scrolled_header_top:.2f}px")

        except TimeoutError:
            print("\n❌ TEST FAILED: Timed out waiting for you to log in and navigate to the inventory page.")
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("Taking a screenshot to 'error_screenshot.png'...")
            await page.screenshot(path="error_screenshot.png")
            print("OK: Screenshot saved.")
        finally:
            print("Test finished. Closing browser in 10 seconds...")
            await page.wait_for_timeout(10000)
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())