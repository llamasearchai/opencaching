PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN groupadd -r cacheuser && useradd -r -g cacheuser cacheuser

# Create application directory
WORKDIR /app

# Copy application code
COPY . .

# Install the application
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups && \
    chown -R cacheuser:cacheuser /app

# Switch to non-root user
USER cacheuser

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Default command
CMD ["caching-platform", "daemon", "--port", "8080"]