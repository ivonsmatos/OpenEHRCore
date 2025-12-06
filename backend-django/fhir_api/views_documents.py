
import logging
from io import BytesIO
from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from django.http import HttpResponse

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, require_role

# ReportLab inputs
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. LISTAR E CRIAR COMPOSITION (Documento Clínico)
# --------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def documents_list_create(request):
    """
    GET: Lista documentos clínicos (converte FHIR Composition -> JSON simples)
    POST: Cria novo documento
    """
    if request.method == 'GET':
        try:
            fhir_service = FHIRService()
            # Buscar compositions ordenadas por data (se possível no FHIR, senão ordena em memória)
            # Para simplificar, buscamos tudo e ordenamos aqui.
            compositions = fhir_service.search_resources('Composition', search_params={'_sort': '-date'})
            
            documents = []
            for comp in compositions:
                # Extrair dados relevantes para a lista
                doc_type_code = comp.get('type', {}).get('coding', [{}])[0].get('code', 'unknown')
                
                # Mapear códigos para labels legíveis (simplificado)
                type_map = {
                    '11488-4': 'Consultation note',
                    '11506-3': 'Progress note',
                    '18842-5': 'Discharge summary',
                    '28655-9': 'Physician attending Note', # Atestado (adaptado)
                     # Mapear nossos tipos customizados
                    'anamnese': 'Anamnese',
                    'evolucao': 'Evolução',
                    'atestado': 'Atestado',
                    'receita': 'Receita'
                }
                # Tentar pegar do text se tiver
                type_display = comp.get('type', {}).get('coding', [{}])[0].get('display') or doc_type_code
                
                # Formatar data
                date_str = comp.get('date', '')
                
                # Author
                author_ref = comp.get('author', [{}])[0].get('reference', 'Desconhecido')
                
                documents.append({
                    'id': comp.get('id'),
                    'title': comp.get('title', 'Sem Título'),
                    'date': date_str,
                    'author': author_ref, # Idealmente resolver o Practitioner
                    'type': type_display,
                    'status': comp.get('status')
                })
                
            return Response(documents, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            from django.http import JsonResponse
            return JsonResponse({"error": "Failed to list documents", "detail": str(e)}, status=500)

    elif request.method == 'POST':
        return create_composition_internal(request)

def create_composition_internal(request):
    """
    Cria um novo documento clínico (Composition).
    
    Payload esperado:
    {
        "patient_id": "patient-1",
        "doc_type": "anamnese" | "evolucao" | "atestado",
        "title": "Evolução de Enfermagem",
        "text_content": "Paciente refere melhora..."
    }
    """
    try:
        user_info = request.user
        logger.info(f"Creating document. User: {user_info.get('preferred_username')}")
        
        data = request.data
        patient_id = data.get('patient_id')
        doc_type = data.get('doc_type', 'evolucao')
        title = data.get('title', 'Documento Clínico')
        text_content = data.get('text_content', '')
        
        # Obter Practitioner ID do usuário logado (assumindo que o ID do Keycloak map para Practitioner)
        # Em um cenário real, consultaríamos o Practitioner pelo email/username
        practitioner_id = "practitioner-1" # Mock
        
        if not patient_id:
            return Response({"error": "patient_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        fhir_service = FHIRService()
        result = fhir_service.create_composition_resource(
            patient_id=patient_id,
            practitioner_id=practitioner_id,
            date_time=datetime.now().date().isoformat(),
            doc_type=doc_type,
            title=title,
            text_content=text_content
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating composition: {str(e)}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Internal Error", "detail": str(e)}, status=500)

# --------------------------------------------------------------------------
# 2. DELETAR DOCUMENTO
# --------------------------------------------------------------------------

@api_view(['DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def delete_document(request, composition_id):
    """
    Deleta um documento clínico pelo ID.
    """
    try:
        fhir_service = FHIRService()
        fhir_service.delete_composition_resource(composition_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return Response({"error": "Failed to delete document"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --------------------------------------------------------------------------
# 3. GERAR PDF (Visualização de Documento - DADOS REAIS)
# --------------------------------------------------------------------------

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def generate_pdf(request, composition_id):
    """
    Gera um PDF para um Composition específico com dados REAIS do FHIR.
    """
    try:
        fhir_service = FHIRService()
        
        # 1. Buscar dados do Composition
        comp = fhir_service.get_composition_by_id(composition_id)
        
        # Extrair dados do documento
        title = comp.get('title', 'Documento Sem Título')
        date_str = comp.get('date', 'Data desconhecida')
        
        # Status
        doc_status = comp.get('status', 'preliminary')
        
        # Extrair conteúdo (Sections)
        sections_content = []
        if 'section' in comp:
            for section in comp['section']:
                sec_title = section.get('title', '')
                # Tentar extrair texto do Narrative (HTML div) ou usar placeholder
                # O FHIR retorna <div ...>texto</div>. Vamos tentar limpar tags simples ou exibir o raw se necessário.
                # Para MVP, vamos pegar o texto cru se possível, ou assumir que salvamos "section.text.div"
                raw_div = section.get('text', {}).get('div', '')
                
                # Limpeza simples de tags HTML (ex: remover <div...>) para o ReportLab
                import re
                clean_text = re.sub(r'<[^>]+>', '', raw_div)
                
                sections_content.append({"title": sec_title, "text": clean_text})
        
        # 2. Buscar Nome do Paciente (Referência)
        # Author: "Patient/123"
        patient_name = "Paciente Não Identificado"
        try:
            subject_ref = comp.get('subject', {}).get('reference', '')
            if 'Patient/' in subject_ref:
                pat_id = subject_ref.split('/')[-1]
                patient = fhir_service.get_patient_by_id(pat_id)
                # Montar nome
                name_list = patient.get('name', [{}])[0]
                given = " ".join(name_list.get('given', []))
                family = name_list.get('family', '')
                patient_name = f"{given} {family}".strip()
            else:
                patient_name = subject_ref or "N/A"
        except:
             patient_name = "Erro ao buscar nome do paciente"

        # 3. Buscar Nome do Profissional
        practitioner_name = "Profissional Não Identificado"
        try:
            author_ref = comp.get('author', [{}])[0].get('reference', '')
            if 'Practitioner/' in author_ref and 'practitioner-1' in author_ref:
                 practitioner_name = "Dr. Ivon Matos (Responsável Técnico)" # Valor fixo para o mock
            elif author_ref:
                 practitioner_name = author_ref
        except:
            pass

        # 4. Construir o PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Cabeçalho
        story.append(Paragraph(f"OpenEHRCore - Documento Clínico ({doc_status})", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Metadados em Tabela (Mais bonito)
        data_table = [
            [Paragraph(f"<b>Paciente:</b> {patient_name}", styles['Normal'])],
            [Paragraph(f"<b>Data:</b> {date_str}", styles['Normal'])],
            [Paragraph(f"<b>Profissional:</b> {practitioner_name}", styles['Normal'])],
        ]
        t = Table(data_table, colWidths=[16*cm], style=[
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('topPadding', (0,0), (-1,-1), 6),
            ('bottomPadding', (0,0), (-1,-1), 6),
        ])
        story.append(t)
        story.append(Spacer(1, 24))
        
        # Título Principal
        story.append(Paragraph(title, styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Conteúdo das Seções
        if not sections_content:
             story.append(Paragraph("<i>Nenhum conteúdo registrado.</i>", styles['Normal']))
        else:
            for sec in sections_content:
                if sec['title']:
                    story.append(Paragraph(sec['title'], styles['Heading3']))
                story.append(Paragraph(sec['text'], styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Rodapé
        story.append(Spacer(1, 48))
        story.append(Paragraph(f"<i>Gerado por OpenEHRCore em {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>", styles['Italic']))
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="documento_{composition_id}.pdf"'
        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        # Em caso de erro, retornar JSON para debug no frontend se não for abrir direto na janela
        # Mas como é window.open, melhor garantir um PDF de erro ou 500
        return Response({"error": "Failed to generate PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
