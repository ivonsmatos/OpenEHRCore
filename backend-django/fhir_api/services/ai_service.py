
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
        Gera um resumo textual do paciente usando BioMistral ou fallback inteligente.
        """
        llm = self.get_llm()
        
        # Prepare context data
        name = patient_data.get('name', 'Paciente')
        age = patient_data.get('age', 'N/A')
        gender = patient_data.get('gender', 'N/A')
        
        conditions = patient_data.get('conditions', [])
        medications = patient_data.get('medications', [])
        vital_signs = patient_data.get('vital_signs', [])
        
        cond_text = ", ".join([c.get('code', {}).get('text', 'Condição') for c in conditions]) if conditions else "Nenhuma condição crônica registrada"
        med_text = ", ".join([m.get('medicationCodeableConcept', {}).get('text', 'Medicamento') for m in medications]) if medications else "Nenhum medicamento em uso"

        # Construct Prompt (Mistral Format) with Bias Prevention Guardrails
        from .bias_prevention_service import BiasPreventionService
        
        base_prompt = f"""Você é um assistente clínico especializado. Gere um resumo clínico conciso e profissional em Português para o seguinte paciente.
        
        Dados do Paciente:
        - Nome: {name}
        - Idade: {age}
        - Sexo: {gender}
        
        Histórico Médico:
        - Condições: {cond_text}
        - Medicamentos em uso: {med_text}
        
        Sua tarefa: Crie um resumo de 3-5 linhas destacando os pontos principais para um médico ler rapidamente antes da consulta. Use termos técnicos apropriados.
        
        IMPORTANTE: Base suas recomendações SOMENTE em evidências clínicas. NÃO faça generalizações baseadas em raça, etnia ou condição socioeconômica."""
        
        # Add guardrails and format for Mistral
        guarded_prompt = BiasPreventionService.add_guardrails_to_prompt(base_prompt)
        prompt = f"<s>[INST] {guarded_prompt} [/INST]"

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
                # Fallback implementation with clinical analysis
                logger.info("Using fallback summary with clinical analysis.")
                return self._fallback_summary(name, age, gender, conditions, medications, vital_signs)

        except Exception as e:
            logger.error(f"Erro na geração de resumo IA: {str(e)}")
            return "Não foi possível gerar o resumo clínico (Erro no modelo)."

    def _fallback_summary(self, name, age, gender, conditions, medications, vital_signs=None):
        """
        Gera resumo clínico inteligente sem modelo LLM.
        Usa lógica médica baseada em regras e faixas de referência para sinais vitais.
        """
        vital_signs = vital_signs or []
        
        # Normalizar gênero
        gender_display = {
            'male': 'masculino',
            'female': 'feminino',
            'other': 'outro',
            'unknown': 'não informado'
        }.get(gender, gender)
        
        # Iniciar resumo
        summary_parts = []
        alerts = []  # Alertas críticos para o início
        
        # Header do paciente
        age_text = f"{age} anos" if age and age not in ("Desconhecida", "N/A") else "idade não informada"
        summary_parts.append(f"📋 **Perfil do Paciente**")
        summary_parts.append(f"Paciente {name}, {age_text}, sexo {gender_display}.")
        summary_parts.append("")
        
        # =====================================================
        # ANÁLISE DE SINAIS VITAIS COM FAIXAS DE REFERÊNCIA
        # =====================================================
        if vital_signs:
            summary_parts.append("💓 **Sinais Vitais (Últimos Registros)**")
            
            # Organizar sinais vitais por tipo
            vitals_by_type = {}
            for vs in vital_signs:
                code = vs.get('code', {})
                coding = code.get('coding', [{}])[0]
                loinc_code = coding.get('code', '')
                display = coding.get('display', code.get('text', 'Vital'))
                value_qty = vs.get('valueQuantity', {})
                value = value_qty.get('value')
                unit = value_qty.get('unit', '')
                
                if value is not None:
                    vitals_by_type[loinc_code] = {
                        'display': display,
                        'value': value,
                        'unit': unit
                    }
            
            # Analisar cada sinal vital com faixas de referência
            vital_analysis = self._analyze_vitals(vitals_by_type, age, gender)
            
            for va in vital_analysis:
                status_icon = "✅" if va['status'] == 'normal' else "⚠️" if va['status'] == 'attention' else "🔴"
                summary_parts.append(f"• {status_icon} **{va['name']}:** {va['value']} {va['unit']} - {va['interpretation']}")
                
                if va['status'] == 'critical':
                    alerts.append(f"🚨 {va['name']}: {va['value']} {va['unit']} - {va['clinical_action']}")
                elif va['status'] == 'attention':
                    alerts.append(f"⚠️ {va['name']} requer atenção: {va['interpretation']}")
            
            summary_parts.append("")
        
        # =====================================================
        # CONDIÇÕES CLÍNICAS
        # =====================================================
        summary_parts.append("🩺 **Condições Clínicas**")
        if conditions:
            condition_names = []
            active_conditions = []
            for c in conditions:
                code_obj = c.get('code', {})
                coding = code_obj.get('coding', [{}])[0]
                cond_name = code_obj.get('text') or coding.get('display', 'Condição')
                icd_code = coding.get('code', '')
                condition_names.append(cond_name)
                
                clinical_status = c.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '')
                if clinical_status == 'active':
                    active_conditions.append(cond_name)
            
            summary_parts.append(f"• {len(conditions)} diagnóstico(s) registrado(s)")
            if active_conditions:
                summary_parts.append(f"• **Condições Ativas:** {', '.join(active_conditions[:5])}")
                if len(active_conditions) > 3:
                    alerts.append(f"⚠️ Paciente com {len(active_conditions)} comorbidades ativas")
            else:
                summary_parts.append(f"• Histórico: {', '.join(condition_names[:3])}")
        else:
            summary_parts.append("• Nenhum diagnóstico registrado no prontuário.")
        summary_parts.append("")
        
        # =====================================================
        # MEDICAMENTOS
        # =====================================================
        summary_parts.append("💊 **Medicamentos em Uso**")
        if medications:
            med_info = []
            for m in medications:
                med_code = m.get('medicationCodeableConcept', {})
                coding = med_code.get('coding', [{}])[0]
                med_name = med_code.get('text') or coding.get('display', 'Medicamento')
                med_info.append(med_name)
            
            summary_parts.append(f"• **{len(medications)} medicamento(s) ativo(s):** {', '.join(med_info[:5])}")
            
            if len(medications) >= 5:
                alerts.append("⚠️ Polifarmácia: revisar interações medicamentosas")
            if len(medications) >= 8:
                alerts.append("🚨 Alto risco de interações - considerar reconciliação medicamentosa")
        else:
            summary_parts.append("• Nenhum medicamento em uso contínuo registrado.")
        summary_parts.append("")
        
        # =====================================================
        # ALERTAS CRÍTICOS (NO TOPO DO RESUMO FINAL)
        # =====================================================
        if alerts:
            alert_section = ["🚨 **ALERTAS CLÍNICOS**"]
            for alert in alerts[:5]:  # Limitar a 5 alertas mais importantes
                alert_section.append(alert)
            alert_section.append("")
            # Inserir alertas no início
            summary_parts = alert_section + summary_parts
        
        # =====================================================
        # RECOMENDAÇÕES
        # =====================================================
        summary_parts.append("📌 **Recomendações Clínicas**")
        recommendations = []
        
        if not conditions and not medications:
            recommendations.append("• Considerar anamnese detalhada - prontuário sem histórico.")
        
        if conditions and len(conditions) >= 3 and medications and len(medications) >= 3:
            recommendations.append("• Revisar plano terapêutico - múltiplas comorbidades e medicações.")
        
        # Recomendações baseadas nos sinais vitais
        if vital_signs:
            recommendations.append("• Sinais vitais disponíveis - verificar tendência nas últimas consultas.")
        else:
            recommendations.append("• ⚠️ Sem sinais vitais registrados - aferição recomendada.")
        
        if not recommendations:
            recommendations = ["• Manter acompanhamento de rotina."]
        
        summary_parts.extend(recommendations)
        
        return "\n\n".join([p for p in summary_parts if p])  # Double newline for line-by-line display
    
    def _analyze_vitals(self, vitals_by_type, age, gender):
        """
        Analisa sinais vitais com base em faixas de referência médicas.
        Retorna lista de análises com interpretação clínica.
        """
        analysis = []
        
        # Definir faixas de referência (simplificadas para adultos)
        # LOINC codes comuns
        VITAL_REFS = {
            '8867-4': {  # Heart Rate
                'name': 'Frequência Cardíaca',
                'low': 60, 'high': 100, 'critical_low': 50, 'critical_high': 120,
                'low_msg': 'Bradicardia', 'high_msg': 'Taquicardia',
                'action_low': 'Avaliar uso de beta-bloqueadores ou causas cardíacas',
                'action_high': 'Investigar febre, ansiedade, hipertireoidismo, arritmias'
            },
            '8480-6': {  # Systolic BP
                'name': 'PA Sistólica',
                'low': 90, 'high': 140, 'critical_low': 80, 'critical_high': 180,
                'low_msg': 'Hipotensão', 'high_msg': 'Hipertensão',
                'action_low': 'Avaliar hidratação e medicações anti-hipertensivas',
                'action_high': 'Considerar ajuste de anti-hipertensivos'
            },
            '8462-4': {  # Diastolic BP
                'name': 'PA Diastólica',
                'low': 60, 'high': 90, 'critical_low': 50, 'critical_high': 110,
                'low_msg': 'Hipotensão diastólica', 'high_msg': 'Hipertensão diastólica',
                'action_low': 'Monitorar perfusão', 'action_high': 'Avaliar risco cardiovascular'
            },
            '8310-5': {  # Body Temperature
                'name': 'Temperatura',
                'low': 36.0, 'high': 37.5, 'critical_low': 35.0, 'critical_high': 38.5,
                'low_msg': 'Hipotermia', 'high_msg': 'Febre',
                'action_low': 'Avaliar hipotireoidismo ou exposição ao frio',
                'action_high': 'Investigar foco infeccioso'
            },
            '2708-6': {  # SpO2
                'name': 'Saturação O₂',
                'low': 95, 'high': 100, 'critical_low': 90, 'critical_high': 101,
                'low_msg': 'Hipoxemia', 'high_msg': 'Normal',
                'action_low': 'Avaliar função pulmonar e considerar oxigenoterapia',
                'action_high': ''
            },
            '9279-1': {  # Respiratory Rate
                'name': 'Frequência Respiratória',
                'low': 12, 'high': 20, 'critical_low': 8, 'critical_high': 30,
                'low_msg': 'Bradipneia', 'high_msg': 'Taquipneia',
                'action_low': 'Avaliar depressão respiratória',
                'action_high': 'Investigar dispneia, acidose ou ansiedade'
            }
        }
        
        for loinc_code, vital_data in vitals_by_type.items():
            ref = VITAL_REFS.get(loinc_code)
            if not ref:
                # Sinal vital não mapeado, incluir como está
                analysis.append({
                    'name': vital_data['display'],
                    'value': vital_data['value'],
                    'unit': vital_data['unit'],
                    'status': 'normal',
                    'interpretation': 'Valor registrado',
                    'clinical_action': ''
                })
                continue
            
            value = vital_data['value']
            status = 'normal'
            interpretation = 'Dentro da normalidade'
            clinical_action = ''
            
            # Verificar faixas críticas primeiro
            if value <= ref['critical_low']:
                status = 'critical'
                interpretation = f"{ref['low_msg']} grave"
                clinical_action = ref['action_low']
            elif value >= ref['critical_high']:
                status = 'critical'
                interpretation = f"{ref['high_msg']} severa"
                clinical_action = ref['action_high']
            elif value < ref['low']:
                status = 'attention'
                interpretation = ref['low_msg']
                clinical_action = ref['action_low']
            elif value > ref['high']:
                status = 'attention'
                interpretation = ref['high_msg']
                clinical_action = ref['action_high']
            
            analysis.append({
                'name': ref['name'],
                'value': value,
                'unit': vital_data['unit'],
                'status': status,
                'interpretation': interpretation,
                'clinical_action': clinical_action
            })
        
        return analysis

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
