import json
from backend.app.infrastructure.gemini_client import _extract_classification_text_for_json


def test_extract_classification_text_simple_json():
    data = {
        "candidates": [
            {"content": {"parts": [{"text": '{"category": "soporte", "priority": 5, "customer_name": "Carlos", "brief_summary": "Servidor no enciende"}'}]}}
        ]
    }
    extracted = _extract_classification_text_for_json(data)
    assert extracted == '{"category": "soporte", "priority": 5, "customer_name": "Carlos", "brief_summary": "Servidor no enciende"}'


def test_extract_classification_text_json_block_in_fence():
    data = {
        "candidates": [
            {"content": {"parts": [
                {"text": 'Some intro\n```json\n{"category":"ventas","priority":4,"customer_name":"Carlos","brief_summary":"Prueba"}\n```'}
            }]}
        ]
    }
    extracted = _extract_classification_text_for_json(data)
    assert extracted == '{"category":"ventas","priority":4,"customer_name":"Carlos","brief_summary":"Prueba"}'
