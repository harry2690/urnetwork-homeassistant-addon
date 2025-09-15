ARG BUILD_FROM
FROM $BUILD_FROM

# 安裝必要套件
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    bash \
    jq \
    docker-cli

# 安裝 Python 依賴
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# 只複製 URnetwork 執行檔（關鍵！）
COPY rootfs/usr/local/bin/ /usr/local/bin/

# 複製應用程式檔案
COPY rootfs/opt/urnetwork/app.py /app/
COPY rootfs/opt/urnetwork/utils/ /app/utils/
COPY rootfs/opt/urnetwork/templates/ /app/templates/

# 設定執行權限
RUN chmod +x /usr/local/bin/* 2>/dev/null || true
RUN chmod +x /app/app.py

# 建立必要目錄
RUN mkdir -p /addon_config/.urnetwork /data

# 設定工作目錄
WORKDIR /app

# 直接執行 Python（application 模式）
ENTRYPOINT []
CMD ["python3", "/app/app.py"]
