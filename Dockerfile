# MotionEngine REST service (FastAPI). Build: docker build -t motion-engine .
# Run:   docker run -p 8000:8000 -e MOTIONENGINE_API_KEY=change-me motion-engine
FROM python:3.12-slim AS build
WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY vdsim ./vdsim
RUN pip install --no-cache-dir --upgrade pip build && python -m build --wheel --outdir /dist

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    MOTIONENGINE_CONFIG_DIR=/app/configs \
    MOTIONENGINE_HOST=0.0.0.0 \
    MOTIONENGINE_PORT=8000
WORKDIR /app
COPY --from=build /dist/*.whl /tmp/
RUN pip install --no-cache-dir "$(ls /tmp/*.whl)[api]" && rm /tmp/*.whl \
    && useradd --create-home --uid 10001 motion
COPY configs ./configs
USER motion
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status != 200)"
CMD ["sh", "-c", "uvicorn vdsim.service.app:app --host ${MOTIONENGINE_HOST} --port ${MOTIONENGINE_PORT} --proxy-headers"]
