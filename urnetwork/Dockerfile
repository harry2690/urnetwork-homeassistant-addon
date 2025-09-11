ARG BUILD_FROM
FROM $BUILD_FROM

# 安裝必要套件
RUN apk add --no-cache python3 py3-pip curl bash

# 安裝 Python 依賴（使用 --break-system-packages 繞過 PEP 668）
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# 複製檔案
COPY rootfs /

# 設定權限
RUN chmod a+x /etc/services.d/webui/run \
    && chmod a+x /etc/services.d/webui/finish

# 建立目錄
RUN mkdir -p /addon_config/.urnetwork
