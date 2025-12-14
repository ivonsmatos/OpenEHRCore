"""
OWASP ZAP Security Scanner for OpenEHR FHIR API
================================================

Script automatizado para executar scan de vulnerabilidades com OWASP ZAP.

Requisitos:
    1. OWASP ZAP instalado: https://www.zaproxy.org/download/
    2. ZAP API habilitada (porta 8080 por padrão)
    3. pip install python-owasp-zap-v2.4

Uso:
    # Scan básico (spider + scan passivo)
    python security/owasp_zap_scan.py --mode quick

    # Scan completo (spider + scan ativo + autenticação)
    python security/owasp_zap_scan.py --mode full

    # Apenas relatório (usa sessão existente)
    python security/owasp_zap_scan.py --mode report

    # Com autenticação JWT
    python security/owasp_zap_scan.py --mode full --auth jwt --token "eyJ..."

Integração CI/CD:
    # Jenkins/GitLab CI
    python security/owasp_zap_scan.py --mode full --exit-on-high

    # GitHub Actions
    - name: OWASP ZAP Scan
      run: |
        docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable \
        zap-baseline.py -t http://api:8000 -r report.html
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from zapv2 import ZAPv2
except ImportError:
    print("❌ ERRO: Instale python-owasp-zap-v2.4")
    print("   pip install python-owasp-zap-v2.4")
    sys.exit(1)


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zap_scan.log')
    ]
)
logger = logging.getLogger(__name__)


class OWASPZAPScanner:
    """
    Wrapper para OWASP ZAP API.
    Executa scans de segurança automatizados.
    """
    
    # Configurações padrão
    ZAP_HOST = 'localhost'
    ZAP_PORT = 8080
    ZAP_API_KEY = None  # Se configurado no ZAP
    
    # Thresholds de alerta
    RISK_LEVELS = {
        'High': 3,
        'Medium': 2,
        'Low': 1,
        'Informational': 0
    }
    
    def __init__(
        self,
        target_url: str,
        api_key: Optional[str] = None,
        zap_host: str = ZAP_HOST,
        zap_port: int = ZAP_PORT
    ):
        """
        Inicializa scanner ZAP.
        
        Args:
            target_url: URL base da aplicação a ser testada
            api_key: API key do ZAP (se habilitado)
            zap_host: Host onde ZAP está rodando
            zap_port: Porta do ZAP API
        """
        self.target_url = target_url.rstrip('/')
        self.zap = ZAPv2(
            apikey=api_key,
            proxies={
                'http': f'http://{zap_host}:{zap_port}',
                'https': f'http://{zap_host}:{zap_port}'
            }
        )
        
        # Diretório para relatórios
        self.report_dir = Path('security/reports')
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔍 ZAP Scanner inicializado")
        logger.info(f"   Target: {self.target_url}")
        logger.info(f"   ZAP Proxy: {zap_host}:{zap_port}")
    
    def start_new_session(self, session_name: Optional[str] = None):
        """Inicia nova sessão ZAP"""
        if session_name is None:
            session_name = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"📝 Criando sessão: {session_name}")
        self.zap.core.new_session(name=session_name, overwrite=True)
        return session_name
    
    def configure_authentication(self, auth_type: str, **kwargs):
        """
        Configura autenticação no ZAP.
        
        Args:
            auth_type: 'jwt', 'basic', 'form'
            **kwargs: Parâmetros específicos do tipo de auth
        """
        if auth_type == 'jwt':
            token = kwargs.get('token')
            if not token:
                logger.error("❌ Token JWT não fornecido")
                return False
            
            # Adiciona header Authorization
            self.zap.replacer.add_rule(
                description='JWT Token',
                enabled=True,
                matchtype='REQ_HEADER',
                matchstring='Authorization',
                replacement=f'Bearer {token}'
            )
            logger.info("✅ Autenticação JWT configurada")
            return True
        
        elif auth_type == 'basic':
            username = kwargs.get('username')
            password = kwargs.get('password')
            
            import base64
            credentials = base64.b64encode(
                f"{username}:{password}".encode()
            ).decode()
            
            self.zap.replacer.add_rule(
                description='Basic Auth',
                enabled=True,
                matchtype='REQ_HEADER',
                matchstring='Authorization',
                replacement=f'Basic {credentials}'
            )
            logger.info("✅ Autenticação Basic configurada")
            return True
        
        else:
            logger.warning(f"⚠️  Tipo de autenticação '{auth_type}' não suportado")
            return False
    
    def spider_scan(self, max_depth: int = 5) -> str:
        """
        Executa spider para descobrir endpoints.
        
        Args:
            max_depth: Profundidade máxima do crawling
            
        Returns:
            scan_id: ID do scan para acompanhamento
        """
        logger.info(f"🕷️  Iniciando Spider Scan (max_depth={max_depth})...")
        
        scan_id = self.zap.spider.scan(
            url=self.target_url,
            maxchildren=None,
            recurse=True,
            contextname=None,
            subtreeonly=None
        )
        
        # Aguarda conclusão
        while int(self.zap.spider.status(scan_id)) < 100:
            progress = self.zap.spider.status(scan_id)
            logger.info(f"   Spider progress: {progress}%")
            time.sleep(5)
        
        logger.info(f"✅ Spider Scan concluído")
        
        # Mostra URLs encontradas
        urls = self.zap.spider.results(scan_id)
        logger.info(f"   URLs encontradas: {len(urls)}")
        
        return scan_id
    
    def passive_scan(self):
        """
        Aguarda conclusão do scan passivo.
        ZAP roda scan passivo automaticamente enquanto spider/active scan.
        """
        logger.info("🔍 Aguardando Passive Scan...")
        
        while int(self.zap.pscan.records_to_scan) > 0:
            remaining = self.zap.pscan.records_to_scan
            logger.info(f"   Registros restantes: {remaining}")
            time.sleep(2)
        
        logger.info("✅ Passive Scan concluído")
    
    def active_scan(self, policy: str = 'Default Policy') -> str:
        """
        Executa scan ativo (invasivo).
        
        Args:
            policy: Política de scan a usar
            
        Returns:
            scan_id: ID do scan
        """
        logger.info(f"⚡ Iniciando Active Scan (policy={policy})...")
        logger.warning("   ⚠️  Active scan é INVASIVO - use apenas em ambiente de teste!")
        
        scan_id = self.zap.ascan.scan(
            url=self.target_url,
            recurse=True,
            inscopeonly=None,
            scanpolicyname=policy,
            method=None,
            postdata=None
        )
        
        # Aguarda conclusão
        while int(self.zap.ascan.status(scan_id)) < 100:
            progress = self.zap.ascan.status(scan_id)
            logger.info(f"   Active scan progress: {progress}%")
            time.sleep(10)
        
        logger.info("✅ Active Scan concluído")
        return scan_id
    
    def ajax_spider_scan(self):
        """
        Executa AJAX Spider para aplicações SPA.
        Útil para frontend React/Vue/Angular.
        """
        logger.info("🌐 Iniciando AJAX Spider (para SPAs)...")
        
        try:
            self.zap.ajaxSpider.scan(url=self.target_url)
            
            while self.zap.ajaxSpider.status == 'running':
                logger.info(f"   AJAX Spider running...")
                time.sleep(5)
            
            logger.info("✅ AJAX Spider concluído")
        except Exception as e:
            logger.warning(f"⚠️  AJAX Spider falhou: {e}")
    
    def get_alerts(self, risk_level: Optional[str] = None) -> List[Dict]:
        """
        Retorna alertas encontrados.
        
        Args:
            risk_level: Filtrar por nível ('High', 'Medium', 'Low', 'Informational')
            
        Returns:
            Lista de alertas
        """
        alerts = self.zap.core.alerts(baseurl=self.target_url)
        
        if risk_level:
            alerts = [a for a in alerts if a['risk'] == risk_level]
        
        return alerts
    
    def generate_report(self, format: str = 'html') -> str:
        """
        Gera relatório do scan.
        
        Args:
            format: 'html', 'json', 'xml', 'md'
            
        Returns:
            Caminho do arquivo gerado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'html':
            report_path = self.report_dir / f'zap_report_{timestamp}.html'
            content = self.zap.core.htmlreport()
        
        elif format == 'json':
            report_path = self.report_dir / f'zap_report_{timestamp}.json'
            content = self.zap.core.jsonreport()
        
        elif format == 'xml':
            report_path = self.report_dir / f'zap_report_{timestamp}.xml'
            content = self.zap.core.xmlreport()
        
        elif format == 'md':
            report_path = self.report_dir / f'zap_report_{timestamp}.md'
            content = self._generate_markdown_report()
        
        else:
            logger.error(f"❌ Formato '{format}' não suportado")
            return None
        
        # Salva relatório
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"📄 Relatório gerado: {report_path}")
        return str(report_path)
    
    def _generate_markdown_report(self) -> str:
        """Gera relatório em Markdown"""
        alerts = self.get_alerts()
        
        # Agrupa por nível de risco
        by_risk = {}
        for alert in alerts:
            risk = alert['risk']
            if risk not in by_risk:
                by_risk[risk] = []
            by_risk[risk].append(alert)
        
        # Gera Markdown
        md = ["# 🔒 OWASP ZAP Security Scan Report\n"]
        md.append(f"**Target:** {self.target_url}\n")
        md.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append(f"**Total Alerts:** {len(alerts)}\n")
        md.append("\n---\n\n")
        
        # Resumo por risco
        md.append("## 📊 Summary\n\n")
        md.append("| Risk Level | Count |\n")
        md.append("|------------|-------|\n")
        for risk in ['High', 'Medium', 'Low', 'Informational']:
            count = len(by_risk.get(risk, []))
            emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 'Informational': '🔵'}[risk]
            md.append(f"| {emoji} {risk} | {count} |\n")
        md.append("\n---\n\n")
        
        # Detalhes por nível de risco
        for risk in ['High', 'Medium', 'Low', 'Informational']:
            if risk not in by_risk:
                continue
            
            emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 'Informational': '🔵'}[risk]
            md.append(f"## {emoji} {risk} Risk Alerts ({len(by_risk[risk])})\n\n")
            
            for idx, alert in enumerate(by_risk[risk], 1):
                md.append(f"### {idx}. {alert['alert']}\n\n")
                md.append(f"**URL:** `{alert['url']}`\n\n")
                md.append(f"**CWE ID:** {alert.get('cweid', 'N/A')}\n\n")
                md.append(f"**WASC ID:** {alert.get('wascid', 'N/A')}\n\n")
                md.append(f"**Description:**\n{alert.get('desc', 'N/A')}\n\n")
                md.append(f"**Solution:**\n{alert.get('solution', 'N/A')}\n\n")
                md.append("---\n\n")
        
        return ''.join(md)
    
    def print_summary(self):
        """Imprime resumo dos alertas"""
        alerts = self.get_alerts()
        
        by_risk = {}
        for alert in alerts:
            risk = alert['risk']
            by_risk[risk] = by_risk.get(risk, 0) + 1
        
        print("\n" + "="*80)
        print("📊 OWASP ZAP SCAN SUMMARY")
        print("="*80)
        print(f"Target: {self.target_url}")
        print(f"Total Alerts: {len(alerts)}")
        print("-"*80)
        print(f"🔴 High:          {by_risk.get('High', 0)}")
        print(f"🟡 Medium:        {by_risk.get('Medium', 0)}")
        print(f"🟢 Low:           {by_risk.get('Low', 0)}")
        print(f"🔵 Informational: {by_risk.get('Informational', 0)}")
        print("="*80 + "\n")
        
        # Mostra High e Medium alerts
        high_alerts = self.get_alerts('High')
        medium_alerts = self.get_alerts('Medium')
        
        if high_alerts:
            print("🔴 HIGH RISK ALERTS:")
            for alert in high_alerts:
                print(f"   - {alert['alert']} ({alert['url']})")
            print()
        
        if medium_alerts:
            print("🟡 MEDIUM RISK ALERTS:")
            for alert in medium_alerts[:5]:  # Mostra apenas 5
                print(f"   - {alert['alert']} ({alert['url']})")
            if len(medium_alerts) > 5:
                print(f"   ... e mais {len(medium_alerts) - 5} alertas")
            print()
    
    def shutdown(self):
        """Desliga ZAP"""
        logger.info("🛑 Encerrando ZAP...")
        try:
            self.zap.core.shutdown()
        except Exception:
            pass


def main():
    """CLI para executar scans"""
    parser = argparse.ArgumentParser(
        description='OWASP ZAP Security Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--target',
        default='http://localhost:8000',
        help='URL alvo (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['quick', 'full', 'report'],
        default='quick',
        help='Modo de scan (default: quick)'
    )
    
    parser.add_argument(
        '--auth',
        choices=['jwt', 'basic', 'none'],
        default='none',
        help='Tipo de autenticação'
    )
    
    parser.add_argument(
        '--token',
        help='JWT token (se --auth jwt)'
    )
    
    parser.add_argument(
        '--username',
        help='Username (se --auth basic)'
    )
    
    parser.add_argument(
        '--password',
        help='Password (se --auth basic)'
    )
    
    parser.add_argument(
        '--exit-on-high',
        action='store_true',
        help='Sai com código 1 se encontrar alertas HIGH (para CI/CD)'
    )
    
    parser.add_argument(
        '--report-format',
        choices=['html', 'json', 'xml', 'md'],
        default='html',
        help='Formato do relatório (default: html)'
    )
    
    args = parser.parse_args()
    
    # Inicializa scanner
    scanner = OWASPZAPScanner(target_url=args.target)
    
    try:
        # Nova sessão
        scanner.start_new_session()
        
        # Configura autenticação
        if args.auth == 'jwt' and args.token:
            scanner.configure_authentication('jwt', token=args.token)
        elif args.auth == 'basic' and args.username and args.password:
            scanner.configure_authentication('basic', 
                username=args.username, password=args.password)
        
        if args.mode == 'quick':
            # Scan rápido: Spider + Passive
            scanner.spider_scan(max_depth=3)
            scanner.passive_scan()
        
        elif args.mode == 'full':
            # Scan completo: Spider + AJAX + Active
            scanner.spider_scan(max_depth=5)
            scanner.ajax_spider_scan()
            scanner.passive_scan()
            scanner.active_scan()
        
        # Gera relatórios
        scanner.generate_report(format=args.report_format)
        scanner.generate_report(format='json')  # Sempre gera JSON
        scanner.generate_report(format='md')    # Sempre gera Markdown
        
        # Mostra resumo
        scanner.print_summary()
        
        # Verifica se deve falhar em CI/CD
        if args.exit_on_high:
            high_alerts = scanner.get_alerts('High')
            if high_alerts:
                logger.error(f"❌ Encontrados {len(high_alerts)} alertas HIGH!")
                sys.exit(1)
        
        logger.info("✅ Scan concluído com sucesso!")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Scan interrompido pelo usuário")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Erro durante scan: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Não desliga ZAP automaticamente para permitir inspeção manual
        # scanner.shutdown()
        pass


if __name__ == '__main__':
    main()
