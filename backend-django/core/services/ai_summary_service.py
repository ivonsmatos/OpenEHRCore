import logging
import requests
from decouple import config
from django.conf import settings

logger = logging.getLogger(__name__)


class AISummaryService:
    """
    AI Summary Service using Groq's Llama 3.3 70B.
    Generates intelligent clinical summaries from FHIR patient data.
    """
    _instance = None
    
    # Groq API configuration
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_API_KEY = config('GROQ_API_KEY', default='')
    MODEL = "llama-3.3-70b-versatile"  # Llama 3.3 70B - great quality/cost balance
    
    # FHIR server
    FHIR_BASE_URL = config('FHIR_SERVER_URL', default='http://localhost:8080/fhir')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AISummaryService, cls).__new__(cls)
        return cls._instance

    def _fetch_fhir_data(self, patient_id: str) -> dict:
        """
        Fetches patient data from FHIR server.
        Returns conditions, medications, observations, allergies.
        """
        data = {
            'patient': None,
            'conditions': [],
            'medications': [],
            'observations': [],
            'allergies': []
        }
        
        try:
            # Fetch Patient
            resp = requests.get(f"{self.FHIR_BASE_URL}/Patient/{patient_id}", timeout=10)
            if resp.status_code == 200:
                data['patient'] = resp.json()
            
            # Fetch Conditions (active problems)
            resp = requests.get(
                f"{self.FHIR_BASE_URL}/Condition",
                params={'patient': patient_id, '_count': 50},
                timeout=10
            )
            if resp.status_code == 200:
                bundle = resp.json()
                data['conditions'] = [e.get('resource', {}) for e in bundle.get('entry', [])]
            
            # Fetch MedicationRequests (current medications)
            resp = requests.get(
                f"{self.FHIR_BASE_URL}/MedicationRequest",
                params={'patient': patient_id, 'status': 'active', '_count': 50},
                timeout=10
            )
            if resp.status_code == 200:
                bundle = resp.json()
                data['medications'] = [e.get('resource', {}) for e in bundle.get('entry', [])]
            
            # Fetch recent Observations (vitals, labs)
            resp = requests.get(
                f"{self.FHIR_BASE_URL}/Observation",
                params={'patient': patient_id, '_count': 20, '_sort': '-date'},
                timeout=10
            )
            if resp.status_code == 200:
                bundle = resp.json()
                data['observations'] = [e.get('resource', {}) for e in bundle.get('entry', [])]
            
            # Fetch Allergies
            resp = requests.get(
                f"{self.FHIR_BASE_URL}/AllergyIntolerance",
                params={'patient': patient_id, '_count': 20},
                timeout=10
            )
            if resp.status_code == 200:
                bundle = resp.json()
                data['allergies'] = [e.get('resource', {}) for e in bundle.get('entry', [])]
                
        except Exception as e:
            logger.error(f"Error fetching FHIR data: {str(e)}")
        
        return data

    def _build_clinical_context(self, fhir_data: dict) -> str:
        """
        Builds a clinical context string from FHIR data for the LLM.
        """
        lines = []
        
        # Patient info
        patient = fhir_data.get('patient', {})
        if patient:
            name = patient.get('name', [{}])[0]
            full_name = f"{' '.join(name.get('given', []))} {name.get('family', '')}"
            gender = patient.get('gender', 'unknown')
            birth_date = patient.get('birthDate', 'unknown')
            lines.append(f"Paciente: {full_name}, Sexo: {gender}, Nascimento: {birth_date}")
        
        # Conditions
        conditions = fhir_data.get('conditions', [])
        if conditions:
            lines.append(f"\nProblemas/Condições ({len(conditions)}):")
            for c in conditions[:10]:
                code = c.get('code', {}).get('coding', [{}])[0]
                display = code.get('display', c.get('code', {}).get('text', 'Não especificado'))
                status = c.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '')
                lines.append(f"  - {display} (status: {status})")
        else:
            lines.append("\nProblemas/Condições: Nenhum registrado")
        
        # Medications
        medications = fhir_data.get('medications', [])
        if medications:
            lines.append(f"\nMedicações Ativas ({len(medications)}):")
            for m in medications[:10]:
                med = m.get('medicationCodeableConcept', {})
                display = med.get('coding', [{}])[0].get('display', med.get('text', 'Não especificado'))
                lines.append(f"  - {display}")
        else:
            lines.append("\nMedicações Ativas: Nenhuma registrada")
        
        # Recent observations
        observations = fhir_data.get('observations', [])
        if observations:
            lines.append(f"\nObservações Recentes ({len(observations)}):")
            for o in observations[:5]:
                code = o.get('code', {}).get('coding', [{}])[0]
                display = code.get('display', 'Observação')
                value = o.get('valueQuantity', {})
                if value:
                    val_str = f"{value.get('value', '')} {value.get('unit', '')}"
                else:
                    val_str = o.get('valueString', 'N/A')
                lines.append(f"  - {display}: {val_str}")
        
        # Allergies
        allergies = fhir_data.get('allergies', [])
        if allergies:
            lines.append(f"\nAlergias ({len(allergies)}):")
            for a in allergies[:5]:
                code = a.get('code', {}).get('coding', [{}])[0]
                display = code.get('display', a.get('code', {}).get('text', 'Alergia'))
                lines.append(f"  - {display}")
        else:
            lines.append("\nAlergias: Nenhuma registrada")
        
        return "\n".join(lines)

    def generate_patient_summary(self, patient_id: str) -> dict:
        """
        Generates an intelligent clinical summary for a patient.
        
        Returns:
            dict with: complexity_level, active_problems_count, medications_count,
                       recommendations, summary_text
        """
        if not self.GROQ_API_KEY:
            logger.error("GROQ_API_KEY not configured")
            return self._empty_summary("API não configurada")
        
        # Fetch FHIR data
        fhir_data = self._fetch_fhir_data(patient_id)
        
        # Build clinical context
        clinical_context = self._build_clinical_context(fhir_data)
        
        # Create prompt for Llama
        system_prompt = """Você é um assistente médico especializado em análise de prontuários eletrônicos.
Analise os dados clínicos do paciente e forneça um resumo estruturado em formato JSON.

Responda APENAS com JSON válido no seguinte formato:
{
    "complexity_level": "BAIXO" ou "MÉDIO" ou "ALTO" ou "CRÍTICO",
    "active_problems_summary": "Resumo dos problemas ativos em 1-2 frases",
    "medication_alerts": "Alertas sobre medicações (interações, duplicidades) ou 'Sem alertas'",
    "recommendations": [
        "Recomendação 1",
        "Recomendação 2",
        "Recomendação 3"
    ],
    "clinical_summary": "Resumo clínico geral em 2-3 frases"
}

Critérios de complexidade:
- BAIXO: Poucos ou nenhum problema ativo, medicações simples
- MÉDIO: Algumas condições crônicas controladas, politerapia moderada
- ALTO: Múltiplas comorbidades, polifarmácia, condições não controladas
- CRÍTICO: Condições graves, alto risco, necessita atenção imediata"""

        user_prompt = f"""Analise os dados clínicos deste paciente e gere o resumo estruturado:

{clinical_context}

Responda APENAS com o JSON estruturado, sem explicações adicionais."""

        try:
            headers = {
                "Authorization": f"Bearer {self.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,  # Lower for more consistent outputs
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                self.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                import json
                summary_data = json.loads(content)
                
                # Build final response
                return {
                    'complexity_level': summary_data.get('complexity_level', 'BAIXO'),
                    'active_problems_count': len(fhir_data.get('conditions', [])),
                    'medications_count': len(fhir_data.get('medications', [])),
                    'active_problems_summary': summary_data.get('active_problems_summary', ''),
                    'medication_alerts': summary_data.get('medication_alerts', 'Sem alertas'),
                    'recommendations': summary_data.get('recommendations', []),
                    'clinical_summary': summary_data.get('clinical_summary', ''),
                    'allergies_count': len(fhir_data.get('allergies', [])),
                    'source': 'AI (Llama 3.3 70B via Groq)'
                }
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return self._empty_summary(f"Erro na API: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return self._empty_summary(str(e))

    def _empty_summary(self, error_msg: str = "") -> dict:
        """Returns an empty summary structure."""
        return {
            'complexity_level': 'BAIXO',
            'active_problems_count': 0,
            'medications_count': 0,
            'active_problems_summary': '',
            'medication_alerts': '',
            'recommendations': [
                'Coletar sinais vitais na próxima consulta',
                'Completar anamnese e histórico clínico'
            ],
            'clinical_summary': error_msg or 'Dados insuficientes para análise',
            'allergies_count': 0,
            'source': 'fallback'
        }
