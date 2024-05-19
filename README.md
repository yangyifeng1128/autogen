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

启动服务器：

```bash
(autogen) mkdir /root/logs/autogen
(autogen) touch /root/logs/autogen/access.log
(autogen) nohup uvicorn app.main:app --host 0.0.0.0 --port 6100 > /root/logs/autogen/access.log 2>&1 &
```
