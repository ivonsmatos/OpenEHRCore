
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
        immunizations = patient_data.get('immunizations', [])
        diagnostic_reports = patient_data.get('diagnostic_reports', [])
        appointments = patient_data.get('appointments', [])
        
        cond_text = ", ".join([c.get('code', {}).get('text', 'Condição') for c in conditions]) if conditions else "Nenhuma condição crônica registrada"
        med_text = ", ".join([m.get('medicationCodeableConcept', {}).get('text', 'Medicamento') for m in medications]) if medications else "Nenhum medicamento em uso"

        # Construct Prompt (Mistral Format) with Bias Prevention Guardrails
        from .bias_prevention_service import BiasPreventionService
        
        # Preparar informações sobre sinais vitais
        vitals_text = "Não disponível"
        if vital_signs:
            vitals_list = []
            for vs in vital_signs[:5]:  # Apenas últimos 5 para o prompt
                code = vs.get('code', {})
                display = code.get('text', code.get('coding', [{}])[0].get('display', 'Vital'))
                value_qty = vs.get('valueQuantity', {})
                if value_qty:
                    value = value_qty.get('value')
                    unit = value_qty.get('unit', '')
                    vitals_list.append(f"{display}: {value} {unit}")
            vitals_text = ", ".join(vitals_list) if vitals_list else "Não disponível"
        
        # Preparar informações sobre vacinas
        vaccines_text = "Não disponível"
        if immunizations:
            vaccines_list = []
            for imm in immunizations[:5]:  # Últimas 5 vacinas
                vaccine_code = imm.get('vaccineCode', {})
                vaccine_name = vaccine_code.get('text', vaccine_code.get('coding', [{}])[0].get('display', 'Vacina'))
                date = imm.get('occurrenceDateTime', imm.get('occurrenceString', ''))
                vaccines_list.append(f"{vaccine_name} ({date[:10] if date else 'data N/A'})")
            vaccines_text = ", ".join(vaccines_list)
        
        # Preparar informações sobre exames
        exams_text = "Não disponível"
        if diagnostic_reports:
            exams_list = []
            for report in diagnostic_reports[:3]:  # Últimos 3 exames
                code_obj = report.get('code', {})
                exam_name = code_obj.get('text', code_obj.get('coding', [{}])[0].get('display', 'Exame'))
                date = report.get('effectiveDateTime', report.get('issued', ''))
                conclusion = report.get('conclusion', '')[:100]  # Resumo
                exams_list.append(f"{exam_name} ({date[:10] if date else 'data N/A'})")
                if conclusion:
                    exams_list.append(f"  → {conclusion}")
            exams_text = "\n".join(exams_list)
        
        # Preparar informações sobre agendamentos
        next_appointment = "Nenhum agendamento futuro"
        if appointments:
            from datetime import datetime
            now = datetime.now()
            future_appts = []
            for appt in appointments:
                appt_start = appt.get('start', '')
                if appt_start:
                    try:
                        appt_date = datetime.fromisoformat(appt_start.replace('Z', '+00:00'))
                        if appt_date > now:
                            desc = appt.get('description', 'Consulta')
                            future_appts.append(f"{desc} em {appt_start[:10]}")
                    except:
                        pass
            if future_appts:
                next_appointment = future_appts[0]  # Próximo agendamento
        
        base_prompt = f"""Você é um assistente clínico especializado em medicina baseada em evidências. Seu objetivo é ajudar médicos a tomar decisões clínicas assertivas e seguras.

CONTEXTO DO PACIENTE:
====================
Nome: {name}
Idade: {age} anos
Sexo: {gender}

DADOS CLÍNICOS:
==============
📋 Condições Diagnosticadas: {cond_text}

💊 Medicamentos em Uso: {med_text}

💓 Sinais Vitais (Últimos Registros): {vitals_text}

💉 Vacinas Recentes: {vaccines_text}

🧪 Exames Recentes:
{exams_text}

📅 Próximo Agendamento: {next_appointment}

SUA TAREFA:
==========
Gere um resumo clínico estruturado e fidedigno que ajude o profissional de saúde a tomar decisões assertivas. O resumo deve conter:

1. **PERFIL CLÍNICO** (2-3 linhas):
   - Caracterização do paciente com foco nas condições mais relevantes
   - Nível de complexidade clínica (ex: "paciente com comorbidades complexas", "quadro clínico estável")

2. **PONTOS DE ATENÇÃO** (lista objetiva):
   - Condições que exigem monitoramento especial
   - Alertas sobre polifarmácia (≥5 medicamentos)
   - Interações medicamentosas potenciais conhecidas
   - Sinais vitais fora da faixa de referência
   - Vacinas em atraso (influenza anual, pneumocócica para idosos)
   - Exames laboratoriais pendentes ou com resultados alterados

3. **RECOMENDAÇÕES BASEADAS EM EVIDÊNCIAS** (lista objetiva):
   - Sugestões de exames ou avaliações necessárias
   - Ajustes terapêuticos a considerar
   - Medidas preventivas ou de acompanhamento
   - Encaminhamentos para especialistas se aplicável
   - Vacinas a atualizar

DIRETRIZES IMPORTANTES:
======================
✅ Use linguagem técnica e precisa
✅ Base todas as recomendações em evidências clínicas
✅ Destaque riscos e alertas de segurança do paciente
✅ Seja objetivo e direto - médicos precisam de informação rápida e confiável
✅ Se faltar informação crítica (ex: alergias, exames), mencione isso como ponto de atenção

❌ NÃO faça generalizações baseadas em raça, etnia ou condição socioeconômica
❌ NÃO invente dados ou exames que não foram fornecidos
❌ NÃO use termos vagos ou ambíguos
❌ NÃO omita alertas de segurança importantes

Este resumo será usado para tomada de decisão clínica. Seja preciso e completo."""
        
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
                return self._fallback_summary(name, age, gender, conditions, medications, vital_signs, immunizations, diagnostic_reports, appointments)

        except Exception as e:
            logger.error(f"Erro na geração de resumo IA: {str(e)}")
            return "Não foi possível gerar o resumo clínico (Erro no modelo)."

    def _fallback_summary(self, name, age, gender, conditions, medications, vital_signs=None, immunizations=None, diagnostic_reports=None, appointments=None):
        """
        Gera resumo clínico inteligente sem modelo LLM.
        Usa lógica médica baseada em regras e faixas de referência para sinais vitais.
        Inclui análise de vacinas, exames e agendamentos.
        """
        logger.info("🔥🔥🔥 USANDO _FALLBACK_SUMMARY ATUALIZADO - VERSÃO COMPLETA! 🔥🔥🔥")
        vital_signs = vital_signs or []
        immunizations = immunizations or []
        diagnostic_reports = diagnostic_reports or []
        appointments = appointments or []
        
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
        summary_parts.append(f"## 📋 PERFIL DO PACIENTE\n")
        summary_parts.append(f"**Nome:** {name}  ")
        summary_parts.append(f"**Idade:** {age_text}  ")
        summary_parts.append(f"**Sexo:** {gender_display}\n")
        summary_parts.append("---\n")
        
        # =====================================================
        # ANÁLISE DE SINAIS VITAIS COM FAIXAS DE REFERÊNCIA
        # =====================================================
        if vital_signs:
            summary_parts.append("## 💓 SINAIS VITAIS\n")
            
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
                summary_parts.append(f"- {status_icon} **{va['name']}:** `{va['value']} {va['unit']}`")
                summary_parts.append(f"  - {va['interpretation']}\n")
                
                if va['status'] == 'critical':
                    alerts.append(f"🚨 **{va['name']}:** {va['value']} {va['unit']} - {va['clinical_action']}")
                elif va['status'] == 'attention':
                    alerts.append(f"⚠️ **{va['name']}** requer atenção: {va['interpretation']}")
            
            summary_parts.append("---\n")
        
        # =====================================================
        # CONDIÇÕES CLÍNICAS
        # =====================================================
        summary_parts.append("## 🩺 CONDIÇÕES CLÍNICAS\n")
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
                    summary_parts.append(f"- 🔴 **{cond_name}** (CID: {icd_code}) - Status: ATIVO\n")
                else:
                    summary_parts.append(f"- ⚪ **{cond_name}** (CID: {icd_code}) - Status: {clinical_status}\n")
            
            if len(active_conditions) > 3:
                alerts.append(f"⚠️ **COMORBIDADES MÚLTIPLAS:** {len(active_conditions)} condições ativas requerem monitoramento integrado")
        else:
            summary_parts.append("- ℹ️ Nenhum diagnóstico registrado no prontuário.\n")
        summary_parts.append("---\n")
        
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
        # VACINAS (IMMUNIZATIONS)
        # =====================================================
        summary_parts.append("## 💉 HISTÓRICO DE VACINAÇÃO\n")
        if immunizations:
            summary_parts.append("**Vacinas Registradas:**\n")
            
            for imm in immunizations[:5]:  # Últimas 5 vacinas
                vaccine_code = imm.get('vaccineCode', {})
                vaccine_name = vaccine_code.get('text', vaccine_code.get('coding', [{}])[0].get('display', 'Vacina'))
                date = imm.get('occurrenceDateTime', imm.get('occurrenceString', ''))
                date_display = date[:10] if date else 'data N/A'
                lot_number = imm.get('lotNumber', 'Lote N/A')
                summary_parts.append(f"- ✅ **{vaccine_name}** - Data: {date_display} | Lote: {lot_number}\n")
            
            # Verificar vacinas importantes em atraso
            vaccine_names_lower = ' '.join([vaccine_code.get('text', vaccine_code.get('coding', [{}])[0].get('display', '')).lower() for imm in immunizations for vaccine_code in [imm.get('vaccineCode', {})]])
            if age and isinstance(age, (int, float)) and age >= 65:
                if 'influenza' not in vaccine_names_lower and 'gripe' not in vaccine_names_lower:
                    alerts.append("⚠️ **VACINA EM ATRASO:** Influenza (gripe) anual recomendada para ≥65 anos")
                if 'pneumo' not in vaccine_names_lower:
                    alerts.append("⚠️ **VACINA EM ATRASO:** Pneumocócica recomendada para ≥65 anos")
        else:
            summary_parts.append("- ⚠️ Nenhum registro de vacinação no sistema\n")
            alerts.append("⚠️ **DADOS INCOMPLETOS:** Atualizar cartão de vacinação no prontuário")
        summary_parts.append("---\n")
        
        # =====================================================
        # EXAMES LABORATORIAIS (DIAGNOSTIC REPORTS)
        # =====================================================
        summary_parts.append("## 🧪 EXAMES LABORATORIAIS\n")
        if diagnostic_reports:
            summary_parts.append("**Últimos Resultados:**\n")
            
            for idx, report in enumerate(diagnostic_reports[:5], 1):
                code_obj = report.get('code', {})
                exam_name = code_obj.get('text', code_obj.get('coding', [{}])[0].get('display', 'Exame'))
                date = report.get('effectiveDateTime', report.get('issued', ''))
                date_display = date[:10] if date else 'data N/A'
                status = report.get('status', 'final')
                
                summary_parts.append(f"\n**{idx}. {exam_name}**")
                summary_parts.append(f"- Data: {date_display} | Status: {status}")
                
                # Adicionar conclusão se disponível
                conclusion = report.get('conclusion', '')
                if conclusion:
                    summary_parts.append(f"- Conclusão: _{conclusion[:200]}{'...' if len(conclusion) > 200 else ''}_\n")
                else:
                    summary_parts.append("- Conclusão: Não disponível\n")
            
            # Verificar se exames estão atualizados
            from datetime import datetime, timedelta
            most_recent_date = None
            for report in diagnostic_reports:
                date_str = report.get('effectiveDateTime', report.get('issued', ''))
                if date_str:
                    try:
                        exam_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        if most_recent_date is None or exam_date > most_recent_date:
                            most_recent_date = exam_date
                    except:
                        pass
            
            if most_recent_date and (datetime.now() - most_recent_date).days > 180:
                alerts.append(f"⚠️ **EXAMES DESATUALIZADOS:** Último exame há {(datetime.now() - most_recent_date).days} dias")
        else:
            summary_parts.append("- ⚠️ Nenhum exame laboratorial registrado\n")
            alerts.append("⚠️ **DADOS INCOMPLETOS:** Solicitar exames de rotina conforme condições clínicas")
        summary_parts.append("---\n")
        
        # =====================================================
        # AGENDAMENTOS (APPOINTMENTS)
        # =====================================================
        summary_parts.append("## 📅 AGENDAMENTOS\n")
        if appointments:
            from datetime import datetime
            now = datetime.now()
            past_appts = []
            future_appts = []
            
            for appt in appointments:
                appt_start = appt.get('start', '')
                status_appt = appt.get('status', '')
                description = appt.get('description', 'Consulta')
                
                if appt_start:
                    try:
                        appt_date = datetime.fromisoformat(appt_start.replace('Z', '+00:00'))
                        date_display = appt_start[:10]
                        time_display = appt_start[11:16] if len(appt_start) > 11 else ''
                        
                        if appt_date > now:
                            future_appts.append(f"- 📌 **{description}** - {date_display} às {time_display} | Status: `{status_appt}`\n")
                        else:
                            past_appts.append(f"- ✅ **{description}** - {date_display}\n")
                    except:
                        pass
            
            if future_appts:
                summary_parts.append("**Próximas Consultas:**\n")
                summary_parts.extend(future_appts[:3])
            else:
                summary_parts.append("- ⚠️ Nenhum agendamento futuro\n")
                alerts.append("⚠️ **ACOMPANHAMENTO:** Agendar consulta de retorno")
            
            if past_appts:
                summary_parts.append("\n**Consultas Recentes:**\n")
                summary_parts.extend(past_appts[:2])
        else:
            summary_parts.append("- ℹ️ Nenhum agendamento no sistema\n")
        summary_parts.append("---\n")
        
        # =====================================================
        # ALERTAS CRÍTICOS (NO TOPO DO RESUMO FINAL)
        # =====================================================
        if alerts:
            alert_section = ["## 🚨 ALERTAS CLÍNICOS\n"]
            alert_section.append("> **ATENÇÃO:** Revisar imediatamente os seguintes pontos:\n")
            for alert in alerts[:10]:
                alert_section.append(f"{alert}\n")
            alert_section.append("---\n")
            # Inserir alertas no início
            summary_parts = alert_section + summary_parts
        
        # =====================================================
        # RECOMENDAÇÕES CLÍNICAS BASEADAS EM EVIDÊNCIAS
        # =====================================================
        summary_parts.append("## 📌 RECOMENDAÇÕES CLÍNICAS\n")
        summary_parts.append("> **Baseadas em evidências e guidelines clínicos**\n")
        recommendations = []
        
        # Análise de prontuário incompleto
        if not conditions and not medications:
            recommendations.append("- ⚠️ **PRONTUÁRIO INCOMPLETO**")
            recommendations.append("  - Realizar anamnese detalhada e registrar histórico médico completo\n")
        
        # Recomendações por complexidade clínica
        if conditions and len(conditions) >= 3 and medications and len(medications) >= 3:
            recommendations.append("- 🔴 **ALTA COMPLEXIDADE**")
            recommendations.append("  - Revisar plano terapêutico integrado considerando todas as comorbidades")
            recommendations.append("  - Avaliar aderência medicamentosa e possíveis interações\n")
        
        # Alertas específicos de condições comuns (baseado em guidelines)
        active_conditions_lower = [c.lower() for c in active_conditions] if conditions else []
        
        if any('diabetes' in c for c in active_conditions_lower):
            recommendations.append("- 💉 **DIABETES MELLITUS**")
            recommendations.append("  - Verificar última HbA1c (meta <7%)")
            recommendations.append("  - Solicitar exame de fundo de olho anual")
            recommendations.append("  - Avaliar função renal (creatinina/TFG)\n")
        
        if any('hipertens' in c for c in active_conditions_lower):
            recommendations.append("- 🩺 **HIPERTENSÃO ARTERIAL**")
            recommendations.append("  - Meta: PA <140/90 mmHg (ou <130/80 se diabético/DRC)")
            recommendations.append("  - Avaliar adesão ao tratamento anti-hipertensivo\n")
        
        if any('insuficiência cardíaca' in c or 'icc' in c for c in active_conditions_lower):
            recommendations.append("- ❤️ **INSUFICIÊNCIA CARDÍACA**")
            recommendations.append("  - Monitorar peso diário")
            recommendations.append("  - Avaliar sintomas de descompensação")
            recommendations.append("  - Verificar função renal\n")
        
        # Recomendações baseadas nos sinais vitais
        if vital_signs:
            vital_analysis = self._analyze_vitals(vitals_by_type, age, gender) if 'vitals_by_type' in locals() else []
            critical_vitals = [va for va in vital_analysis if va['status'] in ['attention', 'critical'] and va.get('clinical_action')]
            
            if critical_vitals:
                recommendations.append("- 💓 **SINAIS VITAIS ALTERADOS**")
                for va in critical_vitals:
                    recommendations.append(f"  - {va['name']}: {va['clinical_action']}\n")
        else:
            recommendations.append("- ⚠️ **SINAIS VITAIS AUSENTES**")
            recommendations.append("  - Aferir PA, FC, temperatura, SpO2 e peso hoje\n")
        
        # Prevenção e rastreamento
        screening_recs = []
        if age and isinstance(age, (int, float)):
            if age >= 50:
                screening_recs.append("  - Colonoscopia (≥50 anos)")
            if gender == 'female' and age >= 40:
                screening_recs.append("  - Mamografia anual (≥40 anos)")
            if age >= 65:
                screening_recs.append("  - Vacinação antipneumocócica")
                screening_recs.append("  - Influenza anual")
        
        if screening_recs:
            recommendations.append("- 🎯 **PREVENÇÃO E RASTREAMENTO**")
            recommendations.extend(screening_recs)
            recommendations.append("")
        
        # Informação crítica faltante
        missing_data = []
        if not vital_signs:
            missing_data.append("sinais vitais")
        if not conditions:
            missing_data.append("diagnósticos")
        if not medications:
            missing_data.append("medicamentos em uso")
        if not immunizations:
            missing_data.append("histórico de vacinação")
        if not diagnostic_reports:
            missing_data.append("exames laboratoriais")
        
        if missing_data:
            recommendations.append("- 📋 **COMPLETAR PRONTUÁRIO**")
            for data in missing_data:
                recommendations.append(f"  - Registrar: {data}")
            recommendations.append("")
            if age >= 50:
                recommendations.append("• **RASTREAMENTO (≥50 anos)**: Verificar status de colonoscopia")
        
        # Recomendações de exames
        if not diagnostic_reports or (diagnostic_reports and (datetime.now() - most_recent_date).days > 365 if 'most_recent_date' in locals() and most_recent_date else True):
            recommendations.append("• **EXAMES**: Solicitar hemograma, glicemia, função renal e lipidograma (exames de rotina)")
        
        # Pelo menos uma recomendação padrão se lista estiver vazia
        if not recommendations:
            recommendations = ["• Manter acompanhamento conforme protocolo estabelecido"]
        
        summary_parts.extend(recommendations)
        
        # =====================================================
        # RESUMO EXECUTIVO NO INÍCIO
        # =====================================================
        complexity = "BAIXA"
        if (conditions and len(conditions) >= 3) or (medications and len(medications) >= 5):
            complexity = "ALTA"
        elif (conditions and len(conditions) >= 1) or (medications and len(medications) >= 1):
            complexity = "MODERADA"
        
        executive_summary = [
            f"🎯 **RESUMO EXECUTIVO**",
            f"Paciente com complexidade clínica **{complexity}**.",
        ]
        
        if conditions and len(active_conditions) > 0:
            executive_summary.append(f"Principais condições ativas: {', '.join(active_conditions[:3])}.")
        
        if medications and len(medications) >= 5:
            executive_summary.append(f"⚠️ Polifarmácia identificada ({len(medications)} medicamentos).")
        
        if len(alerts) > 0:
            executive_summary.append(f"🚨 **{len(alerts)} alerta(s) clínico(s)** - verificar seção de alertas.")
        
        executive_summary.append("")
        
        # Inserir resumo executivo no topo
        summary_parts = executive_summary + summary_parts
        
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
