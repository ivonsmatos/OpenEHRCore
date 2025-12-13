"""
Pharmacy Integration Service - Integração com Sistema de Farmácia
Gestão de dispensação de medicamentos e controle de estoque
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StatusDispensacao(Enum):
    """Status da dispensação"""
    PREPARATION = 'preparation'  # Em preparação
    IN_PROGRESS = 'in-progress'  # Em andamento
    CANCELLED = 'cancelled'  # Cancelada
    ON_HOLD = 'on-hold'  # Em espera
    COMPLETED = 'completed'  # Concluída
    ENTERED_IN_ERROR = 'entered-in-error'  # Erro de entrada
    STOPPED = 'stopped'  # Parada
    DECLINED = 'declined'  # Recusada
    UNKNOWN = 'unknown'  # Desconhecido


class TipoMedicamento(Enum):
    """Tipos de medicamento por controle"""
    COMUM = 'comum'
    CONTROLADO_C1 = 'controlado_c1'  # Lista C1 - Psicotrópicos
    CONTROLADO_C2 = 'controlado_c2'  # Lista C2 - Retinoides
    CONTROLADO_C4 = 'controlado_c4'  # Lista C4 - Anorexígenos
    CONTROLADO_A = 'controlado_a'    # Lista A - Entorpecentes
    CONTROLADO_B = 'controlado_b'    # Lista B - Psicotrópicos
    ANTIMICROBIANO = 'antimicrobiano'
    ALTA_VIGILANCIA = 'alta_vigilancia'


@dataclass
class ItemPrescricao:
    """Item de prescrição para dispensação"""
    medication_request_id: str
    medicamento_codigo: str
    medicamento_nome: str
    forma_farmaceutica: str
    concentracao: str
    quantidade_prescrita: float
    unidade: str
    posologia: str
    via_administracao: str
    tipo_controle: TipoMedicamento = TipoMedicamento.COMUM


@dataclass
class ItemDispensacao:
    """Item dispensado"""
    medicamento_codigo: str
    medicamento_nome: str
    lote: str
    validade: str
    quantidade_dispensada: float
    unidade: str
    fabricante: Optional[str] = None
    registro_anvisa: Optional[str] = None


class PharmacyIntegrationService:
    """
    Serviço de integração com farmácia hospitalar.
    
    Funcionalidades:
    - Recebimento de prescrições (MedicationRequest)
    - Registro de dispensações (MedicationDispense)
    - Controle de estoque
    - Alertas de medicamentos controlados
    - Verificação de interações
    """
    
    def __init__(self, fhir_service=None):
        self.fhir_service = fhir_service
        self.dispensacoes_pendentes = []
    
    def criar_medication_dispense(
        self,
        medication_request_id: str,
        patient_id: str,
        item: ItemDispensacao,
        performer_id: str,
        quando_preparado: Optional[str] = None,
        quando_entregue: Optional[str] = None,
        notas: Optional[str] = None
    ) -> Dict:
        """
        Cria recurso MedicationDispense FHIR.
        
        Args:
            medication_request_id: ID da prescrição original
            patient_id: ID do paciente
            item: Item dispensado
            performer_id: ID do farmacêutico
            quando_preparado: Data/hora da preparação
            quando_entregue: Data/hora da entrega
            notas: Observações
        
        Returns:
            MedicationDispense FHIR
        """
        status = StatusDispensacao.COMPLETED if quando_entregue else StatusDispensacao.PREPARATION
        
        dispense = {
            'resourceType': 'MedicationDispense',
            'status': status.value,
            'medicationCodeableConcept': {
                'coding': [{
                    'system': 'http://www.anvisa.gov.br/medicamentos',
                    'code': item.medicamento_codigo,
                    'display': item.medicamento_nome
                }]
            },
            'subject': {
                'reference': f'Patient/{patient_id}'
            },
            'authorizingPrescription': [{
                'reference': f'MedicationRequest/{medication_request_id}'
            }],
            'quantity': {
                'value': item.quantidade_dispensada,
                'unit': item.unidade,
                'system': 'http://unitsofmeasure.org'
            },
            'daysSupply': {
                'value': 30,  # Calcular baseado na posologia
                'unit': 'd'
            },
            'whenPrepared': quando_preparado or datetime.now().isoformat(),
            'performer': [{
                'actor': {
                    'reference': f'Practitioner/{performer_id}'
                }
            }]
        }
        
        # Adicionar informações do lote
        dispense['extension'] = [
            {
                'url': 'http://hl7.org/fhir/StructureDefinition/medication-batch',
                'extension': [
                    {
                        'url': 'lotNumber',
                        'valueString': item.lote
                    },
                    {
                        'url': 'expirationDate',
                        'valueDateTime': item.validade
                    }
                ]
            }
        ]
        
        if item.fabricante:
            dispense['extension'].append({
                'url': 'http://hl7.org/fhir/StructureDefinition/medication-manufacturer',
                'valueString': item.fabricante
            })
        
        if quando_entregue:
            dispense['whenHandedOver'] = quando_entregue
        
        if notas:
            dispense['note'] = [{'text': notas}]
        
        logger.info(f"MedicationDispense criado para MedicationRequest {medication_request_id}")
        
        return dispense
    
    def processar_prescricao(
        self,
        medication_request: Dict
    ) -> Dict:
        """
        Processa prescrição recebida e prepara para dispensação.
        
        Args:
            medication_request: Recurso MedicationRequest FHIR
        
        Returns:
            Status do processamento
        """
        request_id = medication_request.get('id')
        status = medication_request.get('status')
        
        if status != 'active':
            return {
                'status': 'rejected',
                'reason': f'Prescrição com status {status} - apenas prescrições ativas podem ser processadas'
            }
        
        # Extrair informações do medicamento
        medication = medication_request.get('medicationCodeableConcept', {})
        coding = medication.get('coding', [{}])[0]
        
        # Verificar tipo de controle
        tipo_controle = self._verificar_controle_medicamento(coding.get('code', ''))
        
        # Verificar estoque
        quantidade_solicitada = self._extrair_quantidade(medication_request)
        disponibilidade = self._verificar_estoque(coding.get('code'), quantidade_solicitada)
        
        resultado = {
            'status': 'processed',
            'medication_request_id': request_id,
            'medicamento': coding.get('display'),
            'codigo': coding.get('code'),
            'tipo_controle': tipo_controle.value,
            'quantidade_solicitada': quantidade_solicitada,
            'disponibilidade': disponibilidade,
            'alertas': []
        }
        
        # Adicionar alertas específicos
        if tipo_controle in [TipoMedicamento.CONTROLADO_A, TipoMedicamento.CONTROLADO_B]:
            resultado['alertas'].append({
                'tipo': 'MEDICAMENTO_CONTROLADO',
                'mensagem': f'Medicamento controlado {tipo_controle.value} - requer receituário especial',
                'severidade': 'warning'
            })
        
        if tipo_controle == TipoMedicamento.ALTA_VIGILANCIA:
            resultado['alertas'].append({
                'tipo': 'ALTA_VIGILANCIA',
                'mensagem': 'Medicamento de alta vigilância - verificar dupla conferência',
                'severidade': 'warning'
            })
        
        if not disponibilidade.get('disponivel'):
            resultado['alertas'].append({
                'tipo': 'ESTOQUE_INSUFICIENTE',
                'mensagem': f"Estoque insuficiente. Disponível: {disponibilidade.get('quantidade_disponivel')}",
                'severidade': 'error'
            })
        
        return resultado
    
    def _verificar_controle_medicamento(self, codigo: str) -> TipoMedicamento:
        """Verifica tipo de controle do medicamento baseado no código"""
        # Em produção, consultar tabela de medicamentos controlados ANVISA
        # Simulação baseada em prefixos
        if codigo.startswith('A'):
            return TipoMedicamento.CONTROLADO_A
        elif codigo.startswith('B'):
            return TipoMedicamento.CONTROLADO_B
        elif codigo.startswith('C1'):
            return TipoMedicamento.CONTROLADO_C1
        elif codigo.startswith('AM'):
            return TipoMedicamento.ANTIMICROBIANO
        return TipoMedicamento.COMUM
    
    def _extrair_quantidade(self, medication_request: Dict) -> float:
        """Extrai quantidade solicitada da prescrição"""
        dispense_request = medication_request.get('dispenseRequest', {})
        quantity = dispense_request.get('quantity', {})
        return quantity.get('value', 0)
    
    def _verificar_estoque(self, codigo_medicamento: str, quantidade: float) -> Dict:
        """
        Verifica disponibilidade em estoque.
        Em produção, integrar com sistema de estoque real.
        """
        # Simulação de estoque
        return {
            'disponivel': True,
            'quantidade_disponivel': 100,
            'lotes': [
                {'lote': 'ABC123', 'quantidade': 50, 'validade': '2025-06-30'},
                {'lote': 'DEF456', 'quantidade': 50, 'validade': '2025-12-31'}
            ]
        }
    
    def atualizar_estoque(
        self,
        codigo_medicamento: str,
        lote: str,
        quantidade: float,
        tipo_movimento: str  # 'entrada', 'saida', 'ajuste'
    ) -> Dict:
        """
        Atualiza estoque após dispensação ou recebimento.
        
        Args:
            codigo_medicamento: Código do medicamento
            lote: Número do lote
            quantidade: Quantidade movimentada
            tipo_movimento: Tipo de movimento
        
        Returns:
            Status da atualização
        """
        logger.info(f"Movimento de estoque: {tipo_movimento} - {codigo_medicamento} - Lote {lote} - Qtd: {quantidade}")
        
        return {
            'status': 'success',
            'codigo_medicamento': codigo_medicamento,
            'lote': lote,
            'tipo_movimento': tipo_movimento,
            'quantidade': quantidade,
            'timestamp': datetime.now().isoformat()
        }
    
    def listar_dispensacoes_pendentes(self, unidade_id: Optional[str] = None) -> List[Dict]:
        """
        Lista dispensações pendentes de entrega.
        
        Args:
            unidade_id: Filtro por unidade de internação
        
        Returns:
            Lista de dispensações pendentes
        """
        # Em produção, consultar banco de dados
        return self.dispensacoes_pendentes
    
    def confirmar_entrega(
        self,
        dispense_id: str,
        recebido_por: str,
        data_entrega: Optional[str] = None
    ) -> Dict:
        """
        Confirma entrega do medicamento ao paciente/unidade.
        
        Args:
            dispense_id: ID da dispensação
            recebido_por: Nome de quem recebeu
            data_entrega: Data/hora da entrega
        
        Returns:
            Status da confirmação
        """
        return {
            'status': 'confirmed',
            'dispense_id': dispense_id,
            'recebido_por': recebido_por,
            'data_entrega': data_entrega or datetime.now().isoformat(),
            'message': 'Entrega confirmada com sucesso'
        }
    
    def registrar_devolucao(
        self,
        dispense_id: str,
        quantidade_devolvida: float,
        motivo: str,
        condicao_medicamento: str  # 'bom_estado', 'danificado', 'vencido'
    ) -> Dict:
        """
        Registra devolução de medicamento à farmácia.
        
        Args:
            dispense_id: ID da dispensação original
            quantidade_devolvida: Quantidade
            motivo: Motivo da devolução
            condicao_medicamento: Estado do medicamento devolvido
        
        Returns:
            Status da devolução
        """
        reincorporar_estoque = condicao_medicamento == 'bom_estado'
        
        return {
            'status': 'registered',
            'dispense_id': dispense_id,
            'quantidade_devolvida': quantidade_devolvida,
            'motivo': motivo,
            'condicao': condicao_medicamento,
            'reincorporado_estoque': reincorporar_estoque,
            'timestamp': datetime.now().isoformat()
        }
    
    def gerar_relatorio_consumo(
        self,
        data_inicio: str,
        data_fim: str,
        unidade_id: Optional[str] = None,
        tipo_medicamento: Optional[TipoMedicamento] = None
    ) -> Dict:
        """
        Gera relatório de consumo de medicamentos.
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
            unidade_id: Filtro por unidade
            tipo_medicamento: Filtro por tipo
        
        Returns:
            Relatório de consumo
        """
        return {
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim
            },
            'filtros': {
                'unidade': unidade_id,
                'tipo': tipo_medicamento.value if tipo_medicamento else None
            },
            'totais': {
                'dispensacoes': 150,
                'valor_total': 12500.00,
                'medicamentos_distintos': 45
            },
            'top_medicamentos': [
                {'nome': 'Dipirona 500mg', 'quantidade': 500, 'valor': 250.00},
                {'nome': 'Omeprazol 20mg', 'quantidade': 300, 'valor': 450.00},
                {'nome': 'Captopril 25mg', 'quantidade': 200, 'valor': 180.00}
            ],
            'alertas': {
                'medicamentos_vencendo': 5,
                'estoque_baixo': 12,
                'controlados_dispensados': 25
            },
            'gerado_em': datetime.now().isoformat()
        }
    
    def verificar_interacoes_prescricao(
        self,
        medication_requests: List[Dict]
    ) -> List[Dict]:
        """
        Verifica interações entre medicamentos da prescrição.
        
        Args:
            medication_requests: Lista de prescrições
        
        Returns:
            Lista de interações encontradas
        """
        # Extrair códigos dos medicamentos
        codigos = []
        for mr in medication_requests:
            medication = mr.get('medicationCodeableConcept', {})
            coding = medication.get('coding', [{}])[0]
            codigos.append(coding.get('code'))
        
        # Em produção, consultar base de interações (DrugBank, FDA, etc.)
        # Simulação de algumas interações conhecidas
        interacoes = []
        
        # Exemplo: verificar combinações perigosas
        if 'WARFARINA' in str(codigos) and 'AAS' in str(codigos):
            interacoes.append({
                'tipo': 'grave',
                'medicamento_1': 'Varfarina',
                'medicamento_2': 'Ácido Acetilsalicílico',
                'descricao': 'Aumento do risco de sangramento',
                'recomendacao': 'Evitar uso concomitante ou monitorar INR frequentemente'
            })
        
        return interacoes
