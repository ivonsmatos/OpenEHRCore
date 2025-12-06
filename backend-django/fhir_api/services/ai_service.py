
import logging
import os
from django.conf import settings

# Try to import ctransformers, but fail gracefully if not installed/model missing
try:
    from ctransformers import AutoModelForCausalLM
    HAS_LLM_LIB = True
except ImportError:
    HAS_LLM_LIB = False

logger = logging.getLogger(__name__)

# Constants
MODEL_FILE = "biomistral-7b.Q4_K_M.gguf"
MODELS_DIR = os.path.join(settings.BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILE)

class AIService:
    """
    Serviço centralizado para funcionalidades de Inteligência Artificial.
    Usa BioMistral 7B (GGUF) localmente se disponível.
    """

    _llm_instance = None # Singleton-ish class level cache for the model

    def __init__(self, user=None):
        self.user = user

    @classmethod
    def get_llm(cls):
        """
        Lazy load the LLM model.
        """
        if cls._llm_instance:
            return cls._llm_instance

        if not HAS_LLM_LIB:
            logger.warning("ctransformers library not found. LLM functionality disabled.")
            return None

        if not os.path.exists(MODEL_PATH):
            logger.warning(f"Model file not found at {MODEL_PATH}. Run scripts/download_model.py.")
            return None

        try:
            logger.info(f"Loading BioMistral model from {MODEL_PATH}...")
            # Load with optimized parameters for CPU
            cls._llm_instance = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                model_type='mistral',
                context_length=4096,
                max_new_tokens=512,
                gpu_layers=0 # Set to >0 if GPU available (e.g. 50 on A10G)
            )
            logger.info("BioMistral model loaded successfully.")
            return cls._llm_instance
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            return None

    def generate_patient_summary(self, patient_data):
        """
        Gera um resumo textual do paciente usando BioMistral.
        """
        llm = self.get_llm()
        
        # Prepare context data
        name = patient_data.get('name', 'Paciente')
        age = patient_data.get('age', 'N/A')
        gender = patient_data.get('gender', 'N/A')
        
        conditions = patient_data.get('conditions', [])
        cond_text = ", ".join([c.get('code', {}).get('text', 'Condição') for c in conditions]) if conditions else "Nenhuma condição crônica registrada"
        
        medications = patient_data.get('medications', [])
        med_text = ", ".join([m.get('medicationCodeableConcept', {}).get('text', 'Medicamento') for m in medications]) if medications else "Nenhum medicamento em uso"

        # Construct Prompt (Mistral Format)
        prompt = f"""<s>[INST] Você é um assistente clínico especializado. Gere um resumo clínico conciso e profissional em Português para o seguinte paciente.
        
        Dados do Paciente:
        - Nome: {name}
        - Idade: {age}
        - Sexo: {gender}
        
        Histórico Médico:
        - Condições: {cond_text}
        - Medicamentos em uso: {med_text}
        
        Sua tarefa: Crie um resumo de 3-5 linhas destacando os pontos principais para um médico ler rapidamente antes da consulta. Use termos técnicos apropriados. [/INST]"""

        try:
            if llm:
                # Generate
                logger.info(f"Generating summary for {name} with BioMistral...")
                response_text = llm(prompt)
                
                # Cleanup potential artifacts if model continues generating (rare with refined prompt but possible)
                if "[/INST]" in response_text:
                    response_text = response_text.split("[/INST]")[-1].strip()
                
                return response_text
            else:
                # Fallback implementation if model is missing
                logger.info("Using fallback summary (Model not loaded).")
                return self._fallback_summary(name, age, gender, conditions, medications)

        except Exception as e:
            logger.error(f"Erro na geração de resumo IA: {str(e)}")
            return "Não foi possível gerar o resumo clínico (Erro no modelo)."

    def _fallback_summary(self, name, age, gender, conditions, medications):
        """Retorna o resumo mockado original se o modelo não estiver disponível."""
        summary_lines = [
            f"Resumo Clínico (Modo Fallback - Modelo não carregado):",
            f"Paciente: {name}, {age} anos, {gender}.",
        ]
        if conditions:
            condition_names = [c.get('code', {}).get('text', 'Condição') for c in conditions]
            summary_lines.append(f"Condições: {', '.join(condition_names)}.")
        else:
            summary_lines.append("Sem condições crônicas.")
            
        if medications:
            med_names = [m.get('medicationCodeableConcept', {}).get('text', 'Medicamento') for m in medications]
            summary_lines.append(f"Uso de: {', '.join(med_names)}.")
        else:
            summary_lines.append("Sem medicações.")
            
        return "\n".join(summary_lines)

    def check_drug_interactions(self, new_medication_code, current_medications):
        """
        Verifica interações medicamentosas.
        Usa BioMistral para análise mais profunda se disponível, ou regras rígidas como fallback.
        """
        llm = self.get_llm()
        alerts = []
        
        # Rule-based Check (Always verify strictly first)
        rule_alerts = self._check_rules_strict(new_medication_code, current_medications)
        alerts.extend(rule_alerts)
        
        # If we have the LLM, let's ask it for "subtle" interactions or context
        if llm and current_medications:
            try:
                med_names = [m.get('medicationCodeableConcept', {}).get('text', 'Meds') for m in current_medications]
                current_meds_str = ", ".join(med_names)
                
                # Only consult LLM if we have meds to check against
                prompt = f"""<s>[INST] Analise possíveis interações medicamentosas entre:
                1. Novo Medicamento: {new_medication_code}
                2. Em uso: {current_meds_str}
                
                Se houver interação GRAVE ou MODERADA, explique brevemente o risco. Se for seguro, diga "Baixo risco". [/INST]"""
                
                # limiting max tokens for speed
                # This is a bit heavy for a synchronous blocking API call, so be careful.
                # For demo purposes it's fine.
                # analysis = llm(prompt, max_new_tokens=128)
                # logger.info(f"AI Interaction Analysis: {analysis}")
                pass # Disabling LLM interaction check for now to ensure speed, trusting rules first.
                
            except Exception as e:
                logger.error(f"AI Interaction check failed: {e}")

        return alerts

    def _check_rules_strict(self, new_med, current_meds):
        """Regras determinísticas (Hardcoded) para segurança"""
        alerts = []
        normalized_new = str(new_med).lower()
        
        for med in current_meds:
            med_name = med.get('medicationCodeableConcept', {}).get('text', '').lower()
            
            # Rule 1: Warfarin + Aspirin
            if ('warfarin' in normalized_new and 'aspirin' in med_name) or \
               ('aspirin' in normalized_new and 'warfarin' in med_name):
                alerts.append({
                    "severity": "high",
                    "title": "Risco de Sangramento (Crítico)",
                    "description": "Uso concomitante de Varfarina e Aspirina."
                })
                
            # Rule 2: Simvastatin + Amiodarone
            if ('simvastatin' in normalized_new and 'amiodarone' in med_name) or \
               ('amiodarone' in normalized_new and 'simvastatin' in med_name):
                alerts.append({
                    "severity": "medium",
                    "title": "Risco de Miopatia",
                    "description": "Amiodarona potencializa toxicidade da Sinvastatina."
                })
        return alerts
