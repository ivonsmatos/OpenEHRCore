"""
Sprint 21: Terminology Service

This module provides integration with medical terminology systems:
- RxNorm (NLM) for medications
- ICD-10 for diagnoses
- TUSS (Tabela SUS) for Brazilian procedures
- SNOMED CT mappings
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# RxNorm API base URL (NLM public API - no authentication required)
RXNORM_API_BASE = "https://rxnav.nlm.nih.gov/REST"


class TerminologyService:
    """Service for medical terminology lookups and validations."""
    
    # Cache TTL in seconds (1 hour for terminology data)
    _cache_ttl = 3600
    
    @classmethod
    @lru_cache(maxsize=1000)
    def search_rxnorm(cls, term: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search RxNorm for medications by name.
        
        Args:
            term: Search term (medication name)
            max_results: Maximum number of results to return
            
        Returns:
            List of matching medications with RxCUI codes
        """
        try:
            # Use approximate matching for better results
            url = f"{RXNORM_API_BASE}/approximateTerm.json"
            params = {"term": term, "maxEntries": max_results}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            candidates = data.get("approximateGroup", {}).get("candidate", [])
            
            results = []
            for candidate in candidates[:max_results]:
                rxcui = candidate.get("rxcui")
                if rxcui:
                    # Get detailed info for each result
                    details = cls.get_rxnorm_details(rxcui)
                    if details:
                        results.append({
                            "rxcui": rxcui,
                            "name": details.get("name", candidate.get("name", "")),
                            "score": candidate.get("score", 0),
                            "tty": details.get("tty", ""),  # Term type (SCD, SBD, etc.)
                            "synonym": details.get("synonym", "")
                        })
            
            logger.info(f"RxNorm search for '{term}' returned {len(results)} results")
            return results
            
        except requests.RequestException as e:
            logger.error(f"RxNorm API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error searching RxNorm: {str(e)}")
            return []
    
    @classmethod
    @lru_cache(maxsize=500)
    def get_rxnorm_details(cls, rxcui: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for an RxNorm concept.
        
        Args:
            rxcui: RxNorm Concept Unique Identifier
            
        Returns:
            Dictionary with medication details
        """
        try:
            url = f"{RXNORM_API_BASE}/rxcui/{rxcui}/properties.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            props = data.get("properties", {})
            
            return {
                "rxcui": rxcui,
                "name": props.get("name", ""),
                "tty": props.get("tty", ""),
                "synonym": props.get("synonym", ""),
                "language": props.get("language", "ENG"),
                "active": props.get("suppress", "N") != "Y"
            }
            
        except requests.RequestException as e:
            logger.error(f"RxNorm details error for {rxcui}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting RxNorm details: {str(e)}")
            return None
    
    @classmethod
    @lru_cache(maxsize=200)
    def get_rxnorm_interactions(cls, rxcui: str) -> List[Dict[str, Any]]:
        """
        Get drug interactions for an RxNorm concept.
        
        Args:
            rxcui: RxNorm Concept Unique Identifier
            
        Returns:
            List of potential drug interactions
        """
        try:
            url = f"{RXNORM_API_BASE}/interaction/interaction.json"
            params = {"rxcui": rxcui}
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            interaction_groups = data.get("interactionTypeGroup", [])
            
            interactions = []
            for group in interaction_groups:
                source = group.get("sourceName", "")
                for interaction_type in group.get("interactionType", []):
                    for pair in interaction_type.get("interactionPair", []):
                        interactions.append({
                            "source": source,
                            "severity": pair.get("severity", "unknown"),
                            "description": pair.get("description", ""),
                            "interacting_drug": pair.get("interactionConcept", [{}])[1].get("minConceptItem", {}).get("name", "") if len(pair.get("interactionConcept", [])) > 1 else ""
                        })
            
            logger.info(f"Found {len(interactions)} interactions for RxCUI {rxcui}")
            return interactions
            
        except requests.RequestException as e:
            logger.error(f"RxNorm interactions error for {rxcui}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting RxNorm interactions: {str(e)}")
            return []
    
    @classmethod
    def check_multi_drug_interactions(cls, rxcuis: List[str]) -> List[Dict[str, Any]]:
        """
        Check interactions between multiple drugs.
        
        Args:
            rxcuis: List of RxNorm CUIs to check
            
        Returns:
            List of interactions between the provided drugs
        """
        if len(rxcuis) < 2:
            return []
            
        try:
            url = f"{RXNORM_API_BASE}/interaction/list.json"
            params = {"rxcuis": "+".join(rxcuis)}
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            interactions = []
            
            for group in data.get("fullInteractionTypeGroup", []):
                for interaction_type in group.get("fullInteractionType", []):
                    for pair in interaction_type.get("interactionPair", []):
                        concepts = pair.get("interactionConcept", [])
                        if len(concepts) >= 2:
                            interactions.append({
                                "drug1": concepts[0].get("minConceptItem", {}).get("name", ""),
                                "drug1_rxcui": concepts[0].get("minConceptItem", {}).get("rxcui", ""),
                                "drug2": concepts[1].get("minConceptItem", {}).get("name", ""),
                                "drug2_rxcui": concepts[1].get("minConceptItem", {}).get("rxcui", ""),
                                "severity": pair.get("severity", "unknown"),
                                "description": pair.get("description", "")
                            })
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error checking multi-drug interactions: {str(e)}")
            return []


# ICD-10 Code Database (subset of commonly used codes)
# Full database would be loaded from a JSON file
ICD10_CODES = {
    # Infectious diseases (A00-B99)
    "A09": {"description": "Outras gastroenterites e colites de origem infecciosa e não especificada", "category": "Doenças infecciosas intestinais"},
    "A15": {"description": "Tuberculose respiratória, confirmada bacteriológica e histologicamente", "category": "Tuberculose"},
    "A90": {"description": "Dengue [dengue clássico]", "category": "Febres virais transmitidas por artrópodes"},
    "A91": {"description": "Febre hemorrágica devida ao vírus do dengue", "category": "Febres virais transmitidas por artrópodes"},
    
    # Neoplasms (C00-D49)
    "C34": {"description": "Neoplasia maligna dos brônquios e dos pulmões", "category": "Neoplasias malignas dos órgãos respiratórios"},
    "C50": {"description": "Neoplasia maligna da mama", "category": "Neoplasias malignas da mama"},
    "C61": {"description": "Neoplasia maligna da próstata", "category": "Neoplasias malignas dos órgãos genitais masculinos"},
    
    # Diseases of blood (D50-D89)
    "D50": {"description": "Anemia por deficiência de ferro", "category": "Anemias nutricionais"},
    
    # Endocrine diseases (E00-E89)
    "E10": {"description": "Diabetes mellitus insulino-dependente", "category": "Diabetes mellitus"},
    "E11": {"description": "Diabetes mellitus não-insulino-dependente", "category": "Diabetes mellitus"},
    "E66": {"description": "Obesidade", "category": "Obesidade e outras formas de hiperalimentação"},
    "E78": {"description": "Distúrbios do metabolismo de lipoproteínas e outras lipidemias", "category": "Distúrbios metabólicos"},
    
    # Mental disorders (F00-F99)
    "F32": {"description": "Episódios depressivos", "category": "Transtornos do humor [afetivos]"},
    "F33": {"description": "Transtorno depressivo recorrente", "category": "Transtornos do humor [afetivos]"},
    "F41": {"description": "Outros transtornos ansiosos", "category": "Transtornos neuróticos"},
    
    # Circulatory system (I00-I99)
    "I10": {"description": "Hipertensão essencial (primária)", "category": "Doenças hipertensivas"},
    "I11": {"description": "Doença cardíaca hipertensiva", "category": "Doenças hipertensivas"},
    "I20": {"description": "Angina pectoris", "category": "Doenças isquêmicas do coração"},
    "I21": {"description": "Infarto agudo do miocárdio", "category": "Doenças isquêmicas do coração"},
    "I25": {"description": "Doença isquêmica crônica do coração", "category": "Doenças isquêmicas do coração"},
    "I50": {"description": "Insuficiência cardíaca", "category": "Outras formas de doença do coração"},
    "I63": {"description": "Infarto cerebral", "category": "Doenças cerebrovasculares"},
    "I64": {"description": "Acidente vascular cerebral, não especificado", "category": "Doenças cerebrovasculares"},
    
    # Respiratory system (J00-J99)
    "J00": {"description": "Nasofaringite aguda [resfriado comum]", "category": "Infecções agudas das vias aéreas superiores"},
    "J06": {"description": "Infecções agudas das vias aéreas superiores", "category": "Infecções agudas das vias aéreas superiores"},
    "J18": {"description": "Pneumonia por microorganismo não especificado", "category": "Pneumonia"},
    "J45": {"description": "Asma", "category": "Doenças crônicas das vias aéreas inferiores"},
    "J44": {"description": "Outras doenças pulmonares obstrutivas crônicas", "category": "Doenças crônicas das vias aéreas inferiores"},
    
    # Digestive system (K00-K95)
    "K21": {"description": "Doença de refluxo gastroesofágico", "category": "Doenças do esôfago, estômago e duodeno"},
    "K29": {"description": "Gastrite e duodenite", "category": "Doenças do esôfago, estômago e duodeno"},
    "K35": {"description": "Apendicite aguda", "category": "Doenças do apêndice"},
    "K80": {"description": "Colelitíase", "category": "Transtornos da vesícula biliar"},
    
    # Musculoskeletal (M00-M99)
    "M54": {"description": "Dorsalgia", "category": "Dorsopatias"},
    "M79": {"description": "Outros transtornos de tecidos moles", "category": "Outros transtornos de tecidos moles"},
    
    # Genitourinary (N00-N99)
    "N18": {"description": "Doença renal crônica", "category": "Insuficiência renal"},
    "N30": {"description": "Cistite", "category": "Outras doenças do aparelho urinário"},
    "N39": {"description": "Outros transtornos do trato urinário", "category": "Outras doenças do aparelho urinário"},
    
    # Pregnancy (O00-O9A)
    "O80": {"description": "Parto único espontâneo", "category": "Parto"},
    
    # Symptoms and signs (R00-R99)
    "R10": {"description": "Dor abdominal e pélvica", "category": "Sintomas e sinais relativos ao aparelho digestivo e abdome"},
    "R50": {"description": "Febre de origem desconhecida", "category": "Sintomas e sinais gerais"},
    "R51": {"description": "Cefaleia", "category": "Sintomas e sinais gerais"},
    
    # Injuries (S00-T88)
    "S62": {"description": "Fratura ao nível do punho e da mão", "category": "Traumatismos do punho e da mão"},
    "S72": {"description": "Fratura do fêmur", "category": "Traumatismos do quadril e da coxa"},
    
    # External causes (V00-Y99)
    "W19": {"description": "Queda sem especificação", "category": "Quedas"},
    
    # COVID-19 related
    "U07.1": {"description": "COVID-19, vírus identificado", "category": "COVID-19"},
    "U07.2": {"description": "COVID-19, vírus não identificado", "category": "COVID-19"},
}


class ICD10Service:
    """Service for ICD-10 code validation and lookup."""
    
    @classmethod
    def search(cls, term: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search ICD-10 codes by description.
        
        Args:
            term: Search term
            max_results: Maximum results
            
        Returns:
            List of matching ICD-10 codes
        """
        term_lower = term.lower()
        results = []
        
        for code, info in ICD10_CODES.items():
            # Search in code, description and category
            if (term_lower in code.lower() or 
                term_lower in info["description"].lower() or
                term_lower in info["category"].lower()):
                results.append({
                    "code": code,
                    "description": info["description"],
                    "category": info["category"],
                    "system": "http://hl7.org/fhir/sid/icd-10"
                })
                
                if len(results) >= max_results:
                    break
        
        return results
    
    @classmethod
    def validate(cls, code: str) -> Optional[Dict[str, Any]]:
        """
        Validate an ICD-10 code.
        
        Args:
            code: ICD-10 code to validate
            
        Returns:
            Code details if valid, None if invalid
        """
        # Normalize code (remove dots)
        normalized = code.upper().replace(".", "")
        
        # Check with and without subcodes
        for icd_code in ICD10_CODES:
            if normalized.startswith(icd_code.replace(".", "").upper()):
                info = ICD10_CODES[icd_code]
                return {
                    "code": code,
                    "normalized": icd_code,
                    "description": info["description"],
                    "category": info["category"],
                    "valid": True,
                    "system": "http://hl7.org/fhir/sid/icd-10"
                }
        
        return None
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional[Dict[str, Any]]:
        """Get ICD-10 code details."""
        return cls.validate(code)


# ICD-10 to SNOMED CT mapping (subset of common mappings)
ICD10_SNOMED_MAP = {
    "I10": {"snomed": "38341003", "snomed_display": "Essential hypertension"},
    "I21": {"snomed": "22298006", "snomed_display": "Myocardial infarction"},
    "E11": {"snomed": "44054006", "snomed_display": "Type 2 diabetes mellitus"},
    "E10": {"snomed": "46635009", "snomed_display": "Type 1 diabetes mellitus"},
    "J45": {"snomed": "195967001", "snomed_display": "Asthma"},
    "F32": {"snomed": "35489007", "snomed_display": "Depressive disorder"},
    "J18": {"snomed": "233604007", "snomed_display": "Pneumonia"},
    "I50": {"snomed": "84114007", "snomed_display": "Heart failure"},
    "I25": {"snomed": "414545008", "snomed_display": "Ischemic heart disease"},
    "N18": {"snomed": "709044004", "snomed_display": "Chronic kidney disease"},
    "J44": {"snomed": "13645005", "snomed_display": "Chronic obstructive lung disease"},
    "C50": {"snomed": "254837009", "snomed_display": "Malignant neoplasm of breast"},
    "C61": {"snomed": "399068003", "snomed_display": "Malignant tumor of prostate"},
    "E66": {"snomed": "414916001", "snomed_display": "Obesity"},
    "F41": {"snomed": "197480006", "snomed_display": "Anxiety disorder"},
}

# SNOMED CT to ICD-10 reverse mapping
SNOMED_ICD10_MAP = {v["snomed"]: {"icd10": k, **v} for k, v in ICD10_SNOMED_MAP.items()}


class TerminologyMappingService:
    """Service for mapping between terminology systems."""
    
    @classmethod
    def icd10_to_snomed(cls, icd10_code: str) -> Optional[Dict[str, Any]]:
        """
        Map ICD-10 code to SNOMED CT.
        
        Args:
            icd10_code: ICD-10 code
            
        Returns:
            SNOMED CT mapping if found
        """
        normalized = icd10_code.upper().replace(".", "")
        
        # Check exact match first
        if normalized in ICD10_SNOMED_MAP:
            mapping = ICD10_SNOMED_MAP[normalized]
            return {
                "source_system": "http://hl7.org/fhir/sid/icd-10",
                "source_code": icd10_code,
                "target_system": "http://snomed.info/sct",
                "target_code": mapping["snomed"],
                "target_display": mapping["snomed_display"],
                "equivalence": "equivalent"
            }
        
        # Check prefix matches (e.g., I21.0 -> I21)
        for prefix_len in range(len(normalized) - 1, 2, -1):
            prefix = normalized[:prefix_len]
            if prefix in ICD10_SNOMED_MAP:
                mapping = ICD10_SNOMED_MAP[prefix]
                return {
                    "source_system": "http://hl7.org/fhir/sid/icd-10",
                    "source_code": icd10_code,
                    "target_system": "http://snomed.info/sct",
                    "target_code": mapping["snomed"],
                    "target_display": mapping["snomed_display"],
                    "equivalence": "wider"  # Less specific match
                }
        
        return None
    
    @classmethod
    def snomed_to_icd10(cls, snomed_code: str) -> Optional[Dict[str, Any]]:
        """
        Map SNOMED CT code to ICD-10.
        
        Args:
            snomed_code: SNOMED CT code
            
        Returns:
            ICD-10 mapping if found
        """
        if snomed_code in SNOMED_ICD10_MAP:
            mapping = SNOMED_ICD10_MAP[snomed_code]
            icd10_info = ICD10_CODES.get(mapping["icd10"], {})
            return {
                "source_system": "http://snomed.info/sct",
                "source_code": snomed_code,
                "source_display": mapping["snomed_display"],
                "target_system": "http://hl7.org/fhir/sid/icd-10",
                "target_code": mapping["icd10"],
                "target_display": icd10_info.get("description", ""),
                "equivalence": "equivalent"
            }
        
        return None


# TUSS (Tabela Unificada de Saúde Suplementar) codes
TUSS_CODES = {
    # Consultas
    "10101012": {"description": "Consulta em consultório (no horário normal)", "type": "consulta", "category": "Consultas"},
    "10101020": {"description": "Consulta em domicílio", "type": "consulta", "category": "Consultas"},
    "10101039": {"description": "Consulta em pronto socorro", "type": "consulta", "category": "Consultas"},
    
    # Procedimentos diagnósticos
    "40301010": {"description": "Hemograma com contagem de plaquetas", "type": "exame", "category": "Patologia Clínica"},
    "40301028": {"description": "Glicemia", "type": "exame", "category": "Patologia Clínica"},
    "40301036": {"description": "Creatinina", "type": "exame", "category": "Patologia Clínica"},
    "40301044": {"description": "Ureia", "type": "exame", "category": "Patologia Clínica"},
    "40301052": {"description": "Ácido úrico", "type": "exame", "category": "Patologia Clínica"},
    "40301060": {"description": "Colesterol total", "type": "exame", "category": "Patologia Clínica"},
    "40301079": {"description": "HDL colesterol", "type": "exame", "category": "Patologia Clínica"},
    "40301087": {"description": "LDL colesterol", "type": "exame", "category": "Patologia Clínica"},
    "40301095": {"description": "Triglicerídeos", "type": "exame", "category": "Patologia Clínica"},
    "40302016": {"description": "TSH", "type": "exame", "category": "Patologia Clínica"},
    "40302024": {"description": "T4 livre", "type": "exame", "category": "Patologia Clínica"},
    "40302032": {"description": "T3", "type": "exame", "category": "Patologia Clínica"},
    "40301117": {"description": "Hemoglobina glicada (HbA1c)", "type": "exame", "category": "Patologia Clínica"},
    "40301125": {"description": "PSA total", "type": "exame", "category": "Patologia Clínica"},
    
    # Exames de imagem
    "40808017": {"description": "Radiografia de tórax", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40808025": {"description": "Radiografia de coluna lombar", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40809013": {"description": "Ultrassonografia de abdome total", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40809021": {"description": "Ultrassonografia de tireoide", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40810010": {"description": "Tomografia computadorizada de crânio", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40810029": {"description": "Tomografia computadorizada de tórax", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40810037": {"description": "Tomografia computadorizada de abdome", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40811018": {"description": "Ressonância magnética de crânio", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40811026": {"description": "Ressonância magnética de coluna", "type": "imagem", "category": "Diagnóstico por Imagem"},
    "40811034": {"description": "Ressonância magnética de joelho", "type": "imagem", "category": "Diagnóstico por Imagem"},
    
    # Procedimentos cardiológicos
    "40101010": {"description": "Eletrocardiograma (ECG)", "type": "exame", "category": "Cardiologia"},
    "40101029": {"description": "Holter 24 horas", "type": "exame", "category": "Cardiologia"},
    "40101037": {"description": "MAPA (Monitorização Ambulatorial de Pressão Arterial)", "type": "exame", "category": "Cardiologia"},
    "40101045": {"description": "Teste ergométrico", "type": "exame", "category": "Cardiologia"},
    "40101053": {"description": "Ecocardiograma transtorácico", "type": "exame", "category": "Cardiologia"},
    
    # Procedimentos cirúrgicos
    "30101012": {"description": "Apendicectomia", "type": "cirurgia", "category": "Cirurgia do Aparelho Digestivo"},
    "30101020": {"description": "Colecistectomia", "type": "cirurgia", "category": "Cirurgia do Aparelho Digestivo"},
    "30201012": {"description": "Artroscopia de joelho diagnóstica", "type": "cirurgia", "category": "Cirurgia Ortopédica"},
    "30301010": {"description": "Cesariana", "type": "cirurgia", "category": "Obstetrícia"},
    "30301029": {"description": "Parto normal", "type": "cirurgia", "category": "Obstetrícia"},
    
    # Fisioterapia
    "50000012": {"description": "Sessão de fisioterapia motora", "type": "terapia", "category": "Fisioterapia"},
    "50000020": {"description": "Sessão de fisioterapia respiratória", "type": "terapia", "category": "Fisioterapia"},
    
    # Outros
    "20101012": {"description": "Curativo grau I", "type": "procedimento", "category": "Procedimentos Gerais"},
    "20101020": {"description": "Curativo grau II", "type": "procedimento", "category": "Procedimentos Gerais"},
    "20101039": {"description": "Sutura de ferimento (até 10 cm)", "type": "procedimento", "category": "Procedimentos Gerais"},
}


class TUSSService:
    """Service for TUSS code validation and lookup."""
    
    @classmethod
    def search(cls, term: str, procedure_type: Optional[str] = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search TUSS codes by description.
        
        Args:
            term: Search term
            procedure_type: Filter by type (consulta, exame, imagem, cirurgia, terapia, procedimento)
            max_results: Maximum results
            
        Returns:
            List of matching TUSS codes
        """
        term_lower = term.lower()
        results = []
        
        for code, info in TUSS_CODES.items():
            # Filter by type if specified
            if procedure_type and info["type"] != procedure_type:
                continue
                
            # Search in code, description and category
            if (term_lower in code or 
                term_lower in info["description"].lower() or
                term_lower in info["category"].lower()):
                results.append({
                    "code": code,
                    "description": info["description"],
                    "type": info["type"],
                    "category": info["category"],
                    "system": "http://www.ans.gov.br/tuss"
                })
                
                if len(results) >= max_results:
                    break
        
        return results
    
    @classmethod
    def validate(cls, code: str) -> Optional[Dict[str, Any]]:
        """
        Validate a TUSS code.
        
        Args:
            code: TUSS code to validate
            
        Returns:
            Code details if valid, None if invalid
        """
        if code in TUSS_CODES:
            info = TUSS_CODES[code]
            return {
                "code": code,
                "description": info["description"],
                "type": info["type"],
                "category": info["category"],
                "valid": True,
                "system": "http://www.ans.gov.br/tuss"
            }
        
        return None
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional[Dict[str, Any]]:
        """Get TUSS code details."""
        return cls.validate(code)
    
    @classmethod
    def get_by_type(cls, procedure_type: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get all TUSS codes of a specific type.
        
        Args:
            procedure_type: Type filter
            max_results: Maximum results
            
        Returns:
            List of TUSS codes
        """
        results = []
        for code, info in TUSS_CODES.items():
            if info["type"] == procedure_type:
                results.append({
                    "code": code,
                    "description": info["description"],
                    "type": info["type"],
                    "category": info["category"],
                    "system": "http://www.ans.gov.br/tuss"
                })
                
                if len(results) >= max_results:
                    break
        
        return results
