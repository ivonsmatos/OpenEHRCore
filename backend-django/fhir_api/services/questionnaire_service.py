"""
Questionnaire Service - FHIR Questionnaires & Assessments

Sprint 36: Dynamic Forms Implementation

Features:
- Questionnaire CRUD operations
- QuestionnaireResponse management
- Score calculation for clinical assessments
- Pre-built clinical questionnaires (PHQ-9, GAD-7, etc.)
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """FHIR Questionnaire item types."""
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    INTEGER = "integer"
    DATE = "date"
    DATETIME = "dateTime"
    TIME = "time"
    STRING = "string"
    TEXT = "text"
    URL = "url"
    CHOICE = "choice"
    OPEN_CHOICE = "open-choice"
    ATTACHMENT = "attachment"
    REFERENCE = "reference"
    QUANTITY = "quantity"
    GROUP = "group"
    DISPLAY = "display"


@dataclass
class QuestionOption:
    """Answer option for choice questions."""
    value: str
    display: str
    score: Optional[int] = None  # For scored assessments


@dataclass
class QuestionItem:
    """Questionnaire item (question or group)."""
    link_id: str
    text: str
    type: QuestionType
    required: bool = False
    repeats: bool = False
    options: List[QuestionOption] = field(default_factory=list)
    items: List['QuestionItem'] = field(default_factory=list)  # Nested items
    enable_when: Optional[Dict] = None  # Conditional display
    initial_value: Optional[Any] = None
    max_length: Optional[int] = None
    code: Optional[str] = None  # LOINC/SNOMED code


@dataclass
class Questionnaire:
    """FHIR Questionnaire resource."""
    id: str
    title: str
    name: str  # Computer-friendly name
    status: str = "active"  # draft, active, retired
    version: str = "1.0.0"
    description: Optional[str] = None
    purpose: Optional[str] = None
    publisher: str = "OpenEHRCore"
    use_context: Optional[List[str]] = None
    items: List[QuestionItem] = field(default_factory=list)
    scoring_algorithm: Optional[str] = None  # sum, weighted, custom
    
    def to_fhir(self) -> Dict[str, Any]:
        """Convert to FHIR Questionnaire resource."""
        return {
            "resourceType": "Questionnaire",
            "id": self.id,
            "url": f"http://openehrcore.com.br/fhir/Questionnaire/{self.name}",
            "version": self.version,
            "name": self.name,
            "title": self.title,
            "status": self.status,
            "description": self.description,
            "purpose": self.purpose,
            "publisher": self.publisher,
            "item": [self._item_to_fhir(item) for item in self.items]
        }
    
    def _item_to_fhir(self, item: QuestionItem) -> Dict[str, Any]:
        """Convert item to FHIR format."""
        fhir_item = {
            "linkId": item.link_id,
            "text": item.text,
            "type": item.type.value,
            "required": item.required,
            "repeats": item.repeats
        }
        
        if item.code:
            fhir_item["code"] = [{
                "system": "http://loinc.org",
                "code": item.code
            }]
        
        if item.options:
            fhir_item["answerOption"] = [
                {
                    "valueCoding": {
                        "code": opt.value,
                        "display": opt.display
                    }
                }
                for opt in item.options
            ]
        
        if item.items:
            fhir_item["item"] = [self._item_to_fhir(i) for i in item.items]
        
        if item.max_length:
            fhir_item["maxLength"] = item.max_length
        
        return fhir_item


class QuestionnaireService:
    """
    FHIR Questionnaire Service.
    
    Manages questionnaires, responses, and scoring.
    """
    
    # In-memory storage (use database in production)
    _questionnaires: Dict[str, Questionnaire] = {}
    _responses: Dict[str, Dict] = {}
    
    @classmethod
    def _init_built_in_questionnaires(cls):
        """Initialize built-in clinical questionnaires."""
        if cls._questionnaires:
            return
        
        # =====================================================
        # PHQ-9: Patient Health Questionnaire (Depression)
        # =====================================================
        phq9_options = [
            QuestionOption("0", "Nenhuma vez", 0),
            QuestionOption("1", "Vários dias", 1),
            QuestionOption("2", "Mais da metade dos dias", 2),
            QuestionOption("3", "Quase todos os dias", 3),
        ]
        
        phq9 = Questionnaire(
            id="phq-9",
            name="PHQ9",
            title="PHQ-9: Questionário de Saúde do Paciente",
            description="Instrumento para rastreamento e medida da gravidade do transtorno depressivo maior",
            purpose="screening",
            scoring_algorithm="sum",
            items=[
                QuestionItem("phq1", "Pouco interesse ou prazer em fazer as coisas", QuestionType.CHOICE, True, options=phq9_options, code="44250-9"),
                QuestionItem("phq2", "Se sentir para baixo, deprimido/a ou sem perspectiva", QuestionType.CHOICE, True, options=phq9_options, code="44255-8"),
                QuestionItem("phq3", "Dificuldade para pegar no sono ou permanecer dormindo, ou dormir mais do que de costume", QuestionType.CHOICE, True, options=phq9_options, code="44259-0"),
                QuestionItem("phq4", "Se sentir cansado/a ou com pouca energia", QuestionType.CHOICE, True, options=phq9_options, code="44254-1"),
                QuestionItem("phq5", "Falta de apetite ou comendo demais", QuestionType.CHOICE, True, options=phq9_options, code="44251-7"),
                QuestionItem("phq6", "Se sentir mal consigo mesmo/a — ou achar que você é um fracasso ou que decepcionou sua família ou você mesmo/a", QuestionType.CHOICE, True, options=phq9_options, code="44258-2"),
                QuestionItem("phq7", "Dificuldade para se concentrar nas coisas, como ler o jornal ou ver televisão", QuestionType.CHOICE, True, options=phq9_options, code="44252-5"),
                QuestionItem("phq8", "Lentidão para se movimentar ou falar, a ponto das outras pessoas perceberem? Ou o oposto — Loss inquieto/a ou agitado/a", QuestionType.CHOICE, True, options=phq9_options, code="44253-3"),
                QuestionItem("phq9", "Pensar em se machucar de alguma maneira ou que seria melhor estar morto/a", QuestionType.CHOICE, True, options=phq9_options, code="44260-8"),
            ]
        )
        cls._questionnaires["phq-9"] = phq9
        
        # =====================================================
        # GAD-7: Generalized Anxiety Disorder
        # =====================================================
        gad7_options = [
            QuestionOption("0", "Nenhuma vez", 0),
            QuestionOption("1", "Vários dias", 1),
            QuestionOption("2", "Mais da metade dos dias", 2),
            QuestionOption("3", "Quase todos os dias", 3),
        ]
        
        gad7 = Questionnaire(
            id="gad-7",
            name="GAD7",
            title="GAD-7: Escala de Transtorno de Ansiedade Generalizada",
            description="Questionário de 7 itens para rastreamento de transtorno de ansiedade generalizada",
            purpose="screening",
            scoring_algorithm="sum",
            items=[
                QuestionItem("gad1", "Sentir-se nervoso/a, ansioso/a ou muito tenso/a", QuestionType.CHOICE, True, options=gad7_options, code="69725-0"),
                QuestionItem("gad2", "Não ser capaz de impedir ou de controlar as preocupações", QuestionType.CHOICE, True, options=gad7_options, code="68509-9"),
                QuestionItem("gad3", "Preocupar-se muito com diversas coisas", QuestionType.CHOICE, True, options=gad7_options, code="69733-4"),
                QuestionItem("gad4", "Dificuldade para relaxar", QuestionType.CHOICE, True, options=gad7_options, code="69734-2"),
                QuestionItem("gad5", "Ficar tão agitado/a que se torna difícil permanecer sentado/a", QuestionType.CHOICE, True, options=gad7_options, code="69735-9"),
                QuestionItem("gad6", "Ficar facilmente aborrecido/a ou irritado/a", QuestionType.CHOICE, True, options=gad7_options, code="69689-8"),
                QuestionItem("gad7", "Sentir medo como se algo horrível fosse acontecer", QuestionType.CHOICE, True, options=gad7_options, code="69736-7"),
            ]
        )
        cls._questionnaires["gad-7"] = gad7
        
        # =====================================================
        # Anamnese Geral
        # =====================================================
        anamnese = Questionnaire(
            id="anamnese-geral",
            name="AnamneseGeral",
            title="Anamnese Geral",
            description="Questionário de anamnese para primeira consulta",
            purpose="intake",
            items=[
                QuestionItem("queixa", "Qual é a sua queixa principal?", QuestionType.TEXT, True, max_length=1000),
                QuestionItem("duracao", "Há quanto tempo apresenta esses sintomas?", QuestionType.STRING, True),
                QuestionItem("historico", "Histórico de doenças (marque todas que se aplicam)", QuestionType.GROUP, items=[
                    QuestionItem("diabetes", "Diabetes", QuestionType.BOOLEAN),
                    QuestionItem("hipertensao", "Hipertensão", QuestionType.BOOLEAN),
                    QuestionItem("cardiopatia", "Doença cardíaca", QuestionType.BOOLEAN),
                    QuestionItem("asma", "Asma/Bronquite", QuestionType.BOOLEAN),
                    QuestionItem("cancer", "Câncer", QuestionType.BOOLEAN),
                    QuestionItem("depressao", "Depressão/Ansiedade", QuestionType.BOOLEAN),
                ]),
                QuestionItem("alergias", "Possui alguma alergia? Se sim, quais?", QuestionType.TEXT),
                QuestionItem("medicamentos", "Medicamentos em uso atual", QuestionType.TEXT),
                QuestionItem("cirurgias", "Já realizou alguma cirurgia? Se sim, quais e quando?", QuestionType.TEXT),
                QuestionItem("tabagismo", "É fumante?", QuestionType.CHOICE, options=[
                    QuestionOption("nao", "Não, nunca fumei"),
                    QuestionOption("ex", "Ex-fumante"),
                    QuestionOption("sim", "Sim, fumo atualmente"),
                ]),
                QuestionItem("alcool", "Consumo de bebidas alcoólicas", QuestionType.CHOICE, options=[
                    QuestionOption("nao", "Não bebo"),
                    QuestionOption("social", "Socialmente"),
                    QuestionOption("regular", "Regularmente"),
                ]),
                QuestionItem("exercicio", "Pratica exercícios físicos?", QuestionType.CHOICE, options=[
                    QuestionOption("nao", "Não pratico"),
                    QuestionOption("eventual", "Eventualmente"),
                    QuestionOption("regular", "Regularmente (3+ vezes/semana)"),
                ]),
            ]
        )
        cls._questionnaires["anamnese-geral"] = anamnese
        
        # =====================================================
        # Triagem COVID-19
        # =====================================================
        covid_triagem = Questionnaire(
            id="triagem-covid",
            name="TriagemCOVID",
            title="Triagem COVID-19",
            description="Questionário de triagem para sintomas de COVID-19",
            purpose="screening",
            items=[
                QuestionItem("febre", "Apresentou febre nos últimos 7 dias?", QuestionType.BOOLEAN, True),
                QuestionItem("tosse", "Tosse seca persistente?", QuestionType.BOOLEAN, True),
                QuestionItem("dispneia", "Dificuldade para respirar?", QuestionType.BOOLEAN, True),
                QuestionItem("anosmia", "Perda de olfato ou paladar?", QuestionType.BOOLEAN, True),
                QuestionItem("dor_garganta", "Dor de garganta?", QuestionType.BOOLEAN, True),
                QuestionItem("dor_corpo", "Dores no corpo?", QuestionType.BOOLEAN, True),
                QuestionItem("diarreia", "Diarreia?", QuestionType.BOOLEAN, True),
                QuestionItem("contato", "Teve contato com pessoa confirmada com COVID-19 nos últimos 14 dias?", QuestionType.BOOLEAN, True),
                QuestionItem("viagem", "Viajou para área de risco nos últimos 14 dias?", QuestionType.BOOLEAN),
            ]
        )
        cls._questionnaires["triagem-covid"] = covid_triagem
        
        # =====================================================
        # NPS (Net Promoter Score)
        # =====================================================
        nps = Questionnaire(
            id="nps",
            name="NPS",
            title="Pesquisa de Satisfação",
            description="Net Promoter Score - Avaliação da satisfação do paciente",
            purpose="satisfaction",
            items=[
                QuestionItem("recomendacao", "De 0 a 10, qual a probabilidade de você recomendar nossos serviços para um amigo ou familiar?", QuestionType.INTEGER, True),
                QuestionItem("motivo", "Por que você deu essa nota?", QuestionType.TEXT),
                QuestionItem("sugestao", "Tem alguma sugestão de melhoria?", QuestionType.TEXT),
            ]
        )
        cls._questionnaires["nps"] = nps
        
        logger.info(f"Initialized {len(cls._questionnaires)} questionnaires")
    
    @classmethod
    def list_questionnaires(cls, purpose: Optional[str] = None) -> List[Dict]:
        """List available questionnaires."""
        cls._init_built_in_questionnaires()
        
        questionnaires = list(cls._questionnaires.values())
        
        if purpose:
            questionnaires = [q for q in questionnaires if q.purpose == purpose]
        
        return [
            {
                "id": q.id,
                "name": q.name,
                "title": q.title,
                "description": q.description,
                "purpose": q.purpose,
                "item_count": len(q.items),
                "status": q.status
            }
            for q in questionnaires
        ]
    
    @classmethod
    def get_questionnaire(cls, questionnaire_id: str) -> Optional[Questionnaire]:
        """Get a questionnaire by ID."""
        cls._init_built_in_questionnaires()
        return cls._questionnaires.get(questionnaire_id)
    
    @classmethod
    def get_questionnaire_fhir(cls, questionnaire_id: str) -> Optional[Dict]:
        """Get questionnaire as FHIR resource."""
        questionnaire = cls.get_questionnaire(questionnaire_id)
        return questionnaire.to_fhir() if questionnaire else None
    
    @classmethod
    def create_questionnaire(cls, data: Dict) -> Questionnaire:
        """Create a custom questionnaire."""
        questionnaire_id = data.get("id", str(uuid.uuid4()))
        
        items = []
        for item_data in data.get("items", []):
            items.append(QuestionItem(
                link_id=item_data["linkId"],
                text=item_data["text"],
                type=QuestionType(item_data.get("type", "string")),
                required=item_data.get("required", False),
                options=[
                    QuestionOption(opt["value"], opt["display"], opt.get("score"))
                    for opt in item_data.get("options", [])
                ]
            ))
        
        questionnaire = Questionnaire(
            id=questionnaire_id,
            name=data.get("name", questionnaire_id),
            title=data["title"],
            description=data.get("description"),
            purpose=data.get("purpose"),
            items=items
        )
        
        cls._questionnaires[questionnaire_id] = questionnaire
        return questionnaire
    
    @classmethod
    def submit_response(
        cls,
        questionnaire_id: str,
        patient_id: str,
        answers: Dict[str, Any],
        practitioner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a questionnaire response.
        
        Args:
            questionnaire_id: ID of the questionnaire
            patient_id: Patient who completed the questionnaire
            answers: Dictionary of link_id -> answer
            practitioner_id: Optional practitioner who administered
            
        Returns:
            QuestionnaireResponse resource
        """
        questionnaire = cls.get_questionnaire(questionnaire_id)
        if not questionnaire:
            raise ValueError(f"Questionnaire not found: {questionnaire_id}")
        
        response_id = str(uuid.uuid4())
        
        # Build response items
        response_items = []
        for link_id, answer in answers.items():
            item = {
                "linkId": link_id,
                "answer": [cls._format_answer(answer)]
            }
            response_items.append(item)
        
        # Calculate score if applicable
        score = None
        interpretation = None
        if questionnaire.scoring_algorithm == "sum":
            score = cls._calculate_sum_score(questionnaire, answers)
            interpretation = cls._interpret_score(questionnaire.id, score)
        
        # Build FHIR QuestionnaireResponse
        response = {
            "resourceType": "QuestionnaireResponse",
            "id": response_id,
            "questionnaire": f"Questionnaire/{questionnaire_id}",
            "status": "completed",
            "subject": {"reference": f"Patient/{patient_id}"},
            "authored": datetime.now().isoformat(),
            "item": response_items
        }
        
        if practitioner_id:
            response["author"] = {"reference": f"Practitioner/{practitioner_id}"}
        
        # Store response
        cls._responses[response_id] = {
            "response": response,
            "score": score,
            "interpretation": interpretation,
            "questionnaire_id": questionnaire_id,
            "patient_id": patient_id
        }
        
        return {
            "id": response_id,
            "questionnaire": questionnaire_id,
            "patient": patient_id,
            "status": "completed",
            "score": score,
            "interpretation": interpretation,
            "response": response
        }
    
    @classmethod
    def _format_answer(cls, answer: Any) -> Dict:
        """Format answer for FHIR."""
        if isinstance(answer, bool):
            return {"valueBoolean": answer}
        elif isinstance(answer, int):
            return {"valueInteger": answer}
        elif isinstance(answer, float):
            return {"valueDecimal": answer}
        elif isinstance(answer, str):
            # Check if it's a coded answer
            if answer.isdigit() or len(answer) <= 3:
                return {"valueCoding": {"code": answer}}
            return {"valueString": answer}
        else:
            return {"valueString": str(answer)}
    
    @classmethod
    def _calculate_sum_score(cls, questionnaire: Questionnaire, answers: Dict) -> int:
        """Calculate sum score for scored questionnaires."""
        total = 0
        
        for item in questionnaire.items:
            if item.link_id in answers:
                answer = answers[item.link_id]
                # Find score for this answer
                for opt in item.options:
                    if opt.value == str(answer) and opt.score is not None:
                        total += opt.score
                        break
        
        return total
    
    @classmethod
    def _interpret_score(cls, questionnaire_id: str, score: int) -> Dict:
        """Interpret score based on questionnaire type."""
        interpretations = {
            "phq-9": [
                (0, 4, "Mínimo", "Nenhum ou mínimo sintoma de depressão"),
                (5, 9, "Leve", "Sintomas leves de depressão"),
                (10, 14, "Moderado", "Sintomas moderados de depressão"),
                (15, 19, "Moderadamente severo", "Sintomas moderadamente severos"),
                (20, 27, "Severo", "Sintomas severos de depressão"),
            ],
            "gad-7": [
                (0, 4, "Mínimo", "Ansiedade mínima"),
                (5, 9, "Leve", "Ansiedade leve"),
                (10, 14, "Moderado", "Ansiedade moderada"),
                (15, 21, "Severo", "Ansiedade severa"),
            ]
        }
        
        ranges = interpretations.get(questionnaire_id, [])
        
        for min_score, max_score, severity, description in ranges:
            if min_score <= score <= max_score:
                return {
                    "severity": severity,
                    "description": description,
                    "score": score,
                    "max_score": ranges[-1][1] if ranges else None
                }
        
        return {"severity": "unknown", "score": score}
    
    @classmethod
    def get_responses(
        cls,
        patient_id: Optional[str] = None,
        questionnaire_id: Optional[str] = None
    ) -> List[Dict]:
        """Get questionnaire responses with optional filters."""
        responses = list(cls._responses.values())
        
        if patient_id:
            responses = [r for r in responses if r["patient_id"] == patient_id]
        
        if questionnaire_id:
            responses = [r for r in responses if r["questionnaire_id"] == questionnaire_id]
        
        return responses
    
    @classmethod
    def get_response(cls, response_id: str) -> Optional[Dict]:
        """Get a specific response by ID."""
        return cls._responses.get(response_id)


# Singleton
_questionnaire_service = None


def get_questionnaire_service() -> QuestionnaireService:
    """Get questionnaire service singleton."""
    global _questionnaire_service
    if _questionnaire_service is None:
        _questionnaire_service = QuestionnaireService()
        QuestionnaireService._init_built_in_questionnaires()
    return _questionnaire_service
