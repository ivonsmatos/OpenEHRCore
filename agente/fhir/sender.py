# FHIR Sender
# Envia recursos FHIR para o backend

import requests
import logging
import json

logging.basicConfig(level=logging.INFO)

class FHIRSender:
    def __init__(self, fhir_server_url="http://localhost:8080/fhir"):
        self.fhir_server_url = fhir_server_url

    def send(self, resource):
        print(f"Enviando recurso FHIR para {self.fhir_server_url}...")
        headers = {"Content-Type": "application/fhir+json"}
        try:
            resource_json = json.loads(resource.json())  # Garantir compatibilidade com JSON
            response = requests.post(
                f"{self.fhir_server_url}/{resource.__resource_type__}",
                json=resource_json,
                headers=headers
            )
            response.raise_for_status()
            logging.info("Recurso enviado com sucesso!")
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar recurso: {e}")
            raise

if __name__ == "__main__":
    from fhir.resources.patient import Patient

    # Configuração de exemplo para teste
    fhir_server_url = "http://localhost:8080/fhir"
    sender = FHIRSender(fhir_server_url)

    # Criar um recurso FHIR de exemplo
    patient = Patient(
        id="example-patient",
        name=[{"family": "Doe", "given": ["John"]}],
        gender="male",
        birthDate="1980-01-01"
    )

    # Enviar o recurso
    sender.send(patient)