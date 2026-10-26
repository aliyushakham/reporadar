FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY reporadar ./reporadar
COPY examples ./examples
RUN pip install --no-cache-dir . && useradd --create-home radar && mkdir /data && chown radar:radar /data
USER radar
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health')"
ENTRYPOINT ["python", "-m", "reporadar", "--db", "/data/index.sqlite", "serve"]
CMD ["/app/examples/shop", "--host", "0.0.0.0"]
