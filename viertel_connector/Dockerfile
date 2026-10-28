# Works both as a Home Assistant add-on (BUILD_FROM = HA base image) and standalone.
ARG BUILD_FROM=python:3.12-alpine
FROM ${BUILD_FROM}
RUN command -v python3 >/dev/null || apk add --no-cache python3 py3-pip; \
    python3 -m pip install --no-cache-dir --break-system-packages requests==2.32.3 2>/dev/null \
    || python3 -m pip install --no-cache-dir requests==2.32.3
COPY viertel /app/viertel
WORKDIR /app
CMD ["python3", "-m", "viertel"]
