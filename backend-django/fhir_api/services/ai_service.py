"""
Serviço de IA para resumos clínicos via servidor compatível com OpenAI
(open-source / self-hosted — vLLM em produção, Ollama em dev).

Princípios:
- APOIO À DECISÃO: a IA organiza e resume; o médico decide (exigência do CFM).
- LGPD by design: PII é redigida antes do envio; o modelo roda no seu ambiente.
- Fallback determinístico (resumo estruturado) quando a IA não está disponível.
"""

import logging
from core.services import llm_client

logger = logging.getLogger(__name__)


class AIService:
    """Apoio à decisão clínica usando LLM open-source self-hosted."""

    def __init__(self, user=None):
        self.user = user

    def _generate(self, prompt, max_tokens=1000, json_mode=False):
        """Redige PII e chama o LLM com o system prompt de apoio à decisão."""
        safe_prompt = llm_client.redact_pii(prompt)
        return llm_client.chat(
            [
                {"role": "system", "content": llm_client.DEFAULT_CLINICAL_SYSTEM},
                {"role": "user", "content": safe_prompt},
            ],
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

    def generate_patient_summary(self, patient_data):
        """
        Gera resumo clínico do paciente (apoio à decisão).

        Returns:
            dict: {'summary': str, 'using_ai': bool}
        """
        name = patient_data.get("name", "Paciente")

        if llm_client.available():
            summary = self._generate(self._build_clinical_prompt(patient_data), max_tokens=1200)
            if summary:
                logger.info(f"Resumo gerado por IA (self-hosted): {len(summary)} chars")
                return {"summary": summary, "using_ai": True}

        logger.info(f"Usando resumo estruturado (fallback) para {name}")
        return {"summary": self._generate_structured_summary(patient_data), "using_ai": False}

    def _build_clinical_prompt(self, patient_data):
        """Constrói prompt médico para a IA."""
        name = patient_data.get("name", "Paciente")
        age = patient_data.get("age", "N/A")
        gender = patient_data.get("gender", "N/A")

        conditions = patient_data.get("conditions", [])
        medications = patient_data.get("medications", [])
        vital_signs = patient_data.get("vital_signs", [])

        cond_list = []
        for c in conditions[:5]:
            display = c.get("display") or c.get("code", {}).get("text", "N/A")
            cond_list.append(f"- {display}")
        cond_text = "\n".join(cond_list) if cond_list else "Nenhum problema registrado"

        med_list = []
        for m in medications[:5]:
            med_code = m.get("medicationCodeableConcept", {})
            display = med_code.get("text") or med_code.get("coding", [{}])[0].get("display", "N/A")
            med_list.append(f"- {display}")
        med_text = "\n".join(med_list) if med_list else "Nenhuma medicação registrada"

        vs_list = []
        for v in vital_signs[:5]:
            code = v.get("code", {})
            display = code.get("text") or code.get("coding", [{}])[0].get("display", "Sinal vital")
            value_qty = v.get("valueQuantity", {})
            value = value_qty.get("value", "N/A")
            unit = value_qty.get("unit", "")
            vs_list.append(f"- {display}: {value} {unit}")
        vs_text = "\n".join(vs_list) if vs_list else "Não disponíveis"

        return f"""Gere um resumo clínico profissional (apoio à decisão) deste paciente.

**DADOS DO PACIENTE:**
Idade: {age} anos
Sexo: {gender}

**PROBLEMAS ATIVOS:**
{cond_text}

**MEDICAÇÕES ATUAIS:**
{med_text}

**SINAIS VITAIS RECENTES:**
{vs_text}

**INSTRUÇÕES:**
1. Resumo clínico em português (PT-BR), linguagem médica clara.
2. Destaque riscos relevantes (ex.: polifarmácia, comorbidades).
3. Sugira 2-3 pontos de atenção para a próxima consulta.
4. Parágrafos corridos, máximo 600 caracteres.
5. Lembre que esta é uma ferramenta de apoio; a decisão é do profissional.

Resumo clínico:"""

    def _generate_structured_summary(self, patient_data):
        """Gera resumo estruturado sem IA (fallback determinístico)."""
        name = patient_data.get("name", "Paciente")
        age = patient_data.get("age", "N/A")
        gender = patient_data.get("gender", "N/A")

        conditions = patient_data.get("conditions", [])
        medications = patient_data.get("medications", [])
        vital_signs = patient_data.get("vital_signs", [])

        summary = []
        summary.append(f"# Resumo Clínico: {name}\n\n")
        summary.append(f"**Idade:** {age} anos | **Sexo:** {gender}\n\n")

        if conditions:
            summary.append("## Problemas Ativos\n\n")
            for c in conditions[:5]:
                display = c.get("display") or c.get("code", {}).get("text", "Condição")
                status = c.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "active")
                summary.append(f"- {display} ({status})\n")
            summary.append("\n")

        if medications:
            summary.append("## Medicações\n\n")
            for m in medications[:5]:
                med_code = m.get("medicationCodeableConcept", {})
                display = med_code.get("text") or med_code.get("coding", [{}])[0].get("display", "Medicamento")
                summary.append(f"- {display}\n")
            if len(medications) >= 5:
                summary.append("\n**Polifarmácia:** revisar interações medicamentosas\n")
            summary.append("\n")

        if vital_signs:
            summary.append("## Sinais Vitais Recentes\n\n")
            for v in vital_signs[:6]:
                code = v.get("code", {})
                display = code.get("text") or code.get("coding", [{}])[0].get("display", "Sinal")
                value_qty = v.get("valueQuantity", {})
                value = value_qty.get("value", "N/A")
                unit = value_qty.get("unit", "")
                date = v.get("effectiveDateTime", "")[:10]
                summary.append(f"- **{display}:** {value} {unit} ({date})\n")
            summary.append("\n")

        summary.append("## Análise\n\n")
        risk_level = "BAIXO"
        if len(conditions) > 3:
            risk_level = "MODERADO"
        if len(conditions) > 5:
            risk_level = "ALTO"
        summary.append(f"**Nível de Complexidade:** {risk_level}\n\n")
        summary.append(f"**Problemas ativos:** {len(conditions)}\n\n")
        summary.append(f"**Medicações:** {len(medications)}\n\n")

        summary.append("## Recomendações\n\n")
        if not vital_signs:
            summary.append("- Coletar sinais vitais na próxima consulta\n")
        if len(medications) > 5:
            summary.append("- Revisar esquema terapêutico (polifarmácia)\n")
        if not conditions and not medications:
            summary.append("- Completar anamnese e histórico clínico\n")

        summary.append("\n---\n\n*Resumo estruturado automático (HL7 FHIR R4)*\n")
        return "".join(summary)

    def check_medication_interactions(self, medication_codes):
        """
        Verifica interações medicamentosas (apoio à decisão).
        Fallback: análise básica quando a IA não está disponível.
        """
        if not medication_codes or len(medication_codes) < 2:
            return {"has_interactions": False, "severity": "none", "interactions": [], "recommendations": []}

        if llm_client.available():
            prompt = (
                "Analise possíveis interações medicamentosas entre os itens a seguir. "
                "Responda em JSON com as chaves has_interactions (bool), severity "
                "(low/moderate/high), interactions (lista), recommendations (lista):\n"
                + "\n".join([f"- {code}" for code in medication_codes])
            )
            result = self._generate(prompt, max_tokens=500, json_mode=True)
            if result:
                try:
                    import json
                    return json.loads(result)
                except Exception as e:
                    logger.warning(f"Erro ao parsear JSON de interações: {e}")

        return {
            "has_interactions": False,
            "severity": "unknown",
            "interactions": ["Análise de IA indisponível."],
            "recommendations": [
                "Consultar base de dados de interações medicamentosas",
                "Revisar com farmacêutico clínico se > 5 medicações",
            ],
        }
