"""
CBO Service - Classificação Brasileira de Ocupações
Terminologia oficial do Ministério do Trabalho para profissionais de saúde
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class GrupoCBO(Enum):
    """Grandes grupos CBO relacionados à saúde"""
    PROFISSIONAIS_CIENCIAS_SAUDE = '2'      # Profissionais das ciências e das artes
    TECNICOS_NIVEL_MEDIO_SAUDE = '3'        # Técnicos de nível médio
    TRABALHADORES_SERVICOS_SAUDE = '5'      # Trabalhadores dos serviços


# Tabela completa de CBOs de saúde (principais)
CBO_SAUDE = {
    # Médicos
    '2251-01': {'nome': 'Médico', 'familia': '2251', 'descricao': 'Médico clínico'},
    '2251-02': {'nome': 'Médico acupunturista', 'familia': '2251', 'descricao': 'Médico acupunturista'},
    '2251-03': {'nome': 'Médico alergista', 'familia': '2251', 'descricao': 'Médico alergista e imunologista'},
    '2251-04': {'nome': 'Médico anestesiologista', 'familia': '2251', 'descricao': 'Médico anestesiologista'},
    '2251-05': {'nome': 'Médico angiologista', 'familia': '2251', 'descricao': 'Médico angiologista'},
    '2251-06': {'nome': 'Médico cardiologista', 'familia': '2251', 'descricao': 'Médico cardiologista'},
    '2251-07': {'nome': 'Médico clínico geral', 'familia': '2251', 'descricao': 'Médico clínico geral'},
    '2251-08': {'nome': 'Médico dermatologista', 'familia': '2251', 'descricao': 'Médico dermatologista'},
    '2251-09': {'nome': 'Médico endocrinologista', 'familia': '2251', 'descricao': 'Médico endocrinologista e metabologista'},
    '2251-10': {'nome': 'Médico fisiatra', 'familia': '2251', 'descricao': 'Médico fisiatra'},
    '2251-11': {'nome': 'Médico gastroenterologista', 'familia': '2251', 'descricao': 'Médico gastroenterologista'},
    '2251-12': {'nome': 'Médico generalista', 'familia': '2251', 'descricao': 'Médico generalista'},
    '2251-13': {'nome': 'Médico geneticista', 'familia': '2251', 'descricao': 'Médico geneticista'},
    '2251-14': {'nome': 'Médico geriatra', 'familia': '2251', 'descricao': 'Médico geriatra'},
    '2251-15': {'nome': 'Médico ginecologista', 'familia': '2251', 'descricao': 'Médico ginecologista e obstetra'},
    '2251-16': {'nome': 'Médico hematologista', 'familia': '2251', 'descricao': 'Médico hematologista'},
    '2251-17': {'nome': 'Médico homeopata', 'familia': '2251', 'descricao': 'Médico homeopata'},
    '2251-18': {'nome': 'Médico infectologista', 'familia': '2251', 'descricao': 'Médico infectologista'},
    '2251-19': {'nome': 'Médico mastologista', 'familia': '2251', 'descricao': 'Médico mastologista'},
    '2251-20': {'nome': 'Médico nefrologista', 'familia': '2251', 'descricao': 'Médico nefrologista'},
    '2251-21': {'nome': 'Médico neurologista', 'familia': '2251', 'descricao': 'Médico neurologista'},
    '2251-22': {'nome': 'Médico nutrologista', 'familia': '2251', 'descricao': 'Médico nutrologista'},
    '2251-23': {'nome': 'Médico oftalmologista', 'familia': '2251', 'descricao': 'Médico oftalmologista'},
    '2251-24': {'nome': 'Médico oncologista', 'familia': '2251', 'descricao': 'Médico oncologista clínico'},
    '2251-25': {'nome': 'Médico ortopedista', 'familia': '2251', 'descricao': 'Médico ortopedista e traumatologista'},
    '2251-26': {'nome': 'Médico otorrinolaringologista', 'familia': '2251', 'descricao': 'Médico otorrinolaringologista'},
    '2251-27': {'nome': 'Médico patologista', 'familia': '2251', 'descricao': 'Médico patologista'},
    '2251-28': {'nome': 'Médico pediatra', 'familia': '2251', 'descricao': 'Médico pediatra'},
    '2251-29': {'nome': 'Médico pneumologista', 'familia': '2251', 'descricao': 'Médico pneumologista'},
    '2251-30': {'nome': 'Médico proctologista', 'familia': '2251', 'descricao': 'Médico proctologista'},
    '2251-31': {'nome': 'Médico psiquiatra', 'familia': '2251', 'descricao': 'Médico psiquiatra'},
    '2251-32': {'nome': 'Médico radiologista', 'familia': '2251', 'descricao': 'Médico radiologista'},
    '2251-33': {'nome': 'Médico reumatologista', 'familia': '2251', 'descricao': 'Médico reumatologista'},
    '2251-34': {'nome': 'Médico urologista', 'familia': '2251', 'descricao': 'Médico urologista'},
    '2251-35': {'nome': 'Médico sanitarista', 'familia': '2251', 'descricao': 'Médico sanitarista'},
    '2251-36': {'nome': 'Médico do trabalho', 'familia': '2251', 'descricao': 'Médico do trabalho'},
    '2251-37': {'nome': 'Médico em medicina intensiva', 'familia': '2251', 'descricao': 'Médico intensivista'},
    '2251-38': {'nome': 'Médico legista', 'familia': '2251', 'descricao': 'Médico legista'},
    '2251-39': {'nome': 'Médico neonatologista', 'familia': '2251', 'descricao': 'Médico neonatologista'},
    '2251-40': {'nome': 'Médico neurocirurgião', 'familia': '2251', 'descricao': 'Médico neurocirurgião'},
    '2251-41': {'nome': 'Médico cirurgião geral', 'familia': '2251', 'descricao': 'Médico cirurgião geral'},
    '2251-42': {'nome': 'Médico cirurgião cardiovascular', 'familia': '2251', 'descricao': 'Médico cirurgião cardiovascular'},
    '2251-43': {'nome': 'Médico cirurgião plástico', 'familia': '2251', 'descricao': 'Médico cirurgião plástico'},
    '2251-44': {'nome': 'Médico emergencista', 'familia': '2251', 'descricao': 'Médico emergencista'},
    '2251-45': {'nome': 'Médico de família', 'familia': '2251', 'descricao': 'Médico de família e comunidade'},
    
    # Cirurgiões-Dentistas
    '2232-01': {'nome': 'Cirurgião-dentista - clínico geral', 'familia': '2232', 'descricao': 'Cirurgião-dentista clínico geral'},
    '2232-02': {'nome': 'Cirurgião-dentista - endodontista', 'familia': '2232', 'descricao': 'Especialista em endodontia'},
    '2232-03': {'nome': 'Cirurgião-dentista - epidemiologista', 'familia': '2232', 'descricao': 'Especialista em epidemiologia bucal'},
    '2232-04': {'nome': 'Cirurgião-dentista - estomatologista', 'familia': '2232', 'descricao': 'Especialista em estomatologia'},
    '2232-05': {'nome': 'Cirurgião-dentista - implantodontista', 'familia': '2232', 'descricao': 'Especialista em implantodontia'},
    '2232-06': {'nome': 'Cirurgião-dentista - odontogeriatra', 'familia': '2232', 'descricao': 'Especialista em odontogeriatria'},
    '2232-07': {'nome': 'Cirurgião-dentista - odontologista legal', 'familia': '2232', 'descricao': 'Especialista em odontologia legal'},
    '2232-08': {'nome': 'Cirurgião-dentista - odontopediatra', 'familia': '2232', 'descricao': 'Especialista em odontopediatria'},
    '2232-09': {'nome': 'Cirurgião-dentista - ortodontista', 'familia': '2232', 'descricao': 'Especialista em ortodontia'},
    '2232-10': {'nome': 'Cirurgião-dentista - patologista bucal', 'familia': '2232', 'descricao': 'Especialista em patologia bucal'},
    '2232-11': {'nome': 'Cirurgião-dentista - periodontista', 'familia': '2232', 'descricao': 'Especialista em periodontia'},
    '2232-12': {'nome': 'Cirurgião-dentista - protesiólogo', 'familia': '2232', 'descricao': 'Especialista em prótese dentária'},
    '2232-13': {'nome': 'Cirurgião-dentista - radiologista', 'familia': '2232', 'descricao': 'Especialista em radiologia odontológica'},
    '2232-14': {'nome': 'Cirurgião-dentista - traumatologista', 'familia': '2232', 'descricao': 'Especialista em cirurgia buco-maxilo-facial'},
    '2232-15': {'nome': 'Cirurgião-dentista - saúde coletiva', 'familia': '2232', 'descricao': 'Especialista em saúde coletiva'},
    
    # Enfermeiros
    '2235-01': {'nome': 'Enfermeiro', 'familia': '2235', 'descricao': 'Enfermeiro'},
    '2235-02': {'nome': 'Enfermeiro auditor', 'familia': '2235', 'descricao': 'Enfermeiro auditor'},
    '2235-03': {'nome': 'Enfermeiro de bordo', 'familia': '2235', 'descricao': 'Enfermeiro de bordo'},
    '2235-04': {'nome': 'Enfermeiro de centro cirúrgico', 'familia': '2235', 'descricao': 'Enfermeiro de centro cirúrgico'},
    '2235-05': {'nome': 'Enfermeiro de terapia intensiva', 'familia': '2235', 'descricao': 'Enfermeiro de UTI'},
    '2235-06': {'nome': 'Enfermeiro do trabalho', 'familia': '2235', 'descricao': 'Enfermeiro do trabalho'},
    '2235-07': {'nome': 'Enfermeiro nefrologista', 'familia': '2235', 'descricao': 'Enfermeiro nefrologista'},
    '2235-08': {'nome': 'Enfermeiro neonatologista', 'familia': '2235', 'descricao': 'Enfermeiro neonatologista'},
    '2235-09': {'nome': 'Enfermeiro obstétrico', 'familia': '2235', 'descricao': 'Enfermeiro obstetra'},
    '2235-10': {'nome': 'Enfermeiro psiquiátrico', 'familia': '2235', 'descricao': 'Enfermeiro psiquiátrico'},
    '2235-11': {'nome': 'Enfermeiro puericultor', 'familia': '2235', 'descricao': 'Enfermeiro puericultor e pediatrico'},
    '2235-12': {'nome': 'Enfermeiro sanitarista', 'familia': '2235', 'descricao': 'Enfermeiro sanitarista'},
    '2235-13': {'nome': 'Enfermeiro da ESF', 'familia': '2235', 'descricao': 'Enfermeiro da Estratégia Saúde da Família'},
    
    # Farmacêuticos
    '2234-01': {'nome': 'Farmacêutico', 'familia': '2234', 'descricao': 'Farmacêutico'},
    '2234-02': {'nome': 'Farmacêutico analista clínico', 'familia': '2234', 'descricao': 'Farmacêutico analista clínico'},
    '2234-03': {'nome': 'Farmacêutico de alimentos', 'familia': '2234', 'descricao': 'Farmacêutico bromatologista'},
    '2234-04': {'nome': 'Farmacêutico hospitalar', 'familia': '2234', 'descricao': 'Farmacêutico hospitalar e clínico'},
    '2234-05': {'nome': 'Farmacêutico industrial', 'familia': '2234', 'descricao': 'Farmacêutico industrial'},
    '2234-06': {'nome': 'Farmacêutico toxicologista', 'familia': '2234', 'descricao': 'Farmacêutico toxicologista'},
    
    # Fisioterapeutas e Terapeutas Ocupacionais
    '2236-01': {'nome': 'Fisioterapeuta geral', 'familia': '2236', 'descricao': 'Fisioterapeuta geral'},
    '2236-02': {'nome': 'Fisioterapeuta acupunturista', 'familia': '2236', 'descricao': 'Fisioterapeuta acupunturista'},
    '2236-03': {'nome': 'Fisioterapeuta aquático', 'familia': '2236', 'descricao': 'Fisioterapeuta aquático'},
    '2236-04': {'nome': 'Fisioterapeuta dermato-funcional', 'familia': '2236', 'descricao': 'Fisioterapeuta dermato-funcional'},
    '2236-05': {'nome': 'Fisioterapeuta esportivo', 'familia': '2236', 'descricao': 'Fisioterapeuta esportivo'},
    '2236-06': {'nome': 'Fisioterapeuta neurofuncional', 'familia': '2236', 'descricao': 'Fisioterapeuta neurofuncional'},
    '2236-07': {'nome': 'Fisioterapeuta respiratório', 'familia': '2236', 'descricao': 'Fisioterapeuta respiratório'},
    '2236-08': {'nome': 'Fisioterapeuta do trabalho', 'familia': '2236', 'descricao': 'Fisioterapeuta do trabalho'},
    '2236-09': {'nome': 'Fisioterapeuta traumato-ortopédico', 'familia': '2236', 'descricao': 'Fisioterapeuta traumato-ortopédico'},
    '2239-01': {'nome': 'Terapeuta ocupacional', 'familia': '2239', 'descricao': 'Terapeuta ocupacional'},
    
    # Nutricionistas
    '2237-01': {'nome': 'Nutricionista', 'familia': '2237', 'descricao': 'Nutricionista'},
    '2237-02': {'nome': 'Nutricionista clínico', 'familia': '2237', 'descricao': 'Nutricionista clínico'},
    '2237-03': {'nome': 'Nutricionista esportivo', 'familia': '2237', 'descricao': 'Nutricionista esportivo'},
    
    # Fonoaudiólogos
    '2238-01': {'nome': 'Fonoaudiólogo geral', 'familia': '2238', 'descricao': 'Fonoaudiólogo geral'},
    '2238-02': {'nome': 'Fonoaudiólogo audiologista', 'familia': '2238', 'descricao': 'Fonoaudiólogo audiologista'},
    '2238-03': {'nome': 'Fonoaudiólogo hospitalar', 'familia': '2238', 'descricao': 'Fonoaudiólogo hospitalar'},
    
    # Psicólogos
    '2515-01': {'nome': 'Psicólogo clínico', 'familia': '2515', 'descricao': 'Psicólogo clínico'},
    '2515-02': {'nome': 'Psicólogo educacional', 'familia': '2515', 'descricao': 'Psicólogo educacional'},
    '2515-03': {'nome': 'Psicólogo hospitalar', 'familia': '2515', 'descricao': 'Psicólogo hospitalar'},
    '2515-04': {'nome': 'Psicólogo jurídico', 'familia': '2515', 'descricao': 'Psicólogo jurídico'},
    '2515-05': {'nome': 'Psicólogo organizacional', 'familia': '2515', 'descricao': 'Psicólogo organizacional e do trabalho'},
    '2515-06': {'nome': 'Psicólogo do trânsito', 'familia': '2515', 'descricao': 'Psicólogo do trânsito'},
    '2515-07': {'nome': 'Psicólogo neuropsicólogo', 'familia': '2515', 'descricao': 'Neuropsicólogo'},
    '2515-08': {'nome': 'Psicólogo social', 'familia': '2515', 'descricao': 'Psicólogo social'},
    
    # Biomédicos
    '2212-01': {'nome': 'Biomédico', 'familia': '2212', 'descricao': 'Biomédico'},
    
    # Assistentes Sociais
    '2516-01': {'nome': 'Assistente social', 'familia': '2516', 'descricao': 'Assistente social'},
    
    # Técnicos de Enfermagem
    '3222-01': {'nome': 'Técnico de enfermagem', 'familia': '3222', 'descricao': 'Técnico de enfermagem'},
    '3222-02': {'nome': 'Técnico de enfermagem de UTI', 'familia': '3222', 'descricao': 'Técnico de enfermagem de terapia intensiva'},
    '3222-03': {'nome': 'Técnico de enfermagem do trabalho', 'familia': '3222', 'descricao': 'Técnico de enfermagem do trabalho'},
    '3222-04': {'nome': 'Técnico de enfermagem psiquiátrica', 'familia': '3222', 'descricao': 'Técnico de enfermagem psiquiátrica'},
    '3222-05': {'nome': 'Instrumentador cirúrgico', 'familia': '3222', 'descricao': 'Instrumentador cirúrgico'},
    
    # Auxiliar de Enfermagem
    '3222-10': {'nome': 'Auxiliar de enfermagem', 'familia': '3222', 'descricao': 'Auxiliar de enfermagem'},
    '3222-11': {'nome': 'Auxiliar de enfermagem do trabalho', 'familia': '3222', 'descricao': 'Auxiliar de enfermagem do trabalho'},
    
    # Técnicos em Radiologia
    '3241-01': {'nome': 'Tecnólogo em radiologia', 'familia': '3241', 'descricao': 'Tecnólogo em radiologia'},
    '3241-02': {'nome': 'Técnico em radiologia', 'familia': '3241', 'descricao': 'Técnico em radiologia e imagenologia'},
    '3241-03': {'nome': 'Técnico em radioterapia', 'familia': '3241', 'descricao': 'Técnico em radioterapia'},
    '3241-04': {'nome': 'Técnico em medicina nuclear', 'familia': '3241', 'descricao': 'Técnico em medicina nuclear'},
    
    # Técnicos de Laboratório
    '3242-01': {'nome': 'Técnico em patologia clínica', 'familia': '3242', 'descricao': 'Técnico em análises clínicas'},
    '3242-02': {'nome': 'Técnico em hemoterapia', 'familia': '3242', 'descricao': 'Técnico em hemoterapia'},
    '3242-03': {'nome': 'Técnico em histologia', 'familia': '3242', 'descricao': 'Técnico em histologia'},
    
    # Agentes Comunitários
    '5151-01': {'nome': 'Agente comunitário de saúde', 'familia': '5151', 'descricao': 'Agente comunitário de saúde - ACS'},
    '5151-02': {'nome': 'Agente de combate às endemias', 'familia': '5151', 'descricao': 'Agente de combate às endemias - ACE'},
    
    # Recepcionistas de Saúde
    '4221-01': {'nome': 'Recepcionista de consultório', 'familia': '4221', 'descricao': 'Recepcionista de consultório médico ou odontológico'},
}

# Famílias CBO
FAMILIAS_CBO = {
    '2212': 'Biólogos e afins',
    '2232': 'Cirurgiões-dentistas',
    '2234': 'Farmacêuticos',
    '2235': 'Enfermeiros e afins',
    '2236': 'Fisioterapeutas',
    '2237': 'Nutricionistas',
    '2238': 'Fonoaudiólogos',
    '2239': 'Terapeutas ocupacionais e ortoptistas',
    '2251': 'Médicos',
    '2515': 'Psicólogos e psicanalistas',
    '2516': 'Assistentes sociais e economistas domésticos',
    '3222': 'Técnicos e auxiliares de enfermagem',
    '3241': 'Tecnólogos e técnicos em terapias',
    '3242': 'Técnicos em ciências da saúde',
    '4221': 'Recepcionistas',
    '5151': 'Agentes comunitários de saúde e afins',
}


@dataclass
class OcupacaoCBO:
    """Representação de uma ocupação CBO"""
    codigo: str
    nome: str
    familia: str
    familia_nome: str
    descricao: str


class CBOService:
    """
    Serviço de consulta CBO - Classificação Brasileira de Ocupações
    
    Integração com:
    - Practitioner.qualification.code
    - PractitionerRole.code
    - CNES
    - TISS/ANS
    """
    
    # Sistema FHIR para CBO
    SYSTEM_CBO = 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRCBO'
    
    def __init__(self):
        self.ocupacoes = CBO_SAUDE
        self.familias = FAMILIAS_CBO
    
    def buscar_por_codigo(self, codigo: str) -> Optional[OcupacaoCBO]:
        """
        Busca ocupação por código CBO.
        
        Args:
            codigo: Código CBO (ex: '2251-25')
        
        Returns:
            OcupacaoCBO ou None
        """
        # Normalizar código
        codigo = codigo.replace('.', '-').strip()
        
        if codigo in self.ocupacoes:
            ocp = self.ocupacoes[codigo]
            return OcupacaoCBO(
                codigo=codigo,
                nome=ocp['nome'],
                familia=ocp['familia'],
                familia_nome=self.familias.get(ocp['familia'], ''),
                descricao=ocp['descricao']
            )
        return None
    
    def buscar_por_nome(self, termo: str, limite: int = 20) -> List[OcupacaoCBO]:
        """
        Busca ocupações por nome/descrição.
        
        Args:
            termo: Termo de busca
            limite: Máximo de resultados
        
        Returns:
            Lista de ocupações
        """
        termo_lower = termo.lower()
        resultados = []
        
        for codigo, dados in self.ocupacoes.items():
            if (termo_lower in dados['nome'].lower() or 
                termo_lower in dados['descricao'].lower()):
                resultados.append(OcupacaoCBO(
                    codigo=codigo,
                    nome=dados['nome'],
                    familia=dados['familia'],
                    familia_nome=self.familias.get(dados['familia'], ''),
                    descricao=dados['descricao']
                ))
                if len(resultados) >= limite:
                    break
        
        return resultados
    
    def listar_por_familia(self, familia: str) -> List[OcupacaoCBO]:
        """
        Lista ocupações de uma família CBO.
        
        Args:
            familia: Código da família (ex: '2251' para médicos)
        
        Returns:
            Lista de ocupações
        """
        resultados = []
        
        for codigo, dados in self.ocupacoes.items():
            if dados['familia'] == familia:
                resultados.append(OcupacaoCBO(
                    codigo=codigo,
                    nome=dados['nome'],
                    familia=dados['familia'],
                    familia_nome=self.familias.get(dados['familia'], ''),
                    descricao=dados['descricao']
                ))
        
        return resultados
    
    def listar_familias(self) -> Dict[str, str]:
        """Lista todas as famílias CBO de saúde"""
        return self.familias
    
    def validar_codigo(self, codigo: str) -> bool:
        """
        Valida se um código CBO existe.
        
        Args:
            codigo: Código a validar
        
        Returns:
            True se válido
        """
        codigo = codigo.replace('.', '-').strip()
        return codigo in self.ocupacoes
    
    def gerar_coding_fhir(self, codigo: str) -> Optional[Dict]:
        """
        Gera Coding FHIR para um código CBO.
        
        Args:
            codigo: Código CBO
        
        Returns:
            Dict no formato FHIR Coding
        """
        ocp = self.buscar_por_codigo(codigo)
        if not ocp:
            return None
        
        return {
            'system': self.SYSTEM_CBO,
            'code': codigo,
            'display': ocp.nome
        }
    
    def gerar_codeable_concept_fhir(self, codigo: str) -> Optional[Dict]:
        """
        Gera CodeableConcept FHIR para um código CBO.
        
        Args:
            codigo: Código CBO
        
        Returns:
            Dict no formato FHIR CodeableConcept
        """
        coding = self.gerar_coding_fhir(codigo)
        if not coding:
            return None
        
        ocp = self.buscar_por_codigo(codigo)
        return {
            'coding': [coding],
            'text': ocp.descricao if ocp else ''
        }
    
    def gerar_practitioner_qualification(
        self,
        codigo_cbo: str,
        numero_conselho: str,
        conselho: str,  # CRM, COREN, CRO, etc.
        uf: str
    ) -> Dict:
        """
        Gera qualification para Practitioner FHIR.
        
        Args:
            codigo_cbo: Código CBO
            numero_conselho: Número do registro profissional
            conselho: Sigla do conselho (CRM, COREN, CRO)
            uf: UF do registro
        
        Returns:
            Dict no formato FHIR Practitioner.qualification
        """
        ocp = self.buscar_por_codigo(codigo_cbo)
        
        return {
            'identifier': [{
                'use': 'official',
                'system': f'http://www.saude.gov.br/fhir/r4/NamingSystem/BR{conselho}',
                'value': f'{numero_conselho}/{uf}'
            }],
            'code': {
                'coding': [
                    self.gerar_coding_fhir(codigo_cbo),
                    {
                        'system': f'http://www.{conselho.lower()}.org.br',
                        'code': numero_conselho,
                        'display': f'{conselho} {numero_conselho}/{uf}'
                    }
                ],
                'text': ocp.descricao if ocp else ''
            },
            'issuer': {
                'display': f'Conselho {conselho} - {uf}'
            }
        }


# Instância singleton
cbo_service = CBOService()
