import asyncio
from playwright.async_api import async_playwright

async def check_website():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # 访问登录页面
            await page.goto('https://ambient-decoder-467517-h8.nn.r.appspot.com/cell-storage/index')
            await page.wait_for_load_state('networkidle')
            
            # 检查是否需要登录
            if 'login' in page.url.lower() or await page.locator('input[name="username"]').count() > 0:
                print("需要登录，正在登录...")
                await page.fill('input[name="username"]', 'admin')
                await page.fill('input[name="password"]', '111111')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
            
            # 检查当前页面的样式
            print("当前页面URL:", page.url)
            
            # 检查导航栏的背景样式
            navbar = await page.locator('.navbar').first
            if await navbar.count() > 0:
                navbar_style = await navbar.get_attribute('style')
                navbar_class = await navbar.get_attribute('class')
                print("导航栏样式:", navbar_style)
                print("导航栏类名:", navbar_class)
                
                # 检查计算后的样式
                navbar_bg = await navbar.evaluate('element => window.getComputedStyle(element).background')
                print("导航栏计算后的背景:", navbar_bg)
            
            # 检查是否加载了科技蓝主题CSS
            stylesheets = await page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
                    return links.map(link => link.href);
                }
            ''')
            print("加载的样式表:")
            for sheet in stylesheets:
                print("-", sheet)
            
            # 检查页面body的背景
            body_bg = await page.evaluate('() => window.getComputedStyle(document.body).background')
            print("页面背景:", body_bg)
            
            # 截图保存
            await page.screenshot(path='current_website.png')
            print("已保存截图: current_website.png")
            
        except Exception as e:
            print(f"访问网站时出错: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_website())