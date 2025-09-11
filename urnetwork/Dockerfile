ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.7
FROM ${BUILD_FROM}

# 設定環境變數
ENV LANG=C.UTF-8

# 安裝必要的套件
RUN apk add --no-cache \
    python3 \
    py3-pip \
    docker \
    docker-compose \
    curl \
    jq \
    bash

# 安裝 Python 依賴
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 複製檔案
COPY rootfs /

# 設定權限（修正權限問題）
RUN find /etc -name "*.sh" -type f -exec chmod +x {} \;
RUN find /etc/services.d -name "run" -type f -exec chmod +x {} \;
RUN find /etc/services.d -name "finish" -type f -exec chmod +x {} \;
RUN find /etc/cont-init.d -name "*.sh" -type f -exec chmod +x {} \;

# 建立配置目錄
RUN mkdir -p /addon_config/.urnetwork

# 建立標籤
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="URnetwork Team" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="URnetwork" \
    org.opencontainers.image.authors="URnetwork Team" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/urnetwork/addon" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}
