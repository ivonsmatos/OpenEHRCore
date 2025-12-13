
import logging
from collections import Counter
from datetime import datetime, date
from typing import Dict, Any, List

from .fhir_core import FHIRService

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Serviço responsável por agregar dados do servidor FHIR
    para gerar indicadores gerenciais e clínicos.
    """

    def __init__(self):
        self.fhir = FHIRService()
        # Reutiliza a sessão e URL do FHIRService
        self.session = self.fhir.session
        self.base_url = self.fhir.base_url
        self.timeout = self.fhir.timeout

    def _fetch_all_resources(self, resource_type: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Busca recursos do FHIR (limite configurável para evitar timeout em demo).
        Em produção, usaria paginação iterativa.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/{resource_type}",
                params={"_count": limit, "_sort": "-_lastUpdated"},
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            
            resources = []
            if "entry" in bundle:
                for entry in bundle["entry"]:
                    if "resource" in entry:
                        resources.append(entry["resource"])
                        
            return resources
        except Exception as e:
            logger.error(f"Analytics: Falha ao buscar {resource_type}: {e}")
            return []

    def get_population_demographics(self) -> Dict[str, Any]:
        """
        Gera métricas de pirâmide etária e gênero.
        """
        patients = self._fetch_all_resources("Patient", limit=1000)
        
        gender_dist = Counter()
        age_groups = {
            "0-12": 0,
            "13-18": 0,
            "19-30": 0,
            "31-50": 0,
            "51-70": 0,
            "71+": 0
        }
        
        today = date.today()
        
        for p in patients:
            # Gênero
            g = p.get("gender", "unknown")
            gender_dist[g] += 1
            
            # Idade
            birth_date_str = p.get("birthDate")
            if birth_date_str:
                try:
                    # Tenta parsing simples YYYY-MM-DD
                    bd = datetime.strptime(birth_date_str[:10], "%Y-%m-%d").date()
                    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
                    
                    if age <= 12: age_groups["0-12"] += 1
                    elif age <= 18: age_groups["13-18"] += 1
                    elif age <= 30: age_groups["19-30"] += 1
                    elif age <= 50: age_groups["31-50"] += 1
                    elif age <= 70: age_groups["51-70"] += 1
                    else: age_groups["71+"] += 1
                except:
                    pass

        return {
            "total_patients": len(patients),
            "gender_distribution": dict(gender_dist),
            "age_distribution": age_groups
        }

    def get_clinical_insights(self) -> Dict[str, Any]:
        """
        Gera métricas de condições mais frequentes.
        """
        conditions = self._fetch_all_resources("Condition", limit=1000)
        
        condition_counter = Counter()
        
        for c in conditions:
            code_entry = {}
            if c.get("code") and c.get("code").get("coding"):
                code_entry = c["code"]["coding"][0]
            
            display = code_entry.get("display") or code_entry.get("code") or "Desconhecido"
            condition_counter[display] += 1
            
        top_5 = [{"name": k, "value": v} for k, v in condition_counter.most_common(5)]
        
        return {
            "total_conditions": len(conditions),
            "top_conditions": top_5
        }

    def get_operational_metrics(self) -> Dict[str, Any]:
        """
        Gera métricas de operação (ex: Atendimentos e Agendamentos).
        OBS: Usaremos Appointment se disponível, ou Encounter como proxy.
        """
        # Para simplificar, vamos analisar Encounters (Atendimentos Realizados)
        encounters = self._fetch_all_resources("Encounter", limit=500)
        
        # Agrupar por status
        status_dist = Counter()
        type_dist = Counter()
        
        dates_counter = Counter() # Atendimentos por dia (últimos 7 dias seria ideal)
        
        for e in encounters:
            status_dist[e.get("status", "unknown")] += 1
            
            # Tipo
            types = e.get("type", [])
            t = "N/A"
            if types and len(types) > 0 and types[0].get("coding"):
                coding = types[0]["coding"]
                if len(coding) > 0:
                    t = coding[0].get("code", "N/A")
            
            type_dist[t] += 1
                
        return {
            "status_distribution": dict(status_dist),
            "type_distribution": dict(type_dist)
        }

    def get_kpi_summary(self) -> Dict[str, Any]:
        """
        Gera os KPIs específicos do 'Medical Template'.
        Puxa dados reais do FHIR.
        """
        print("=== DEBUG: get_kpi_summary NOVO CODIGO v2 ===")  # Debug
        
        # 1. New Patients (Total Pacientes)
        total_patients = len(self._fetch_all_resources("Patient", limit=1000))
        print(f"DEBUG: total_patients = {total_patients}")
        
        # 2. OPD Patients (Outpatient Department - Ambulatorial)
        # Count appointments with status booked, arrived, or fulfilled
        appointments = self._fetch_all_resources("Appointment", limit=500)
        print(f"DEBUG: appointments fetched = {len(appointments)}")
        
        active_statuses = ["booked", "arrived", "fulfilled", "pending"]
        opd_count = sum(1 for a in appointments if a.get("status") in active_statuses)
        print(f"DEBUG: opd_count = {opd_count}")
        
        # 3. Operations (Cirurgias)
        # Count Procedure resources - these represent surgical procedures
        procedures = self._fetch_all_resources("Procedure", limit=100)
        surgeries_count = len(procedures)
        print(f"DEBUG: surgeries_count = {surgeries_count}")
        
        # 4. Visitors
        # Estimate based on patient count
        visitors_count = int(total_patients * 2.5)
        
        result = {
            "new_patients": total_patients,
            "opd_patients": opd_count,
            "todays_operations": surgeries_count,
            "visitors": visitors_count
        }
        print(f"DEBUG: returning = {result}")
        return result

    def get_hospital_survey_data(self) -> Dict[str, Any]:
        """
        Gera dados para o gráfico 'Hospital Survey' (Line Chart).
        Simula dados mensais de Jan a Dez.
        """
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Simulação com base em senoide ou aleatória controlada
        return {
             "labels": months,
             "series": [
                 {"name": "Patients", "data": [15, 45, 35, 20, 40, 60, 35, 20, 15, 30, 20, 10]}, # Linha azul da imagem
                 {"name": "Recovery", "data": [10, 20, 15, 10, 20, 25, 40, 50, 60, 30, 40, 50]}  # Exemplo linha pontilhada
             ]
        }

    def get_recent_admissions(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de admissões recentes para o Dashboard.
        """
        # Fetch encounters with patient included
        try:
            response = self.session.get(
                f"{self.base_url}/Encounter",
                params={
                    "_count": 20,
                    "_sort": "-_lastUpdated",
                    "_include": "Encounter:subject"
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            
            encounters = []
            patients_map = {}
            
            # Separate encounters and patients from bundle
            if "entry" in bundle:
                for entry in bundle["entry"]:
                    resource = entry.get("resource", {})
                    resource_type = resource.get("resourceType")
                    
                    if resource_type == "Encounter":
                        encounters.append(resource)
                    elif resource_type == "Patient":
                        patients_map[resource.get("id")] = resource
        except Exception as e:
            logger.error(f"Error fetching encounters: {e}")
            encounters = []
            patients_map = {}
        
        admissions = []
        for i, enc in enumerate(encounters):
            # Extract data
            patient_ref = enc.get("subject", {})
            patient_id = patient_ref.get('reference', '').split('/')[-1] if patient_ref.get('reference') else None
            
            # Try to get patient name from included patients or display
            patient_name = patient_ref.get("display")
            if not patient_name and patient_id and patient_id in patients_map:
                patient_resource = patients_map[patient_id]
                if "name" in patient_resource:
                    name_obj = patient_resource["name"][0]
                    given = " ".join(name_obj.get("given", []))
                    family = name_obj.get("family", "")
                    patient_name = f"{given} {family}".strip()
            
            if not patient_name:
                patient_name = f"Patient {patient_id or '?'}"
            
            practitioner_ref = enc.get("participant", [{}])[0].get("individual", {})
            doctor_name = practitioner_ref.get("display") or "Dr. Plantão"
            
            period_start = enc.get("period", {}).get("start", "")
            # Format date
            date_str = period_start[:10] if period_start else "N/A"
            
            # Condition? Encounter usually doesn't have condition directly, but 'reasonCode'
            reason = "Check-up"
            if enc.get("reasonCode"):
                reason = enc["reasonCode"][0].get("text") or enc["reasonCode"][0].get("coding", [{}])[0].get("display", "Check-up")
            
            # Mock Room (not standard in Encounter unless location)
            room = f"{100 + (i % 20)}"
            
            admissions.append({
                "id": enc.get("id"),
                "no": i + 1,
                "name": patient_name,
                "patient_id": patient_id,  # Added for navigation
                "doctor": doctor_name,
                "date": date_str,
                "condition": reason,
                "room": room
            })
            
        return admissions
