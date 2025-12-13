"""
TISS Service - Troca de Informação em Saúde Suplementar (ANS)
Geração de guias TISS para faturamento de operadoras de saúde no Brasil
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TipoGuia(Enum):
    """Tipos de guias TISS"""
    CONSULTA = 'consulta'
    SADT = 'sadt'  # SP/SADT - Serviço Profissional / Serviço Auxiliar de Diagnóstico e Terapia
    INTERNACAO = 'internacao'
    HONORARIOS = 'honorarios'
    ODONTOLOGIA = 'odontologia'
    ANEXO_QUIMIOTERAPIA = 'anexo_quimioterapia'
    ANEXO_RADIOTERAPIA = 'anexo_radioterapia'
    RESUMO_INTERNACAO = 'resumo_internacao'


class StatusGuia(Enum):
    """Status da guia TISS"""
    RASCUNHO = 'rascunho'
    PENDENTE = 'pendente'
    ENVIADA = 'enviada'
    AUTORIZADA = 'autorizada'
    NEGADA = 'negada'
    PARCIALMENTE_AUTORIZADA = 'parcialmente_autorizada'
    FATURADA = 'faturada'
    PAGA = 'paga'
    GLOSADA = 'glosada'


@dataclass
class DadosBeneficiario:
    """Dados do beneficiário/paciente para TISS"""
    numero_carteira: str
    nome: str
    data_nascimento: str
    cpf: Optional[str] = None
    cns: Optional[str] = None  # Cartão Nacional de Saúde


@dataclass
class DadosPrestador:
    """Dados do prestador de serviços"""
    codigo_na_operadora: str
    nome: str
    cnpj: str
    cnes: str  # Cadastro Nacional de Estabelecimentos de Saúde
    conselho_profissional: Optional[str] = None
    numero_conselho: Optional[str] = None
    uf_conselho: Optional[str] = None


@dataclass  
class Procedimento:
    """Procedimento TISS"""
    codigo: str  # Código TUSS ou CBHPM
    descricao: str
    quantidade: int = 1
    valor_unitario: float = 0.0
    via_acesso: Optional[str] = None  # Para cirurgias
    tecnica: Optional[str] = None


class TISSService:
    """
    Serviço para geração e validação de guias TISS.
    Implementa padrões ANS para troca de informação em saúde suplementar.
    """
    
    # Versão do padrão TISS implementado
    VERSAO_TISS = '4.01.00'
    
    # Tabelas de procedimentos suportadas
    TABELAS_PROCEDIMENTOS = {
        '22': 'TUSS - Terminologia Unificada da Saúde Suplementar',
        '19': 'CBHPM - Classificação Brasileira Hierarquizada de Procedimentos Médicos',
        '90': 'Tabela própria da operadora',
        '98': 'Tabela própria do prestador'
    }
    
    def __init__(self, prestador: Optional[DadosPrestador] = None):
        self.prestador = prestador
        self.guias_geradas = []
    
    def gerar_guia_consulta(
        self,
        beneficiario: DadosBeneficiario,
        data_atendimento: str,
        tipo_consulta: str,
        procedimento: Procedimento,
        numero_guia_operadora: Optional[str] = None,
        observacoes: Optional[str] = None
    ) -> Dict:
        """
        Gera Guia de Consulta TISS
        
        Args:
            beneficiario: Dados do paciente/beneficiário
            data_atendimento: Data no formato YYYY-MM-DD
            tipo_consulta: '1' (primeira), '2' (seguimento), '3' (pré-natal), '4' (puericultura)
            procedimento: Procedimento realizado (código TUSS/CBHPM)
            numero_guia_operadora: Número autorização da operadora
            observacoes: Observações adicionais
        
        Returns:
            Dict com estrutura da guia TISS
        """
        guia = {
            'tipo': TipoGuia.CONSULTA.value,
            'versao_tiss': self.VERSAO_TISS,
            'numero_guia_prestador': self._gerar_numero_guia(),
            'data_geracao': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'status': StatusGuia.RASCUNHO.value,
            
            'cabecalho': {
                'registro_ans': '',  # Registro ANS da operadora
                'numero_guia_operadora': numero_guia_operadora or ''
            },
            
            'dados_beneficiario': {
                'numero_carteira': beneficiario.numero_carteira,
                'nome': beneficiario.nome,
                'data_nascimento': beneficiario.data_nascimento,
                'cpf': beneficiario.cpf,
                'cns': beneficiario.cns
            },
            
            'dados_solicitante': {
                'contratado_solicitante': {
                    'codigo_na_operadora': self.prestador.codigo_na_operadora if self.prestador else '',
                    'nome': self.prestador.nome if self.prestador else ''
                },
                'profissional_solicitante': {
                    'nome': self.prestador.nome if self.prestador else '',
                    'conselho': self.prestador.conselho_profissional if self.prestador else 'CRM',
                    'numero_conselho': self.prestador.numero_conselho if self.prestador else '',
                    'uf': self.prestador.uf_conselho if self.prestador else ''
                }
            },
            
            'dados_atendimento': {
                'data_atendimento': data_atendimento,
                'tipo_consulta': tipo_consulta,
                'indicacao_acidente': '9',  # 9 = Não acidente
                'procedimento': {
                    'codigo_tabela': '22',  # TUSS
                    'codigo_procedimento': procedimento.codigo,
                    'descricao': procedimento.descricao,
                    'quantidade': procedimento.quantidade,
                    'valor_unitario': procedimento.valor_unitario,
                    'valor_total': procedimento.valor_unitario * procedimento.quantidade
                }
            },
            
            'observacoes': observacoes or '',
            
            'valor_total': procedimento.valor_unitario * procedimento.quantidade
        }
        
        self.guias_geradas.append(guia)
        logger.info(f"Guia de Consulta gerada: {guia['numero_guia_prestador']}")
        
        return guia
    
    def gerar_guia_sadt(
        self,
        beneficiario: DadosBeneficiario,
        procedimentos: List[Procedimento],
        data_solicitacao: str,
        indicacao_clinica: str,
        carater_atendimento: str = 'E',  # E=Eletivo, U=Urgência
        numero_guia_operadora: Optional[str] = None
    ) -> Dict:
        """
        Gera Guia SP/SADT (Serviço Profissional / Serviço Auxiliar de Diagnóstico e Terapia)
        Usada para exames, procedimentos ambulatoriais, terapias.
        
        Args:
            beneficiario: Dados do paciente
            procedimentos: Lista de procedimentos
            data_solicitacao: Data da solicitação
            indicacao_clinica: Indicação clínica/CID
            carater_atendimento: 'E' (eletivo) ou 'U' (urgência)
            numero_guia_operadora: Número da autorização
        
        Returns:
            Dict com estrutura da guia SADT
        """
        procs_formatados = []
        valor_total = 0
        
        for i, proc in enumerate(procedimentos, 1):
            valor_proc = proc.valor_unitario * proc.quantidade
            valor_total += valor_proc
            procs_formatados.append({
                'sequencial': i,
                'data_execucao': datetime.now().strftime('%Y-%m-%d'),
                'hora_inicial': None,
                'hora_final': None,
                'codigo_tabela': '22',
                'codigo_procedimento': proc.codigo,
                'descricao': proc.descricao,
                'quantidade_executada': proc.quantidade,
                'via_acesso': proc.via_acesso or '1',  # 1 = Única
                'tecnica': proc.tecnica or '1',  # 1 = Convencional
                'reducao_acrescimo': 1.0,
                'valor_unitario': proc.valor_unitario,
                'valor_total': valor_proc
            })
        
        guia = {
            'tipo': TipoGuia.SADT.value,
            'versao_tiss': self.VERSAO_TISS,
            'numero_guia_prestador': self._gerar_numero_guia(),
            'data_geracao': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'status': StatusGuia.RASCUNHO.value,
            
            'cabecalho': {
                'registro_ans': '',
                'numero_guia_operadora': numero_guia_operadora or ''
            },
            
            'dados_beneficiario': {
                'numero_carteira': beneficiario.numero_carteira,
                'nome': beneficiario.nome,
                'data_nascimento': beneficiario.data_nascimento
            },
            
            'dados_solicitacao': {
                'data_solicitacao': data_solicitacao,
                'carater_atendimento': carater_atendimento,
                'indicacao_clinica': indicacao_clinica
            },
            
            'dados_executante': {
                'contratado': {
                    'codigo_na_operadora': self.prestador.codigo_na_operadora if self.prestador else '',
                    'nome': self.prestador.nome if self.prestador else '',
                    'cnes': self.prestador.cnes if self.prestador else ''
                }
            },
            
            'procedimentos_executados': procs_formatados,
            
            'valor_total_procedimentos': valor_total,
            'valor_total_taxas': 0.0,
            'valor_total_materiais': 0.0,
            'valor_total_medicamentos': 0.0,
            'valor_total_gases_medicinais': 0.0,
            'valor_total_geral': valor_total
        }
        
        self.guias_geradas.append(guia)
        logger.info(f"Guia SP/SADT gerada: {guia['numero_guia_prestador']} com {len(procedimentos)} procedimentos")
        
        return guia
    
    def gerar_guia_internacao(
        self,
        beneficiario: DadosBeneficiario,
        data_internacao: str,
        hora_internacao: str,
        carater_internacao: str,  # 1=Eletiva, 2=Urgência/Emergência
        tipo_internacao: str,  # 1=Clínica, 2=Cirúrgica, 3=Obstétrica, 4=Pediátrica, 5=Psiquiátrica
        regime_internacao: str,  # 1=Hospitalar, 2=Hospital-dia, 3=Domiciliar
        procedimento_principal: Procedimento,
        cid_principal: str,
        previsao_diarias: int,
        numero_guia_operadora: Optional[str] = None,
        data_alta: Optional[str] = None,
        motivo_alta: Optional[str] = None
    ) -> Dict:
        """
        Gera Guia de Internação TISS
        
        Args:
            beneficiario: Dados do paciente
            data_internacao: Data de admissão
            hora_internacao: Hora de admissão
            carater_internacao: Tipo de urgência
            tipo_internacao: Especialidade
            regime_internacao: Regime de internação
            procedimento_principal: Procedimento principal
            cid_principal: CID-10 do diagnóstico principal
            previsao_diarias: Previsão de dias de internação
            numero_guia_operadora: Autorização prévia
            data_alta: Data de alta (se já ocorreu)
            motivo_alta: Código do motivo de alta
        
        Returns:
            Dict com estrutura da guia de internação
        """
        guia = {
            'tipo': TipoGuia.INTERNACAO.value,
            'versao_tiss': self.VERSAO_TISS,
            'numero_guia_prestador': self._gerar_numero_guia(),
            'data_geracao': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'status': StatusGuia.RASCUNHO.value,
            
            'cabecalho': {
                'registro_ans': '',
                'numero_guia_operadora': numero_guia_operadora or ''
            },
            
            'dados_beneficiario': {
                'numero_carteira': beneficiario.numero_carteira,
                'nome': beneficiario.nome,
                'data_nascimento': beneficiario.data_nascimento,
                'cns': beneficiario.cns
            },
            
            'dados_internacao': {
                'carater_internacao': carater_internacao,
                'tipo_internacao': tipo_internacao,
                'regime_internacao': regime_internacao,
                'data_internacao': data_internacao,
                'hora_internacao': hora_internacao,
                'previsao_diarias': previsao_diarias,
                'indicacao_clinica': '',
                'cid_principal': cid_principal
            },
            
            'dados_hospital': {
                'codigo_na_operadora': self.prestador.codigo_na_operadora if self.prestador else '',
                'nome': self.prestador.nome if self.prestador else '',
                'cnes': self.prestador.cnes if self.prestador else ''
            },
            
            'procedimento_solicitado': {
                'codigo_tabela': '22',
                'codigo_procedimento': procedimento_principal.codigo,
                'descricao': procedimento_principal.descricao,
                'quantidade': procedimento_principal.quantidade
            },
            
            'dados_alta': {
                'data_alta': data_alta,
                'motivo_alta': motivo_alta  # 11=Curado, 12=Melhorado, 14=A pedido, 15=Óbito, etc.
            } if data_alta else None,
            
            'valor_estimado': procedimento_principal.valor_unitario * procedimento_principal.quantidade
        }
        
        self.guias_geradas.append(guia)
        logger.info(f"Guia de Internação gerada: {guia['numero_guia_prestador']}")
        
        return guia
    
    def validar_guia(self, guia: Dict) -> Dict:
        """
        Valida uma guia TISS conforme regras ANS
        
        Returns:
            Dict com status de validação e erros encontrados
        """
        erros = []
        avisos = []
        
        # Validações básicas
        if not guia.get('dados_beneficiario', {}).get('numero_carteira'):
            erros.append('Número da carteira do beneficiário é obrigatório')
        
        if not guia.get('dados_beneficiario', {}).get('nome'):
            erros.append('Nome do beneficiário é obrigatório')
        
        # Validações específicas por tipo
        tipo = guia.get('tipo')
        
        if tipo == TipoGuia.CONSULTA.value:
            if not guia.get('dados_atendimento', {}).get('data_atendimento'):
                erros.append('Data do atendimento é obrigatória para guia de consulta')
            if not guia.get('dados_atendimento', {}).get('procedimento', {}).get('codigo_procedimento'):
                erros.append('Código do procedimento é obrigatório')
        
        elif tipo == TipoGuia.SADT.value:
            if not guia.get('procedimentos_executados'):
                erros.append('Pelo menos um procedimento é obrigatório para guia SP/SADT')
            if not guia.get('dados_solicitacao', {}).get('indicacao_clinica'):
                avisos.append('Indicação clínica não informada')
        
        elif tipo == TipoGuia.INTERNACAO.value:
            if not guia.get('dados_internacao', {}).get('cid_principal'):
                erros.append('CID principal é obrigatório para internação')
            if not guia.get('dados_internacao', {}).get('data_internacao'):
                erros.append('Data de internação é obrigatória')
        
        return {
            'valido': len(erros) == 0,
            'erros': erros,
            'avisos': avisos,
            'guia_id': guia.get('numero_guia_prestador')
        }
    
    def gerar_lote_guias(self, guias: List[Dict], numero_lote: Optional[str] = None) -> Dict:
        """
        Agrupa guias em um lote para envio à operadora
        
        Args:
            guias: Lista de guias a incluir no lote
            numero_lote: Número do lote (gerado automaticamente se não informado)
        
        Returns:
            Dict com estrutura do lote
        """
        if not numero_lote:
            numero_lote = f"LOTE{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calcular totais
        valor_total = sum(g.get('valor_total', g.get('valor_total_geral', 0)) for g in guias)
        
        lote = {
            'numero_lote': numero_lote,
            'data_geracao': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'versao_tiss': self.VERSAO_TISS,
            'quantidade_guias': len(guias),
            'valor_total_lote': valor_total,
            'prestador': {
                'codigo_na_operadora': self.prestador.codigo_na_operadora if self.prestador else '',
                'cnpj': self.prestador.cnpj if self.prestador else '',
                'cnes': self.prestador.cnes if self.prestador else ''
            },
            'guias': guias
        }
        
        logger.info(f"Lote {numero_lote} gerado com {len(guias)} guias, valor total: R$ {valor_total:.2f}")
        
        return lote
    
    def _gerar_numero_guia(self) -> str:
        """Gera número único da guia do prestador"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"GUIA{timestamp}"
    
    def converter_para_xml_tiss(self, guia: Dict) -> str:
        """
        Converte guia para formato XML TISS (para envio à operadora)
        
        Nota: Implementação simplificada. Produção requer schema XSD completo TISS.
        """
        # TODO: Implementar conversão XML completa conforme schema ANS
        logger.warning("Conversão XML TISS simplificada. Use biblioteca lxml para produção.")
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mensagemTISS xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
    <cabecalho>
        <identificacaoTransacao>
            <tipoTransacao>ENVIO_LOTE_GUIAS</tipoTransacao>
            <sequencialTransacao>{guia.get('numero_guia_prestador', '')}</sequencialTransacao>
            <dataRegistroTransacao>{datetime.now().strftime('%Y-%m-%d')}</dataRegistroTransacao>
            <horaRegistroTransacao>{datetime.now().strftime('%H:%M:%S')}</horaRegistroTransacao>
        </identificacaoTransacao>
        <versaoPadrao>{self.VERSAO_TISS}</versaoPadrao>
    </cabecalho>
    <prestadorParaOperadora>
        <!-- Conteúdo da guia -->
    </prestadorParaOperadora>
</mensagemTISS>"""
        
        return xml
