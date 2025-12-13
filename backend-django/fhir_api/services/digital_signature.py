"""
Digital Signature Service - Assinatura Digital ICP-Brasil
Assinatura de documentos clínicos com certificado digital
"""

import logging
import hashlib
import base64
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TipoCertificado(Enum):
    """Tipos de certificados ICP-Brasil"""
    A1 = 'A1'  # Armazenado em arquivo (validade 1 ano)
    A3 = 'A3'  # Armazenado em token/smartcard (validade 3 anos)


class TipoAssinatura(Enum):
    """Tipos de assinatura digital"""
    CADES = 'CAdES'  # Para documentos em geral
    PADES = 'PAdES'  # Para PDFs
    XADES = 'XAdES'  # Para XMLs


@dataclass
class CertificadoInfo:
    """Informações do certificado digital"""
    nome_titular: str
    cpf: str
    data_validade: str
    tipo: TipoCertificado
    emissor: str
    numero_serie: str
    valido: bool
    dias_para_expirar: int


class DigitalSignatureService:
    """
    Serviço de assinatura digital usando certificados ICP-Brasil.
    
    Nota: Esta é uma implementação de interface. Em produção, integrar com:
    - Biblioteca cryptography para operações criptográficas
    - OpenSSL ou python-pkcs11 para certificados A3
    - pyhanko para assinatura de PDFs
    - signxml para assinatura de XMLs
    """
    
    def __init__(self, certificado_path: Optional[str] = None, certificado_senha: Optional[str] = None):
        self.certificado_path = certificado_path
        self.certificado_senha = certificado_senha
        self._certificado = None
        self._chave_privada = None
    
    def carregar_certificado(self, path: str, senha: str) -> CertificadoInfo:
        """
        Carrega certificado digital A1 (.pfx/.p12)
        
        Args:
            path: Caminho do arquivo de certificado
            senha: Senha do certificado
        
        Returns:
            Informações do certificado
        """
        try:
            # Em produção, usar:
            # from cryptography.hazmat.primitives.serialization import pkcs12
            # with open(path, 'rb') as f:
            #     private_key, certificate, chain = pkcs12.load_key_and_certificates(f.read(), senha.encode())
            
            # Simulação para desenvolvimento
            logger.info(f"Carregando certificado: {path}")
            
            # Extrair informações do certificado
            info = CertificadoInfo(
                nome_titular="Dr. João Silva",
                cpf="123.456.789-00",
                data_validade="2025-12-31",
                tipo=TipoCertificado.A1,
                emissor="AC VÁLIDA RFB v5",
                numero_serie="1234567890",
                valido=True,
                dias_para_expirar=365
            )
            
            self._certificado = True  # Placeholder
            return info
            
        except Exception as e:
            logger.error(f"Erro ao carregar certificado: {str(e)}")
            raise
    
    def assinar_documento(
        self,
        conteudo: bytes,
        tipo_assinatura: TipoAssinatura = TipoAssinatura.CADES,
        incluir_carimbo_tempo: bool = True
    ) -> Dict:
        """
        Assina documento digitalmente.
        
        Args:
            conteudo: Bytes do documento a assinar
            tipo_assinatura: Tipo de assinatura (CAdES, PAdES, XAdES)
            incluir_carimbo_tempo: Se deve incluir carimbo de tempo
        
        Returns:
            Dict com assinatura e metadados
        """
        if not self._certificado:
            raise ValueError("Certificado não carregado. Use carregar_certificado() primeiro.")
        
        try:
            # Calcular hash do documento
            hash_documento = hashlib.sha256(conteudo).hexdigest()
            
            # Em produção, usar biblioteca de assinatura real
            # Para CAdES: from asn1crypto import cms
            # Para PAdES: from pyhanko.sign import signers
            # Para XAdES: from signxml import XMLSigner
            
            # Simulação de assinatura
            timestamp = datetime.now().isoformat()
            
            assinatura = {
                'tipo': tipo_assinatura.value,
                'algoritmo': 'SHA256withRSA',
                'hash_documento': hash_documento,
                'data_assinatura': timestamp,
                'assinatura_base64': base64.b64encode(
                    f"ASSINATURA_SIMULADA_{hash_documento}_{timestamp}".encode()
                ).decode(),
                'certificado': {
                    'numero_serie': '1234567890',
                    'emissor': 'AC VÁLIDA RFB v5'
                }
            }
            
            if incluir_carimbo_tempo:
                assinatura['carimbo_tempo'] = {
                    'data': timestamp,
                    'servidor': 'TSA ICP-Brasil',
                    'hash': hashlib.sha256(timestamp.encode()).hexdigest()
                }
            
            logger.info(f"Documento assinado com sucesso - Hash: {hash_documento[:16]}...")
            
            return assinatura
            
        except Exception as e:
            logger.error(f"Erro ao assinar documento: {str(e)}")
            raise
    
    def assinar_pdf(
        self,
        pdf_bytes: bytes,
        razao: str = "Assinatura Digital",
        localizacao: str = "Brasil",
        contato: Optional[str] = None
    ) -> bytes:
        """
        Assina documento PDF com assinatura visível.
        
        Args:
            pdf_bytes: Bytes do PDF original
            razao: Motivo da assinatura
            localizacao: Local da assinatura
            contato: Informações de contato
        
        Returns:
            Bytes do PDF assinado
        """
        if not self._certificado:
            raise ValueError("Certificado não carregado.")
        
        try:
            # Em produção, usar pyhanko:
            # from pyhanko.sign import signers, fields
            # from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
            
            # Simulação - retorna o PDF original com metadados de assinatura
            # Em produção, adicionar assinatura real ao PDF
            
            logger.info(f"PDF assinado - Razão: {razao}, Local: {localizacao}")
            
            # Retornar PDF original (em produção, retornar PDF assinado)
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Erro ao assinar PDF: {str(e)}")
            raise
    
    def assinar_xml(
        self,
        xml_content: str,
        elemento_a_assinar: Optional[str] = None
    ) -> str:
        """
        Assina documento XML.
        
        Args:
            xml_content: Conteúdo XML a assinar
            elemento_a_assinar: ID do elemento específico (opcional)
        
        Returns:
            XML assinado
        """
        if not self._certificado:
            raise ValueError("Certificado não carregado.")
        
        try:
            # Em produção, usar signxml:
            # from signxml import XMLSigner
            # signer = XMLSigner()
            # signed = signer.sign(root, key=key, cert=cert)
            
            # Simulação - adicionar bloco de assinatura
            signature_block = f"""
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
    <SignedInfo>
        <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
        <SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
    </SignedInfo>
    <SignatureValue>ASSINATURA_SIMULADA_BASE64</SignatureValue>
    <KeyInfo>
        <X509Data>
            <X509Certificate>CERTIFICADO_BASE64</X509Certificate>
        </X509Data>
    </KeyInfo>
</Signature>"""
            
            # Inserir assinatura antes do fechamento do elemento raiz
            if '</mensagemTISS>' in xml_content:
                xml_assinado = xml_content.replace('</mensagemTISS>', f'{signature_block}</mensagemTISS>')
            else:
                xml_assinado = xml_content + signature_block
            
            logger.info("XML assinado com sucesso")
            
            return xml_assinado
            
        except Exception as e:
            logger.error(f"Erro ao assinar XML: {str(e)}")
            raise
    
    def verificar_assinatura(
        self,
        documento: bytes,
        assinatura: Dict
    ) -> Dict:
        """
        Verifica validade de uma assinatura digital.
        
        Args:
            documento: Bytes do documento original
            assinatura: Dict com dados da assinatura
        
        Returns:
            Dict com resultado da verificação
        """
        try:
            # Recalcular hash
            hash_atual = hashlib.sha256(documento).hexdigest()
            hash_original = assinatura.get('hash_documento', '')
            
            # Verificar integridade
            integridade = hash_atual == hash_original
            
            # Em produção, verificar:
            # 1. Validade do certificado
            # 2. Cadeia de certificação (ICP-Brasil)
            # 3. Lista de certificados revogados (LCR)
            # 4. Carimbo de tempo
            
            resultado = {
                'valido': integridade,
                'integridade': integridade,
                'hash_confere': integridade,
                'certificado_valido': True,  # Verificar em produção
                'cadeia_confiavel': True,    # Verificar em produção
                'nao_revogado': True,        # Verificar LCR em produção
                'data_verificacao': datetime.now().isoformat(),
                'mensagem': 'Assinatura válida' if integridade else 'Hash não confere - documento adulterado'
            }
            
            if assinatura.get('carimbo_tempo'):
                resultado['carimbo_tempo_valido'] = True
            
            logger.info(f"Verificação de assinatura: {'válida' if integridade else 'inválida'}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao verificar assinatura: {str(e)}")
            return {
                'valido': False,
                'erro': str(e)
            }
    
    def listar_certificados_disponiveis(self) -> list:
        """
        Lista certificados disponíveis no sistema.
        
        Para certificados A3, lista tokens/smartcards conectados.
        Para certificados A1, lista arquivos .pfx/.p12 configurados.
        """
        # Em produção, verificar dispositivos PKCS#11 para A3
        # e arquivos configurados para A1
        
        return [
            {
                'tipo': 'A1',
                'nome': 'Certificado e-CPF',
                'titular': 'Dr. João Silva',
                'validade': '2025-12-31',
                'disponivel': True
            }
        ]
    
    def obter_carimbo_tempo(self, hash_documento: str) -> Dict:
        """
        Obtém carimbo de tempo de uma TSA (Time Stamp Authority).
        
        Args:
            hash_documento: Hash SHA256 do documento
        
        Returns:
            Dict com carimbo de tempo
        """
        # Em produção, conectar com servidor TSA da ICP-Brasil
        # Exemplo: SERPRO, Certisign, etc.
        
        timestamp = datetime.now().isoformat()
        
        return {
            'timestamp': timestamp,
            'hash': hash_documento,
            'tsa': 'TSA ICP-Brasil',
            'politica': '2.16.76.1.6.2',  # Política de carimbo de tempo ICP-Brasil
            'token': base64.b64encode(f"{hash_documento}:{timestamp}".encode()).decode()
        }
