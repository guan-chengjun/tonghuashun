# 同花顺风格 A股看盘工具

网页版股票行情终端，深色同花顺风格，单文件 HTML + FastAPI 后端。

## 功能特性

- **实时行情**：股票搜索、自选列表、实时报价、涨跌幅
- **多周期图表**：分时图、5分/15分/30分/60分钟K线、日K线
- **盘口数据**：五档买卖盘、成交明细、实时刷新
- **排行榜**：涨幅榜、跌幅榜、换手率榜
- **基本面**：个股基本信息查看
- **自选股**：本地存储，支持快速切换

## 技术栈

**前端**
- 原生 JavaScript（无框架依赖）
- Tailwind CSS（CDN）
- ECharts 5.4.3（K线图、分时图）
- 响应式布局，支持桌面和移动端

**后端**
- FastAPI
- akshare（A股数据源）
- Python 3.8+

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install fastapi uvicorn akshare pandas
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

requirements.txt 内容：
```
fastapi==0.104.1
uvicorn==0.24.0
akshare==1.11.80
pandas==2.1.3
```

### 2. 启动后端服务

```bash
python main.py
```

或使用 uvicorn 命令：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后，后端运行在 `http://127.0.0.1:8000`

### 3. 打开前端页面

双击 `index.html` 文件，浏览器打开即可使用。

或通过本地服务器访问：

```bash
# Python 3
python -m http.server 8080

# 然后访问 http://localhost:8080/index.html
```

## API 接口文档

后端提供 7 个 REST API 接口：

### 1. 搜索股票
```
GET /api/search?q=贵州茅台
返回：[{code: "600519", name: "贵州茅台"}, ...]
```

### 2. 实时行情
```
GET /api/spot?code=600519
返回：{price, change, pct, open, high, low, volume, amount, bids[], asks[], ...}
```

### 3. 分时数据
```
GET /api/timeline?code=600519
返回：{minutes: [{time, open, close, high, low, volume}], trades: [{time, price, vol, dir}]}
```

### 4. 日K线
```
GET /api/daily?code=600519&limit=240
返回：[{date, open, close, high, low, volume, amount, pct}, ...]
```

### 5. 分钟K线
```
GET /api/minute?code=600519&period=5
参数 period: 5/15/30/60
返回：[{time, open, close, high, low, volume}, ...]
```

### 6. 涨幅榜
```
GET /api/rank?type=up
参数 type: up/down/turnover/amount
返回：[{code, name, price, pct, volume, turnover}, ...]
```

### 7. 基本面
```
GET /api/basic?code=600519
返回：{总股本: "xxx", 流通股: "xxx", 每股收益: "xxx", ...}
```

完整 API 文档：启动后端后访问 `http://127.0.0.1:8000/docs`

## 使用说明

### 基本操作

1. **搜索股票**：顶部搜索框输入代码或名称（如 `600519` 或 `贵州茅台`）
2. **查看行情**：点击搜索结果，加载股票详情和图表
3. **切换周期**：点击"分时/5分/15分/30分/60分/日K"切换图表周期
4. **加自选**：点击"加自选"按钮，股票加入左侧自选列表（本地存储）
5. **查看排行**：右侧面板查看涨幅榜、跌幅榜、换手率榜
6. **查看基本面**：右侧切换到"基本面"标签，查看个股详细信息

### 图表交互

- **分时图**：显示当日分钟线，蓝色为价格线，黄色为均价线
- **K线图**：显示蜡烛图 + MA5/10/20/60 均线 + 成交量柱
- **缩放**：鼠标滚轮或拖动底部滑块缩放K线图
- **十字线**：鼠标悬停显示详细数据

### 五档盘口

左下角显示实时买卖五档：
- **卖五～卖一**：绿色（跌），价格从高到低
- **买一～买五**：红色（涨），价格从高到低
- 中间显示当前价格和涨跌幅

### 成交明细

右下角显示最近 50 笔成交：
- 红色：主动买入
- 绿色：主动卖出

### 自动刷新

选中股票后，每 3 秒自动刷新实时行情（价格、盘口、成交明细）。

## 注意事项

1. **数据源**：使用 akshare 抓取东方财富网公开数据，仅供学习研究，不构成投资建议
2. **API 限频**：请勿过于频繁请求，避免被数据源封禁
3. **交易时间**：非交易时段（周末、节假日、休市时间）数据不更新
4. **网络要求**：需要连接互联网访问数据接口
5. **浏览器兼容**：建议使用 Chrome/Edge/Firefox 最新版

## 替换数据源

如需使用其他数据源（如 `zzshare`、`tushare`、`baostock`），修改 `main.py`：

```python
# 将所有 akshare 调用替换为对应库的函数
import zzshare as zz  # 替换 import akshare as ak

# 示例：
df = zz.stock_info_a_code_name()  # 替换 ak.stock_info_a_code_name()
```

保持接口返回格式一致即可。

## 目录结构

```
tonghuashun/
├── main.py          # FastAPI 后端
├── index.html       # 前端页面（单文件）
├── README.md        # 本文档
└── requirements.txt # Python 依赖（可选）
```

## 常见问题

**Q: 页面打开后显示"加载失败"？**  
A: 检查后端是否启动（`python main.py`），确认运行在 `http://127.0.0.1:8000`

**Q: 搜索不到股票？**  
A: 检查网络连接，akshare 首次运行需要下载股票列表

**Q: K线图显示不全？**  
A: 拖动底部滑块或鼠标滚轮缩放，默认显示最近 30% 数据

**Q: 如何修改自动刷新频率？**  
A: 编辑 `index.html` 第 326 行，修改 `3000`（毫秒）为其他值

**Q: 支持港股/美股吗？**  
A: 当前仅支持 A股，如需其他市场，修改后端数据源

## 免责声明

本工具仅供学习交流使用，不构成任何投资建议。股市有风险，投资需谨慎。作者不对使用本工具产生的任何损失负责。

## 开源协议

MIT License

---

**开发者**: Claude (Anthropic)  
**版本**: 1.0.0  
**更新日期**: 2024
