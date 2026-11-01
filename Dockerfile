# 基础镜像：Python 3.10 精简版（slim 体积小）
FROM python:3.10-slim
# 设定容器内工作目录为 /app，后续 COPY/RUN/CMD 都以此为基准
WORKDIR /app
# 先拷依赖清单、后拷代码：改代码只动最后几层，依赖层可复用 Docker 缓存、不必重装
COPY requirements.txt .
# 安装依赖：--no-cache-dir 不缓存安装包减小镜像；-i 指定清华 PyPI 镜像加速
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
# 拷贝应用代码（app 包）进容器
COPY app ./app
# 声明容器对外暴露 8000 端口（uvicorn 监听端口）
EXPOSE 8000
# --host 0.0.0.0：容器内默认只听 127.0.0.1，改成 0.0.0.0 才能让宿主机连进来
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
