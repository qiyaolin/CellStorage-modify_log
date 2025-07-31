import asyncio
from playwright.async_api import async_playwright, expect

async def run_login_test():
    """
    使用 Playwright 自动化测试登录流程。
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        login_url = "https://ambient-decoder-467517-h8.nn.r.appspot.com/auth/login"
        username = "admin"
        password = "111111"

        try:
            print(f"正在访问登录页面: {login_url}")
            await page.goto(login_url)

            print("页面加载完成。等待页面稳定...")
            await page.wait_for_load_state("networkidle")

            # 假设输入框的 id 或 name 是 'username' 和 'password'
            print(f"正在填写用户名: {username}")
            await page.locator('[name="username"]').fill(username)

            print(f"正在填写密码: {password}")
            await page.locator('[name="password"]').fill(password)

            print("正在点击登录按钮...")
            # 假设登录按钮是 type="submit"
            await page.locator('button[type="submit"]').click()

            print("登录表单已提交。等待页面跳转...")
            await page.wait_for_load_state("networkidle")

            final_url = page.url
            final_title = await page.title()

            print("\\n--- 测试结果 ---")
            print(f"登录后的 URL: {final_url}")
            print(f"登录后的页面标题: {final_title}")

            if "login" in final_url.lower():
                print("\\n诊断: 登录失败，页面仍停留在登录页。")
                # 尝试查找并打印错误消息
                try:
                    error_element = page.locator(".alert-danger, .flash.danger, [data-test-id='flash-message-danger']")
                    error_text = await error_element.inner_text()
                    print(f"页面上显示的错误信息: {error_text}")
                except Exception:
                    print("未在页面上找到明确的错误消息。")
            else:
                print("\\n诊断: 登录成功！已跳转到新页面。")

        except Exception as e:
            print(f"\\n测试过程中发生错误: {e}")
        finally:
            await browser.close()
            print("\\n测试结束。")

if __name__ == "__main__":
    asyncio.run(run_login_test())