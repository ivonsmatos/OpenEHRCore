from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .auth import KeycloakAuthentication, require_role
from .services.fhir_core import FHIRService, FHIRServiceException

class FinancialViewSet(viewsets.ViewSet):
    """
    Base ViewSet for Financial Resources ensuring FHIRService is available.
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = FHIRService()

class CoverageViewSet(FinancialViewSet):
    """
    Gerencia planos de convênio (Coverage).
    """
    def list(self, request):
        try:
            # Se for paciente, filtrar pelo seu ID
            if "paciente" in request.user.roles:
                patient_id = request.user.sub
            else:
                patient_id = request.query_params.get("patient")

            # Mock search using specific patient if provided, else dummy list?
            # FHIRService needs a search_coverage method if we want to list.
            # For now, let's implement a basic search in FHIRService later or just return empty/mock.
            # Actually, standard HAPI listing:
            if patient_id:
                # We need to implement search in fhir_core or do a direct GET /Coverage?beneficiary=...
                # Let's do direct GET proxy for now to save time
                resp = self.service.session.get(
                    f"{self.service.base_url}/Coverage",
                    params={"beneficiary": f"Patient/{patient_id}"}
                )
                if resp.status_code == 200:
                    bundle = resp.json()
                    resources = [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
                    return Response(resources)
            
            return Response([])
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        try:
            data = request.data
            patient_id = data.get("patient_id")
            
            # Security check
            if "paciente" in request.user.roles and request.user.sub != patient_id:
                 return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

            result = self.service.create_coverage_resource(
                patient_id=patient_id,
                payor_name=data.get("payor_name"),
                subscriber_id=data.get("subscriber_id"),
                status=data.get("status", "active")
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except FHIRServiceException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AccountViewSet(FinancialViewSet):
    """
    Gerencia contas de pacientes (Account).
    """
    def list(self, request):
        try:
            if "paciente" in request.user.roles:
                patient_id = request.user.sub
            else:
                patient_id = request.query_params.get("patient")

            if patient_id:
                resp = self.service.session.get(
                    f"{self.service.base_url}/Account",
                    params={"subject": f"Patient/{patient_id}"}
                )
                if resp.status_code == 200:
                    bundle = resp.json()
                    resources = [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
                    return Response(resources)
            return Response([])
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def create(self, request):
        try:
            data = request.data
            result = self.service.create_account_resource(
                patient_id=data.get("patient_id"),
                name=data.get("name", "Conta Paciente")
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class InvoiceViewSet(FinancialViewSet):
    """
    Gerencia Faturas (Invoice).
    """
    def list(self, request):
        try:
            if "paciente" in request.user.roles:
                patient_id = request.user.sub
            else:
                patient_id = request.query_params.get("patient")

            if patient_id:
                resp = self.service.session.get(
                    f"{self.service.base_url}/Invoice",
                    params={"subject": f"Patient/{patient_id}"}
                )
                if resp.status_code == 200:
                    bundle = resp.json()
                    resources = [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
                    return Response(resources)
            return Response([])
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        try:
            data = request.data
            result = self.service.create_invoice_resource(
                patient_id=data.get("patient_id"),
                account_id=data.get("account_id"),
                total_gross=data.get("total_gross"),
                status=data.get("status", "issued")
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
