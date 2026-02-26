# backend/tests/test_embeddings.py

import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from fastapi import status
from backend.app.main import app
from backend.app.application.embeddings_service import EmbeddingsService
from backend.app.infrastructure.gemini_client import GeminiClient
from backend.app.application.indices_vectoriales import embedding_index

# --- Fixtures ---

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def test_texts():
    return [
        "Hola mundo",
        "Este es un texto de prueba",
        "FastAPI y embeddings con Gemini"
    ]

# Fixture para servicio de embeddings real o mock
@pytest.fixture
def embeddings_service():
    client = GeminiClient(api_key="TEST_API_KEY")  # Reemplazar por ENV real si se desea
    return EmbeddingsService(client=client, index=embedding_index)

# --- Tests Unitarios ---

@pytest.mark.asyncio
async def test_generar_embedding(embeddings_service, test_texts):
    """
    Verifica que el servicio genere vectores de embedding con la longitud correcta
    """
    for texto in test_texts:
        vector = await embeddings_service.generar_embedding(texto)
        assert isinstance(vector, list)
        assert all(isinstance(x, float) for x in vector)
        assert len(vector) > 0

@pytest.mark.asyncio
async def test_agregar_y_buscar_en_index(embeddings_service):
    """
    Agrega vectores al índice local y verifica búsqueda de similitud
    """
    texto = "Prueba de embeddings"
    vector = await embeddings_service.generar_embedding(texto)
    vector_id = str(uuid4())
    embedding_index.add_vector(vector_id, vector, {"texto": texto})

    resultados = embedding_index.search_similar(vector, top_k=1)
    assert resultados
    assert resultados[0][0] == vector_id
    assert resultados[0][1] > 0.9  # Esperamos alta similitud exacta

@pytest.mark.asyncio
async def test_endpoint_embeddings(async_client):
    """
    Testea el endpoint /embeddings que reciba un texto y devuelva vector
    """
    payload = {"texto": "Test endpoint embeddings"}
    response = await async_client.post("/embeddings", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "vector" in data
    assert isinstance(data["vector"], list)
    assert all(isinstance(x, float) for x in data["vector"])

@pytest.mark.asyncio
async def test_busqueda_similar_endpoint(async_client):
    """
    Agrega un vector al index y luego prueba búsqueda desde endpoint
    """
    texto = "Texto para buscar similar"
    vector_id = str(uuid4())
    vector = [0.1, 0.2, 0.3, 0.4]  # Mock simple para test
    embedding_index.add_vector(vector_id, vector, {"texto": texto})

    payload = {"vector": vector, "top_k": 1}
    response = await async_client.post("/embeddings/search", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == vector_id
    assert data[0]["similarity"] > 0


