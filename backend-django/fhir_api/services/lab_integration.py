"""
Laboratory Integration Service - Integração com Sistemas de Laboratório
Recepção de resultados via HL7 FHIR, conversão e criação automática de DiagnosticReport
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StatusExame(Enum):
    """Status do resultado de exame"""
    REGISTERED = 'registered'
    PARTIAL = 'partial'
    PRELIMINARY = 'preliminary'
    FINAL = 'final'
    AMENDED = 'amended'
    CORRECTED = 'corrected'
    CANCELLED = 'cancelled'


class CategoriaExame(Enum):
    """Categorias de exames laboratoriais"""
    HEMATOLOGIA = 'hematology'
    BIOQUIMICA = 'chemistry'
    MICROBIOLOGIA = 'microbiology'
    IMUNOLOGIA = 'serology'
    URINA = 'urinalysis'
    HORMONIOS = 'hormones'
    COAGULACAO = 'coagulation'
    GASOMETRIA = 'blood-gas'


@dataclass
class ResultadoExame:
    """Estrutura de um resultado de exame"""
    codigo_loinc: str
    nome_exame: str
    valor: str
    unidade: str
    valor_referencia_min: Optional[float] = None
    valor_referencia_max: Optional[float] = None
    interpretacao: Optional[str] = None  # N=Normal, L=Low, H=High, A=Abnormal
    observacoes: Optional[str] = None


@dataclass
class LoteResultados:
    """Lote de resultados de laboratório"""
    id_requisicao: str
    paciente_id: str
    data_coleta: str
    data_resultado: str
    laboratorio: str
    responsavel_tecnico: str
    resultados: List[ResultadoExame]


class LaboratoryIntegrationService:
    """
    Serviço de integração com sistemas de laboratório.
    
    Suporta:
    - Recepção de resultados via FHIR Bundle
    - Conversão de HL7 v2.x ORU para FHIR
    - Criação automática de DiagnosticReport
    - Notificação de resultados críticos
    """
    
    # Valores críticos que requerem notificação imediata
    VALORES_CRITICOS = {
        '2339-0': {'min': 40, 'max': 500, 'nome': 'Glicose'},  # Glucose
        '2160-0': {'min': 0.4, 'max': 10, 'nome': 'Creatinina'},  # Creatinine
        '6298-4': {'min': 3.0, 'max': 6.5, 'nome': 'Potássio'},  # Potassium
        '2951-2': {'min': 125, 'max': 155, 'nome': 'Sódio'},  # Sodium
        '718-7': {'min': 7.0, 'max': 18.0, 'nome': 'Hemoglobina'},  # Hemoglobin
        '777-3': {'min': 10000, 'max': 500000, 'nome': 'Plaquetas'},  # Platelets
    }
    
    def __init__(self, fhir_service=None):
        self.fhir_service = fhir_service
        self.resultados_pendentes = []
    
    def processar_bundle_resultados(self, bundle: Dict) -> Dict:
        """
        Processa um Bundle FHIR com resultados de laboratório.
        
        Args:
            bundle: Bundle FHIR contendo DiagnosticReport e Observations
        
        Returns:
            Dict com status do processamento
        """
        if bundle.get('resourceType') != 'Bundle':
            raise ValueError("Esperado Bundle FHIR")
        
        resultados_processados = []
        alertas_criticos = []
        
        entries = bundle.get('entry', [])
        
        # Extrair DiagnosticReport e Observations
        diagnostic_reports = []
        observations = {}
        
        for entry in entries:
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')
            
            if resource_type == 'DiagnosticReport':
                diagnostic_reports.append(resource)
            elif resource_type == 'Observation':
                obs_id = resource.get('id')
                observations[obs_id] = resource
        
        # Processar cada DiagnosticReport
        for report in diagnostic_reports:
            resultado = self._processar_diagnostic_report(report, observations)
            resultados_processados.append(resultado)
            
            # Verificar valores críticos
            alertas = self._verificar_valores_criticos(resultado)
            if alertas:
                alertas_criticos.extend(alertas)
        
        logger.info(f"Processados {len(resultados_processados)} resultados, {len(alertas_criticos)} alertas críticos")
        
        return {
            'status': 'success',
            'resultados_processados': len(resultados_processados),
            'alertas_criticos': alertas_criticos,
            'timestamp': datetime.now().isoformat()
        }
    
    def _processar_diagnostic_report(self, report: Dict, observations: Dict) -> Dict:
        """Processa um DiagnosticReport individual"""
        
        # Extrair referências de observations
        result_refs = report.get('result', [])
        exames = []
        
        for ref in result_refs:
            obs_ref = ref.get('reference', '')
            obs_id = obs_ref.replace('Observation/', '')
            
            if obs_id in observations:
                obs = observations[obs_id]
                exame = self._extrair_resultado_observation(obs)
                if exame:
                    exames.append(exame)
        
        return {
            'id': report.get('id'),
            'status': report.get('status'),
            'category': self._extrair_categoria(report),
            'code': report.get('code', {}).get('coding', [{}])[0].get('display'),
            'subject': report.get('subject', {}).get('reference'),
            'effectiveDateTime': report.get('effectiveDateTime'),
            'issued': report.get('issued'),
            'performer': [p.get('reference') for p in report.get('performer', [])],
            'exames': exames
        }
    
    def _extrair_resultado_observation(self, obs: Dict) -> Optional[Dict]:
        """Extrai resultado de uma Observation"""
        try:
            codigo = obs.get('code', {}).get('coding', [{}])[0]
            
            # Extrair valor
            valor = None
            unidade = None
            
            if 'valueQuantity' in obs:
                vq = obs['valueQuantity']
                valor = vq.get('value')
                unidade = vq.get('unit', '')
            elif 'valueString' in obs:
                valor = obs['valueString']
            elif 'valueCodeableConcept' in obs:
                valor = obs['valueCodeableConcept'].get('coding', [{}])[0].get('display')
            
            # Extrair referência
            ref_range = obs.get('referenceRange', [{}])[0] if obs.get('referenceRange') else {}
            
            return {
                'codigo_loinc': codigo.get('code'),
                'nome': codigo.get('display'),
                'valor': valor,
                'unidade': unidade,
                'referencia_min': ref_range.get('low', {}).get('value'),
                'referencia_max': ref_range.get('high', {}).get('value'),
                'interpretacao': self._extrair_interpretacao(obs),
                'status': obs.get('status')
            }
        except Exception as e:
            logger.error(f"Erro ao extrair resultado: {str(e)}")
            return None
    
    def _extrair_interpretacao(self, obs: Dict) -> Optional[str]:
        """Extrai código de interpretação"""
        interpretation = obs.get('interpretation', [{}])
        if interpretation:
            return interpretation[0].get('coding', [{}])[0].get('code')
        return None
    
    def _extrair_categoria(self, report: Dict) -> str:
        """Extrai categoria do exame"""
        categories = report.get('category', [])
        for cat in categories:
            coding = cat.get('coding', [{}])[0]
            if coding.get('system') == 'http://terminology.hl7.org/CodeSystem/v2-0074':
                return coding.get('code', 'LAB')
        return 'LAB'
    
    def _verificar_valores_criticos(self, resultado: Dict) -> List[Dict]:
        """Verifica se há valores críticos nos resultados"""
        alertas = []
        
        for exame in resultado.get('exames', []):
            codigo = exame.get('codigo_loinc')
            valor = exame.get('valor')
            
            if codigo in self.VALORES_CRITICOS and valor is not None:
                critico = self.VALORES_CRITICOS[codigo]
                try:
                    valor_num = float(valor)
                    if valor_num < critico['min'] or valor_num > critico['max']:
                        alertas.append({
                            'tipo': 'VALOR_CRITICO',
                            'exame': critico['nome'],
                            'codigo_loinc': codigo,
                            'valor': valor_num,
                            'referencia': f"{critico['min']} - {critico['max']}",
                            'paciente': resultado.get('subject'),
                            'urgente': True
                        })
                except (ValueError, TypeError):
                    pass
        
        return alertas
    
    def converter_hl7v2_para_fhir(self, mensagem_hl7: str) -> Dict:
        """
        Converte mensagem HL7 v2.x ORU para Bundle FHIR.
        
        Args:
            mensagem_hl7: Mensagem HL7 v2.x no formato texto
        
        Returns:
            Bundle FHIR com DiagnosticReport e Observations
        """
        # Parser simplificado de HL7 v2.x
        # Em produção, usar biblioteca como hl7apy
        
        linhas = mensagem_hl7.strip().split('\n')
        segmentos = {}
        
        for linha in linhas:
            if '|' in linha:
                tipo = linha[:3]
                if tipo not in segmentos:
                    segmentos[tipo] = []
                segmentos[tipo].append(linha.split('|'))
        
        # Extrair informações do MSH
        msh = segmentos.get('MSH', [[]])[0]
        
        # Extrair informações do PID
        pid = segmentos.get('PID', [[]])[0]
        paciente_id = pid[3] if len(pid) > 3 else 'unknown'
        
        # Extrair resultados dos segmentos OBX
        observations = []
        for obx in segmentos.get('OBX', []):
            if len(obx) > 5:
                obs = {
                    'resourceType': 'Observation',
                    'id': f"obs-{len(observations)+1}",
                    'status': 'final',
                    'code': {
                        'coding': [{
                            'system': 'http://loinc.org',
                            'code': obx[3].split('^')[0] if '^' in obx[3] else obx[3],
                            'display': obx[3].split('^')[1] if '^' in obx[3] else obx[3]
                        }]
                    },
                    'valueQuantity': {
                        'value': float(obx[5]) if obx[5].replace('.', '').isdigit() else None,
                        'unit': obx[6] if len(obx) > 6 else ''
                    } if obx[5].replace('.', '').isdigit() else None,
                    'valueString': obx[5] if not obx[5].replace('.', '').isdigit() else None
                }
                observations.append(obs)
        
        # Criar DiagnosticReport
        diagnostic_report = {
            'resourceType': 'DiagnosticReport',
            'id': f"dr-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'status': 'final',
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': 'LAB'
                }]
            }],
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '11502-2',
                    'display': 'Laboratory report'
                }]
            },
            'subject': {
                'reference': f'Patient/{paciente_id}'
            },
            'effectiveDateTime': datetime.now().isoformat(),
            'issued': datetime.now().isoformat(),
            'result': [{'reference': f"Observation/{obs['id']}"} for obs in observations]
        }
        
        # Montar Bundle
        bundle = {
            'resourceType': 'Bundle',
            'type': 'transaction',
            'timestamp': datetime.now().isoformat(),
            'entry': [
                {'resource': diagnostic_report, 'request': {'method': 'POST', 'url': 'DiagnosticReport'}}
            ]
        }
        
        for obs in observations:
            bundle['entry'].append({
                'resource': obs,
                'request': {'method': 'POST', 'url': 'Observation'}
            })
        
        logger.info(f"Convertido HL7 v2.x para FHIR Bundle com {len(observations)} observations")
        
        return bundle
    
    def criar_diagnostic_report(
        self,
        paciente_id: str,
        categoria: CategoriaExame,
        resultados: List[ResultadoExame],
        data_coleta: str,
        laboratorio: str,
        responsavel: str
    ) -> Dict:
        """
        Cria DiagnosticReport FHIR a partir de resultados estruturados.
        
        Args:
            paciente_id: ID do paciente
            categoria: Categoria do exame
            resultados: Lista de resultados
            data_coleta: Data da coleta
            laboratorio: Nome do laboratório
            responsavel: Responsável técnico
        
        Returns:
            DiagnosticReport FHIR
        """
        # Criar Observations para cada resultado
        observations = []
        
        for i, resultado in enumerate(resultados):
            obs = {
                'resourceType': 'Observation',
                'id': f"obs-{i+1}",
                'status': 'final',
                'category': [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                        'code': 'laboratory'
                    }]
                }],
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': resultado.codigo_loinc,
                        'display': resultado.nome_exame
                    }]
                },
                'subject': {
                    'reference': f'Patient/{paciente_id}'
                },
                'effectiveDateTime': data_coleta,
                'valueQuantity': {
                    'value': float(resultado.valor) if resultado.valor.replace('.', '').replace('-', '').isdigit() else None,
                    'unit': resultado.unidade,
                    'system': 'http://unitsofmeasure.org'
                } if resultado.valor.replace('.', '').replace('-', '').isdigit() else None,
                'valueString': resultado.valor if not resultado.valor.replace('.', '').replace('-', '').isdigit() else None
            }
            
            # Adicionar range de referência
            if resultado.valor_referencia_min is not None or resultado.valor_referencia_max is not None:
                obs['referenceRange'] = [{
                    'low': {'value': resultado.valor_referencia_min, 'unit': resultado.unidade} if resultado.valor_referencia_min else None,
                    'high': {'value': resultado.valor_referencia_max, 'unit': resultado.unidade} if resultado.valor_referencia_max else None
                }]
            
            # Adicionar interpretação
            if resultado.interpretacao:
                obs['interpretation'] = [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': resultado.interpretacao
                    }]
                }]
            
            observations.append(obs)
        
        # Criar DiagnosticReport
        report = {
            'resourceType': 'DiagnosticReport',
            'status': 'final',
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': categoria.value.upper()
                }]
            }],
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '11502-2',
                    'display': 'Laboratory report'
                }]
            },
            'subject': {
                'reference': f'Patient/{paciente_id}'
            },
            'effectiveDateTime': data_coleta,
            'issued': datetime.now().isoformat(),
            'performer': [{
                'display': laboratorio
            }],
            'resultsInterpreter': [{
                'display': responsavel
            }],
            'result': [{'reference': f"#{obs['id']}"} for obs in observations],
            'contained': observations
        }
        
        return report
