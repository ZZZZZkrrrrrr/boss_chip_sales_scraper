# BOSS 直聘芯片销售招聘抓取

运行顺序：

1. 执行 `scrape_boss_chip_sales.py`，浏览器打开后扫码登录。
2. 脚本自动抓取深圳 `芯片销售` 职位列表和详情，JSON 输出到 `C:\Users\96259\Desktop\AIcoding\贸易`。
3. 执行 `build_boss_chip_sales_excel.mjs`，把 JSON 转成 Excel。

本次默认搜索链接：

`https://www.zhipin.com/web/geek/jobs?query=芯片销售&city=101280600&industry=&position=`
