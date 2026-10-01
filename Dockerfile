FROM python:3.11-slim-bookworm

# Copy the uv installer from its official image (faster than pip).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Apply OS security updates, then install the system packages that torch and other libraries need.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies in their own layer, so Docker can reuse it when only the code changes.
# The dependency list is read from pyproject.toml without copying the source code.
COPY pyproject.toml .
RUN python3 -c "import tomllib,subprocess; deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; subprocess.run(['uv','pip','install','--system','--no-cache']+deps,check=True)"

# Copy the source code (this layer is rebuilt only when the code changes).
COPY app/ ./app/
COPY ui/ ./ui/

# The API listens on port 8080.
EXPOSE 8080

# Run as a normal user instead of root, for security.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-graceful-shutdown", "5"]
