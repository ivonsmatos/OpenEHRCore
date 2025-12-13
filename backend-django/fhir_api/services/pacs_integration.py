"""
PACS Integration Service - Integração com Picture Archiving and Communication System
Consulta e visualização de imagens médicas via DICOM/WADO-RS
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class Modalidade(Enum):
    """Modalidades de imagem DICOM"""
    CR = 'CR'   # Computed Radiography (Raio-X Digital)
    CT = 'CT'   # Computed Tomography (Tomografia)
    MR = 'MR'   # Magnetic Resonance (Ressonância)
    US = 'US'   # Ultrasound (Ultrassom)
    XA = 'XA'   # X-Ray Angiography
    NM = 'NM'   # Nuclear Medicine
    PT = 'PT'   # PET Scan
    MG = 'MG'   # Mammography
    DX = 'DX'   # Digital Radiography
    RF = 'RF'   # Radio Fluoroscopy
    OT = 'OT'   # Other


@dataclass
class Estudo:
    """Estudo DICOM"""
    study_instance_uid: str
    study_date: str
    study_time: Optional[str]
    study_description: str
    modalities: List[str]
    patient_id: str
    patient_name: str
    accession_number: str
    referring_physician: Optional[str]
    number_of_series: int
    number_of_instances: int


@dataclass
class Serie:
    """Série DICOM"""
    series_instance_uid: str
    series_number: int
    series_description: str
    modality: str
    body_part: Optional[str]
    number_of_instances: int


@dataclass
class Instancia:
    """Instância DICOM (imagem individual)"""
    sop_instance_uid: str
    instance_number: int
    sop_class_uid: str
    rows: Optional[int]
    columns: Optional[int]


class PACSIntegrationService:
    """
    Serviço de integração com PACS via DICOMweb (WADO-RS, STOW-RS, QIDO-RS).
    
    Funcionalidades:
    - Consulta de estudos (QIDO-RS)
    - Recuperação de imagens (WADO-RS)
    - Armazenamento de imagens (STOW-RS)
    - Geração de links para viewer
    - Criação de ImagingStudy FHIR
    """
    
    def __init__(
        self,
        pacs_url: str = "http://localhost:8042",  # Orthanc default
        auth_token: Optional[str] = None,
        viewer_url: Optional[str] = None
    ):
        self.pacs_url = pacs_url.rstrip('/')
        self.auth_token = auth_token
        self.viewer_url = viewer_url or f"{pacs_url}/app/explorer.html"
        
        # Endpoints DICOMweb
        self.qido_url = f"{self.pacs_url}/dicom-web/studies"
        self.wado_url = f"{self.pacs_url}/dicom-web/wado"
        self.stow_url = f"{self.pacs_url}/dicom-web/stow"
    
    def _get_headers(self) -> Dict:
        """Retorna headers para requisições"""
        headers = {
            'Accept': 'application/dicom+json',
            'Content-Type': 'application/dicom+json'
        }
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        return headers
    
    def buscar_estudos(
        self,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        study_date: Optional[str] = None,
        modality: Optional[str] = None,
        accession_number: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Busca estudos no PACS via QIDO-RS.
        
        Args:
            patient_id: ID do paciente
            patient_name: Nome do paciente (suporta wildcards *)
            study_date: Data do estudo (YYYYMMDD ou range YYYYMMDD-YYYYMMDD)
            modality: Modalidade (CT, MR, US, etc.)
            accession_number: Número de acesso
            limit: Limite de resultados
        
        Returns:
            Lista de estudos
        """
        params = {
            'limit': limit,
            'includefield': 'all'
        }
        
        # DICOM tags para busca
        if patient_id:
            params['PatientID'] = patient_id
        if patient_name:
            params['PatientName'] = patient_name
        if study_date:
            params['StudyDate'] = study_date
        if modality:
            params['ModalitiesInStudy'] = modality
        if accession_number:
            params['AccessionNumber'] = accession_number
        
        try:
            response = requests.get(
                self.qido_url,
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                estudos_dicom = response.json()
                return [self._converter_estudo_dicom(e) for e in estudos_dicom]
            else:
                logger.error(f"Erro ao buscar estudos: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com PACS: {str(e)}")
            return []
    
    def _converter_estudo_dicom(self, estudo_dicom: Dict) -> Dict:
        """Converte estudo DICOM JSON para formato simplificado"""
        def get_value(tag_data):
            if isinstance(tag_data, dict):
                value = tag_data.get('Value', [])
                if value and isinstance(value, list):
                    if isinstance(value[0], dict):
                        return value[0].get('Alphabetic', str(value[0]))
                    return str(value[0])
            return ''
        
        return {
            'study_instance_uid': get_value(estudo_dicom.get('0020000D', {})),
            'study_date': get_value(estudo_dicom.get('00080020', {})),
            'study_time': get_value(estudo_dicom.get('00080030', {})),
            'study_description': get_value(estudo_dicom.get('00081030', {})),
            'modalities': estudo_dicom.get('00080061', {}).get('Value', []),
            'patient_id': get_value(estudo_dicom.get('00100020', {})),
            'patient_name': get_value(estudo_dicom.get('00100010', {})),
            'accession_number': get_value(estudo_dicom.get('00080050', {})),
            'referring_physician': get_value(estudo_dicom.get('00080090', {})),
            'number_of_series': int(get_value(estudo_dicom.get('00201206', {})) or 0),
            'number_of_instances': int(get_value(estudo_dicom.get('00201208', {})) or 0)
        }
    
    def obter_series(self, study_instance_uid: str) -> List[Dict]:
        """
        Obtém séries de um estudo.
        
        Args:
            study_instance_uid: UID do estudo
        
        Returns:
            Lista de séries
        """
        url = f"{self.qido_url}/{study_instance_uid}/series"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                series_dicom = response.json()
                return [self._converter_serie_dicom(s) for s in series_dicom]
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter séries: {str(e)}")
            return []
    
    def _converter_serie_dicom(self, serie_dicom: Dict) -> Dict:
        """Converte série DICOM para formato simplificado"""
        def get_value(tag_data):
            if isinstance(tag_data, dict):
                value = tag_data.get('Value', [])
                if value:
                    return str(value[0]) if value else ''
            return ''
        
        return {
            'series_instance_uid': get_value(serie_dicom.get('0020000E', {})),
            'series_number': int(get_value(serie_dicom.get('00200011', {})) or 0),
            'series_description': get_value(serie_dicom.get('0008103E', {})),
            'modality': get_value(serie_dicom.get('00080060', {})),
            'body_part': get_value(serie_dicom.get('00180015', {})),
            'number_of_instances': int(get_value(serie_dicom.get('00201209', {})) or 0)
        }
    
    def obter_url_imagem(
        self,
        study_instance_uid: str,
        series_instance_uid: Optional[str] = None,
        sop_instance_uid: Optional[str] = None,
        frame: int = 1,
        format: str = 'image/jpeg'
    ) -> str:
        """
        Gera URL WADO-RS para visualização de imagem.
        
        Args:
            study_instance_uid: UID do estudo
            series_instance_uid: UID da série (opcional)
            sop_instance_uid: UID da instância (opcional)
            frame: Número do frame
            format: Formato da imagem (image/jpeg, image/png)
        
        Returns:
            URL para recuperação da imagem
        """
        url = f"{self.pacs_url}/dicom-web/studies/{study_instance_uid}"
        
        if series_instance_uid:
            url += f"/series/{series_instance_uid}"
            if sop_instance_uid:
                url += f"/instances/{sop_instance_uid}"
        
        url += f"/rendered?viewport=512,512&frame={frame}"
        
        return url
    
    def obter_url_viewer(self, study_instance_uid: str) -> str:
        """
        Gera URL para abrir estudo no viewer DICOM.
        
        Args:
            study_instance_uid: UID do estudo
        
        Returns:
            URL do viewer
        """
        # Formato para OHIF Viewer
        return f"{self.viewer_url}?StudyInstanceUIDs={study_instance_uid}"
    
    def criar_imaging_study_fhir(
        self,
        estudo: Dict,
        patient_fhir_id: str,
        endpoint_fhir_id: Optional[str] = None
    ) -> Dict:
        """
        Cria recurso ImagingStudy FHIR a partir de estudo DICOM.
        
        Args:
            estudo: Dados do estudo (retorno de buscar_estudos)
            patient_fhir_id: ID FHIR do paciente
            endpoint_fhir_id: ID do Endpoint FHIR do PACS
        
        Returns:
            Recurso ImagingStudy FHIR
        """
        # Converter data DICOM para ISO
        study_date = estudo.get('study_date', '')
        if len(study_date) == 8:
            study_date = f"{study_date[:4]}-{study_date[4:6]}-{study_date[6:8]}"
        
        imaging_study = {
            'resourceType': 'ImagingStudy',
            'identifier': [{
                'system': 'urn:dicom:uid',
                'value': f"urn:oid:{estudo.get('study_instance_uid')}"
            }],
            'status': 'available',
            'subject': {
                'reference': f"Patient/{patient_fhir_id}"
            },
            'started': study_date,
            'numberOfSeries': estudo.get('number_of_series', 0),
            'numberOfInstances': estudo.get('number_of_instances', 0),
            'description': estudo.get('study_description'),
            'modality': [
                {'system': 'http://dicom.nema.org/resources/ontology/DCM', 'code': m}
                for m in estudo.get('modalities', [])
            ]
        }
        
        # Adicionar referência ao Endpoint PACS
        if endpoint_fhir_id:
            imaging_study['endpoint'] = [{'reference': f"Endpoint/{endpoint_fhir_id}"}]
        
        # Adicionar referencing physician
        if estudo.get('referring_physician'):
            imaging_study['referrer'] = {'display': estudo['referring_physician']}
        
        # Adicionar link para viewer
        imaging_study['extension'] = [{
            'url': 'http://hl7.org/fhir/StructureDefinition/artifact-url',
            'valueUrl': self.obter_url_viewer(estudo.get('study_instance_uid', ''))
        }]
        
        return imaging_study
    
    def verificar_conexao(self) -> Dict:
        """
        Verifica conexão com o PACS.
        
        Returns:
            Dict com status da conexão
        """
        try:
            # Tentar busca vazia para verificar conectividade
            response = requests.get(
                self.qido_url,
                params={'limit': 1},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code in (200, 204):
                return {
                    'status': 'connected',
                    'pacs_url': self.pacs_url,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'pacs_url': self.pacs_url,
                    'error': f'HTTP {response.status_code}',
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'disconnected',
                'pacs_url': self.pacs_url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def buscar_estudos_paciente(self, patient_id: str) -> List[Dict]:
        """
        Busca todos os estudos de um paciente.
        
        Args:
            patient_id: ID do paciente
        
        Returns:
            Lista de estudos do paciente
        """
        return self.buscar_estudos(patient_id=patient_id)
    
    def obter_thumbnail(
        self,
        study_instance_uid: str,
        series_instance_uid: str,
        width: int = 128,
        height: int = 128
    ) -> str:
        """
        Gera URL para thumbnail de uma série.
        
        Args:
            study_instance_uid: UID do estudo
            series_instance_uid: UID da série
            width: Largura do thumbnail
            height: Altura do thumbnail
        
        Returns:
            URL do thumbnail
        """
        return (
            f"{self.pacs_url}/dicom-web/studies/{study_instance_uid}"
            f"/series/{series_instance_uid}/thumbnail"
            f"?viewport={width},{height}"
        )
