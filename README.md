# APK 分发服务

开发人员上传 APK 到服务器，生成自定义域名下载链接供测试人员下载。

## 功能

- 上传 APK 到 AWS S3
- 生成自定义域名下载链接
- Web 界面上传和管理文件
- 简单 Token 认证
- 支持断点续传下载

## 快速开始

### 方式一：本地运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

配置项说明：
| 变量 | 说明 |
|------|------|
| S3_BUCKET | S3 存储桶名称 |
| S3_REGION | S3 区域 |
| AWS_ACCESS_KEY_ID | AWS 访问密钥 |
| AWS_SECRET_ACCESS_KEY | AWS 秘密密钥 |
| UPLOAD_TOKEN | 上传认证 Token |
| BASE_URL | 服务基础 URL |

#### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. 使用

访问 http://localhost:8000 打开上传页面，输入 Token 后可上传 APK。

### 方式二：Docker 部署

#### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

#### 2. 构建并启动

```bash
docker-compose up -d --build
```

#### 3. 查看状态

```bash
docker-compose ps
docker-compose logs -f
```

#### 4. 停止服务

```bash
docker-compose down
```

## API 接口

### 上传 APK

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@app.apk"
```

响应：
```json
{
  "id": "xxx-xxx-xxx",
  "filename": "app.apk",
  "size": 12345678,
  "download_url": "https://dl.example.com/download/xxx-xxx-xxx",
  "message": "Upload successful"
}
```

### 下载 APK

直接访问下载链接即可，无需认证：
```
GET /download/{file_id}
```

### 文件列表

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/files
```

### 删除文件

```bash
curl -X DELETE -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/files/{file_id}
```

## 生产部署建议

1. 使用 HTTPS (Nginx 反向代理或直接配置 SSL)
2. 配置合理的 S3 存储桶权限策略
3. 定期清理过期文件
4. 监控上传/下载流量

## 项目结构

```
apkmraeds/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库操作
│   ├── models.py        # 数据模型
│   ├── s3.py            # S3 操作
│   ├── routers/
│   │   ├── upload.py    # 上传接口
│   │   └── download.py  # 下载接口
│   └── templates/
│       ├── index.html   # 上传页面
│       └── list.html    # 文件列表
├── data/                # SQLite 数据库
├── uploads/             # 临时目录
├── requirements.txt
└── .env.example
```