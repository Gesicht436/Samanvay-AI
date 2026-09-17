FROM python:3.14-slim

RUN pip install uv

WORKDIR /app
COPY pyproject.toml .
# Install specific ML dependencies
RUN uv pip install --system onnxruntime paddleocr PyMuPDF fastapi uvicorn pydantic || echo "Some ML dependencies failed to install"

COPY ml/ ./ml/
COPY backend/ ./backend/

EXPOSE 8001
CMD ["uvicorn", "ml.main:app", "--host", "0.0.0.0", "--port", "8001"]
