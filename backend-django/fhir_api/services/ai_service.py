"""
Serviço de IA para resumos clínicos usando Ollama.

INSTALAÇÃO:
1. Baixar Ollama: https://ollama.ai/download (Windows/Mac/Linux)
2. Instalar modelos:
   - ollama pull mistral      (Modelo geral, 4GB)
   - ollama pull medllama2    (Modelo médico, 3.8GB) - RECOMENDADO
3. Verificar: ollama list

COMPATIBILIDADE:
- HL7 FHIR R4: Sim (gera resumos de recursos FHIR)
- LGPD: Sim (100% local, sem envio de dados externos)
- Segurança: Dados nunca saem do servidor
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'mistral-nemo')  # mistral-nemo:latest instalado

class AIService:
    """
    Serviço centralizado para Inteligência Artificial.
    Usa Ollama + Mistral/Medllama2 rodando localmente.
    """

    def __init__(self, user=None):
        self.user = user

    def check_ollama_health(self):
        """Verifica se Ollama está rodando e modelos disponíveis."""
        try:
            print(f"🔍 Testando conexão Ollama em: {OLLAMA_BASE_URL}")
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
            print(f"🔍 Response status: {response.status_code}")
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                print(f"🔍 Modelos encontrados: {model_names}")
                
                # Check if preferred model exists (permite variações como mistral-nemo, mistral, etc)
                model_found = any(
                    OLLAMA_MODEL in name or name.startswith(OLLAMA_MODEL)
                    for name in model_names
                )
                
                if model_found:
                    logger.info(f"✅ Ollama OK | Modelo: {OLLAMA_MODEL} | Disponíveis: {model_names}")
                    print(f"✅ Modelo {OLLAMA_MODEL} ENCONTRADO!")
                    return True
                else:
                    logger.warning(f"⚠️ Modelo '{OLLAMA_MODEL}' não encontrado. Disponíveis: {model_names}")
                    logger.warning(f"💡 Execute: ollama pull {OLLAMA_MODEL}")
                    print(f"❌ Modelo {OLLAMA_MODEL} NÃO encontrado. Disponíveis: {model_names}")
                    return False
        except Exception as e:
            logger.warning(f"❌ Ollama não conectou: {e}")
            logger.warning("💡 Verifique se Ollama está rodando")
            logger.warning("💡 Windows: Abra o aplicativo Ollama")
            logger.warning("💡 Linux/Mac: ollama serve")
            print(f"❌ ERRO ao conectar Ollama: {e}")
        return False

    def generate_with_ollama(self, prompt, max_tokens=1000):
        """Gera texto usando Ollama API."""
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Erro ao chamar Ollama: {e}")
            return None

    def generate_patient_summary(self, patient_data):
        """
        Gera resumo clínico do paciente.
        Tenta Ollama primeiro, fallback para resumo estruturado.
        
        Returns:
            dict: {'summary': str, 'using_ai': bool}
        """
        name = patient_data.get('name', 'Paciente')
        age = patient_data.get('age', 'N/A')
        
        logger.warning(f"🔍 generate_patient_summary chamado para: {name}")
        
        # Try Ollama first
        logger.warning("🔍 Verificando saúde do Ollama...")
        ollama_ok = self.check_ollama_health()
        logger.warning(f"🔍 Ollama status: {ollama_ok}")
        
        if ollama_ok:
            logger.warning("🔍 Construindo prompt clínico...")
            prompt = self._build_clinical_prompt(patient_data)
            logger.warning(f"🔍 Prompt construído: {len(prompt)} chars")
            
            logger.warning("🔍 Chamando Ollama para gerar resumo...")
            ai_summary = self.generate_with_ollama(prompt, max_tokens=1200)
            logger.warning(f"🔍 Ollama retornou: {len(ai_summary) if ai_summary else 0} chars")
            
            if ai_summary:
                logger.info(f"🤖 Resumo gerado por IA (Ollama/{OLLAMA_MODEL}): {len(ai_summary)} chars")
                return {
                    'summary': ai_summary,
                    'using_ai': True
                }
        
        # Fallback: structured summary
        logger.info(f"📋 Usando resumo estruturado (fallback) para {name}")
        return {
            'summary': self._generate_structured_summary(patient_data),
            'using_ai': False
        }

    def _build_clinical_prompt(self, patient_data):
        """Constrói prompt médico para a IA."""
        name = patient_data.get('name', 'Paciente')
        age = patient_data.get('age', 'N/A')
        gender = patient_data.get('gender', 'N/A')
        
        conditions = patient_data.get('conditions', [])
        medications = patient_data.get('medications', [])
        vital_signs = patient_data.get('vital_signs', [])
        
        # Format conditions
        cond_list = []
        for c in conditions[:5]:
            display = c.get('display') or c.get('code', {}).get('text', 'N/A')
            cond_list.append(f"- {display}")
        cond_text = '\n'.join(cond_list) if cond_list else "Nenhum problema registrado"
        
        # Format medications
        med_list = []
        for m in medications[:5]:
            med_code = m.get('medicationCodeableConcept', {})
            display = med_code.get('text') or med_code.get('coding', [{}])[0].get('display', 'N/A')
            med_list.append(f"- {display}")
        med_text = '\n'.join(med_list) if med_list else "Nenhuma medicação registrada"
        
        # Format vital signs
        vs_list = []
        for v in vital_signs[:5]:
            code = v.get('code', {})
            display = code.get('text') or code.get('coding', [{}])[0].get('display', 'Sinal vital')
            value_qty = v.get('valueQuantity', {})
            value = value_qty.get('value', 'N/A')
            unit = value_qty.get('unit', '')
            vs_list.append(f"- {display}: {value} {unit}")
        vs_text = '\n'.join(vs_list) if vs_list else "Não disponíveis"
        
        prompt = f"""Você é um assistente médico especializado. Gere um resumo clínico profissional deste paciente.

**DADOS DO PACIENTE:**
Nome: {name}
Idade: {age} anos
Sexo: {gender}

**PROBLEMAS ATIVOS:**
{cond_text}

**MEDICAÇÕES ATUAIS:**
{med_text}

**SINAIS VITAIS RECENTES:**
{vs_text}

**INSTRUÇÕES:**
1. Gere um resumo clínico em português (PT-BR)
2. Use linguagem médica profissional mas clara
3. Destaque riscos clínicos importantes (ex: polifarmácia, comorbidades complexas)
4. Sugira 2-3 pontos de atenção para próxima consulta
5. Formato: parágrafos corridos (não use markdown ou listas)
6. Máximo 600 caracteres
7. Foco: resumo executivo para tomada de decisão clínica

Resumo clínico:"""
        
        return prompt

    def _generate_structured_summary(self, patient_data):
        """Gera resumo estruturado sem IA (fallback)."""
        name = patient_data.get('name', 'Paciente')
        age = patient_data.get('age', 'N/A')
        gender = patient_data.get('gender', 'N/A')
        
        conditions = patient_data.get('conditions', [])
        medications = patient_data.get('medications', [])
        vital_signs = patient_data.get('vital_signs', [])
        immunizations = patient_data.get('immunizations', [])
        diagnostic_reports = patient_data.get('diagnostic_reports', [])
        
        # Build markdown summary
        summary = []
        
        # Header
        summary.append(f"# 🎯 Resumo Clínico: {name}\n\n")
        summary.append(f"**Idade:** {age} anos | **Sexo:** {gender}\n\n")
        
        # Conditions
        if conditions:
            summary.append("## 🔴 Problemas Ativos\n\n")
            for c in conditions[:5]:
                display = c.get('display') or c.get('code', {}).get('text', 'Condição')
                status = c.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'active')
                summary.append(f"- {display} ({status})\n")
            summary.append("\n")  # Espaço extra após seção
        
        # Medications
        if medications:
            summary.append("## 💊 Medicações\n\n")
            for m in medications[:5]:
                med_code = m.get('medicationCodeableConcept', {})
                display = med_code.get('text') or med_code.get('coding', [{}])[0].get('display', 'Medicamento')
                summary.append(f"- {display}\n")
            
            if len(medications) >= 5:
                summary.append("\n⚠️ **Polifarmácia:** Revisar interações medicamentosas\n")
            summary.append("\n")  # Espaço extra após seção
        
        # Vital Signs
        if vital_signs:
            summary.append("## 🩺 Sinais Vitais Recentes\n\n")
            for v in vital_signs[:6]:
                code = v.get('code', {})
                display = code.get('text') or code.get('coding', [{}])[0].get('display', 'Sinal')
                value_qty = v.get('valueQuantity', {})
                value = value_qty.get('value', 'N/A')
                unit = value_qty.get('unit', '')
                date = v.get('effectiveDateTime', '')[:10]
                summary.append(f"- **{display}:** {value} {unit} ({date})\n")
            summary.append("\n")  # Espaço extra após seção
        
        # Clinical Analysis
        summary.append("## 📊 Análise Clínica\n\n")
        
        risk_level = "BAIXO"
        if len(conditions) > 3:
            risk_level = "MODERADO"
        if len(conditions) > 5:
            risk_level = "ALTO"
        
        summary.append(f"**Nível de Complexidade:** {risk_level}\n\n")
        summary.append(f"**Problemas ativos:** {len(conditions)}\n\n")
        summary.append(f"**Medicações:** {len(medications)}\n\n")
        
        # Recommendations
        summary.append("## 💡 Recomendações\n\n")
        if not vital_signs:
            summary.append("- Coletar sinais vitais na próxima consulta\n")
        if len(medications) > 5:
            summary.append("- Revisar esquema terapêutico (polifarmácia)\n")
        if not conditions and not medications:
            summary.append("- Completar anamnese e histórico clínico\n")
        
        summary.append("\n---\n\n")
        summary.append("*Resumo estruturado automático (HL7 FHIR R4)*\n")
        
        return ''.join(summary)

    def check_medication_interactions(self, medication_codes):
        """
        Verifica interações medicamentosas usando IA.
        Fallback: retorna análise básica.
        """
        if not medication_codes or len(medication_codes) < 2:
            return {
                "has_interactions": False,
                "severity": "none",
                "interactions": [],
                "recommendations": []
            }
        
        if self.check_ollama_health():
            prompt = f"""Você é um farmacêutico clínico. Analise possíveis interações medicamentosas entre:

{chr(10).join([f"- {code}" for code in medication_codes])}

Responda em JSON simples:
{{
    "has_interactions": true/false,
    "severity": "low/moderate/high",
    "interactions": ["descrição da interação"],
    "recommendations": ["recomendação clínica"]
}}

Análise JSON:"""
            
            result = self.generate_with_ollama(prompt, max_tokens=400)
            if result:
                try:
                    import json
                    # Extract JSON from response
                    json_start = result.find('{')
                    json_end = result.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = result[json_start:json_end]
                        return json.loads(json_str)
                except Exception as e:
                    logger.warning(f"Erro ao parsear JSON de interações: {e}")
        
        # Fallback
        return {
            "has_interactions": False,
            "severity": "unknown",
            "interactions": ["Análise de IA indisponível."],
            "recommendations": [
                "Consultar base de dados de interações medicamentosas",
                "Revisar com farmacêutico clínico se > 5 medicações"
            ]
        }
