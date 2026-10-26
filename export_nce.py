import os
import asyncio
from playwright.async_api import async_playwright

/*
# 创建一个名为 venv 的虚拟环境
python3 -m venv venv
# 激活虚拟环境（激活后，终端命令行前面会多出一个 (venv) 提示符）
source venv/bin/activate
#在虚拟环境中安装 Playwright
pip install playwright
# 安装浏览器驱动
playwright install
#运行你的导出脚本
python export_nce.py
*/

async def export_nce_direct():
    async with async_playwright() as p:
        # 启动无头浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        root_dir = "NCE_Notes_PDFs"
        os.makedirs(root_dir, exist_ok=True)

        print("开始通过 ID 遍历导出《新概念英语》打印版笔记 (1 至 281)...")

        # 遍历 1 到 281 课
        for lesson_id in range(1, 282):
            url = f"https://www.ncego.com/lessons/{lesson_id}?pdf"
            try:
                # 访问专用的打印版页面
                response = await page.goto(url, timeout=30000, wait_until="networkidle")
                
                # 如果页面不存在、报错或者被重定向回首页，则跳过
                if not response or response.status >= 400 or page.url == "https://www.ncego.com/":
                    continue

                # 100% 确定 H1 存在，直接获取 H1 文本
                h1_element = page.locator("h1").first
                h1_text = await h1_element.inner_text()

                # 清洗文件名：允许字母、数字、空格、& 符号以及常见中英文标点，防止 & 消失变成粘连数字
                allowed_chars = (' ', '_', '-', '&', '第', '册', '课', '（', '）', '(', ')', '.', '·', ',', '，', '、', '：', ':')
                safe_title = "".join(c for c in h1_text if c.isalnum() or c in allowed_chars).strip()
                
                if not safe_title:
                    safe_title = f"lesson_{lesson_id}"

                # 直接使用 H1 标签作为文件名（无任何数字前缀）
                pdf_filename = f"{safe_title}.pdf"
                pdf_path = os.path.join(root_dir, pdf_filename)

                # 防止同名文件冲突（若存在相同 H1，自动加上 ID 后缀区分）
                if os.path.exists(pdf_path):
                    pdf_filename = f"{safe_title} ({lesson_id}).pdf"
                    pdf_path = os.path.join(root_dir, pdf_filename)

                # 导出为独立 PDF
                await page.pdf(
                    path=pdf_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"}
                )
                print(f"已成功保存: {pdf_filename}")

                # 短暂缓冲，避免请求过快
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"[{lesson_id}/281] 导出出错: {e}")

        await browser.close()
        print("🎉 全部课程导出完成！所有 PDF 已整齐保存在当前目录下的 'NCE_Notes_PDFs' 文件夹中。")

if __name__ == "__main__":
    asyncio.run(export_nce_direct())