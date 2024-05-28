# autogen

## 1.1 搭建生产环境

### 1.1.1 克隆项目代码

```bash
git clone https://github.com/yangyifeng1128/autogen.git
```

### 1.1.2 部署项目代码

安装 Miniconda：

https://docs.anaconda.com/free/miniconda/#quick-command-line-install

```bash
# 安装 miniconda
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
# 为 conda 虚拟环境配置 shell
~/miniconda3/bin/conda init bash
```

创建并激活 Conda 虚拟环境：

```bash
conda create -n autogen
conda activate autogen
```

安装依赖包：

```bash
(autogen) cd autogen
(autogen) pip install -r requirements.txt
```

启动 uvicorn 服务器：

```bash
(autogen) mkdir /root/logs/autogen
(autogen) touch /root/logs/autogen/access.log
(autogen) nohup uvicorn app.main:app --host 0.0.0.0 --port 6001 > /root/logs/autogen/access.log 2>&1 &
```

### 1.1.3 配置 Nginx 服务器

安装 Nginx 服务器：

```bash
sudo apt-get install nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

新建 `/etc/nginx/conf.d/autogen.conf` 文件：

```nginx
server {
  listen 80;

  server_name autogen;

  location / {
    proxy_pass http://127.0.0.1:6001/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forward-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Nginx-Proxy true;
    proxy_redirect off;
  }
}
```

## 1.2 测试 API 接口

使用 Postman 连接下述地址：

```bash
ws://ai.xinqueyun.com/autogen/{chat_id}
# 其中 chat_id 用于标记一次聊天对话
```

然后向该地址发送 WebSocket 消息即可。
