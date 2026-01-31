"""
Testes unitários para a API FastAPI - SmartRx AI
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas import PrescriptionRequest, PrescriptionResponse


@pytest.fixture
def mock_rag_service():
    """Mock do RAG Service para testes"""
    mock = MagicMock()
    # Injeta o mock no módulo main
    with patch('backend.main.rag_service', mock):
        yield mock


@pytest.fixture
def client(mock_rag_service):
    """Cliente de teste para a API"""
    # O mock já está injetado via patch no mock_rag_service
    return TestClient(app)


class TestHealthEndpoints:
    """Testes para endpoints de health check"""
    
    def test_root_endpoint(self, client):
        """Testa o endpoint raiz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SmartRx AI API"
        assert data["status"] == "online"
    
    def test_health_check(self, client):
        """Testa o endpoint de health check"""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # Pode estar unavailable se RAG não inicializado


class TestPrescribeEndpoint:
    """Testes para o endpoint de prescrição"""
    
    def test_prescribe_success(self, client, mock_rag_service):
        """Testa prescrição bem-sucedida"""
        # Mock da resposta do RAG service
        mock_prescription = {
            "medicamentos": [
                {
                    "nome": "Amoxicilina",
                    "principio_ativo": "Amoxicilina",
                    "forma": "Cápsula",
                    "concentracao": "500mg",
                    "posologia": "1 cápsula",
                    "via": "Oral",
                    "frequencia": "A cada 8 horas",
                    "duracao": "10 dias",
                    "observacoes": "Tomar após refeições"
                }
            ],
            "resumo_tecnico_medico": [
                "Tratamento de primeira linha para amigdalite bacteriana",
                "Antibiótico de amplo espectro"
            ],
            "orientacoes_ao_paciente": [
                "Completar o tratamento mesmo com melhora dos sintomas",
                "Retornar se não houver melhora em 48-72h"
            ],
            "alertas_seguranca": [
                "Não exceder a dosagem prescrita"
            ],
            "monitorizacao": [
                "Avaliar resposta ao tratamento em 48-72h"
            ],
            "fontes": [
                {
                    "source_id": "pcdt_amigdalite_001",
                    "source_type": "OFFICIAL_PROTOCOL",
                    "title": "PCDT - Amigdalite Bacteriana",
                    "confidence_score": 0.85
                }
            ],
            "confidence_score": 0.85
        }
        
        # Configura o mock
        mock_rag_service.prescribe.return_value = mock_prescription
        
        # Faz a requisição
        request_data = {
            "symptoms": "Dor de garganta",
            "diagnosis": "Amigdalite bacteriana"
        }
        
        response = client.post("/api/v1/prescribe", json=request_data)
        
        # Verifica resposta
        assert response.status_code == 200
        data = response.json()
        
        # Valida estrutura da resposta
        assert "medicamentos" in data
        assert len(data["medicamentos"]) > 0
        assert data["medicamentos"][0]["nome"] == "Amoxicilina"
        assert "fontes" in data
        assert len(data["fontes"]) > 0
        assert data["fontes"][0]["source_type"] == "OFFICIAL_PROTOCOL"
        
        # Verifica que o RAG service foi chamado corretamente
        mock_rag_service.prescribe.assert_called_once_with(
            symptoms="Dor de garganta",
            diagnosis="Amigdalite bacteriana"
        )
    
    def test_prescribe_without_diagnosis(self, client, mock_rag_service):
        """Testa prescrição apenas com sintomas (sem diagnóstico)"""
        mock_prescription = {
            "medicamentos": [
                {
                    "nome": "Dipirona",
                    "principio_ativo": "Dipirona",
                    "forma": "Comprimido",
                    "concentracao": "1g",
                    "posologia": "1 comprimido",
                    "via": "Oral",
                    "frequencia": "A cada 6-8 horas",
                    "duracao": "5 dias",
                    "observacoes": None
                }
            ],
            "resumo_tecnico_medico": ["Analgésico e antitérmico"],
            "orientacoes_ao_paciente": ["Tomar com água"],
            "alertas_seguranca": [],
            "monitorizacao": [],
            "fontes": [
                {
                    "source_id": "bula_dipirona_1g_001",
                    "source_type": "DRUG_LEAFLET",
                    "title": "Bula - Dipirona 1g",
                    "confidence_score": 0.75
                }
            ],
            "confidence_score": 0.75
        }
        
        mock_rag_service.prescribe.return_value = mock_prescription
        
        request_data = {
            "symptoms": "Dor de cabeça e febre"
        }
        
        response = client.post("/api/v1/prescribe", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["medicamentos"]) > 0
        assert data["medicamentos"][0]["nome"] == "Dipirona"
        
        # Verifica que foi chamado com diagnosis=None
        mock_rag_service.prescribe.assert_called_once_with(
            symptoms="Dor de cabeça e febre",
            diagnosis=None
        )
    
    def test_prescribe_insufficient_context(self, client, mock_rag_service):
        """Testa erro quando não há contexto suficiente"""
        # Simula erro de valor (não encontrou documentos)
        mock_rag_service.prescribe.side_effect = ValueError(
            "Não foram encontrados protocolos clínicos suficientes para gerar a prescrição. "
            "Sistema em modo manual."
        )
        
        request_data = {
            "symptoms": "Sintoma muito específico e raro"
        }
        
        response = client.post("/api/v1/prescribe", json=request_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "protocolos clínicos" in data["detail"].lower()
    
    def test_prescribe_invalid_request(self, client):
        """Testa requisição inválida (sintomas muito curtos)"""
        request_data = {
            "symptoms": "AB"  # Muito curto (min_length=3)
        }
        
        response = client.post("/api/v1/prescribe", json=request_data)
        
        assert response.status_code == 422
    
    def test_prescribe_service_unavailable(self, client):
        """Testa quando o serviço RAG não está disponível"""
        # Simula RAG service não inicializado
        with patch('backend.main.rag_service', None):
            request_data = {
                "symptoms": "Dor de garganta"
            }
            
            response = client.post("/api/v1/prescribe", json=request_data)
            
            assert response.status_code == 503
            data = response.json()
            assert "não disponível" in data["detail"].lower()
    
    def test_prescribe_internal_error(self, client, mock_rag_service):
        """Testa erro interno do servidor"""
        # Simula erro genérico
        mock_rag_service.prescribe.side_effect = Exception("Erro interno")
        
        request_data = {
            "symptoms": "Dor de garganta"
        }
        
        response = client.post("/api/v1/prescribe", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestSchemas:
    """Testes para os schemas Pydantic"""
    
    def test_prescription_request_valid(self):
        """Testa schema de requisição válido"""
        request = PrescriptionRequest(
            symptoms="Dor de garganta e febre",
            diagnosis="Amigdalite"
        )
        assert request.symptoms == "Dor de garganta e febre"
        assert request.diagnosis == "Amigdalite"
    
    def test_prescription_request_without_diagnosis(self):
        """Testa schema de requisição sem diagnóstico"""
        request = PrescriptionRequest(symptoms="Dor de cabeça")
        assert request.symptoms == "Dor de cabeça"
        assert request.diagnosis is None
    
    def test_prescription_request_invalid(self):
        """Testa schema de requisição inválido"""
        with pytest.raises(Exception):  # Pydantic validation error
            PrescriptionRequest(symptoms="AB")  # Muito curto
    
    def test_prescription_response_structure(self):
        """Testa estrutura do schema de resposta"""
        response = PrescriptionResponse(
            medicamentos=[
                {
                    "nome": "Amoxicilina",
                    "principio_ativo": "Amoxicilina",
                    "forma": "Cápsula",
                    "concentracao": "500mg",
                    "posologia": "1 cápsula",
                    "via": "Oral",
                    "frequencia": "A cada 8 horas",
                    "duracao": "10 dias",
                    "observacoes": None
                }
            ],
            resumo_tecnico_medico=["Tratamento de primeira linha"],
            orientacoes_ao_paciente=["Completar tratamento"],
            alertas_seguranca=[],
            monitorizacao=[],
            fontes=[
                {
                    "source_id": "pcdt_001",
                    "source_type": "OFFICIAL_PROTOCOL",
                    "title": "PCDT - Amigdalite",
                    "confidence_score": 0.85
                }
            ],
            confidence_score=0.85
        )
        
        assert len(response.medicamentos) == 1
        assert response.medicamentos[0].nome == "Amoxicilina"
        assert len(response.fontes) == 1
        assert response.fontes[0].source_type == "OFFICIAL_PROTOCOL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
