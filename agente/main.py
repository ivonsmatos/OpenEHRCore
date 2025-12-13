# OpenEHRCore Agent
# Ponto de entrada para o agente on-premise

from hl7.processor import HL7Processor
from dicom.processor import DICOMProcessor
from fhir.sender import FHIRSender

def main():
    print("Iniciando o OpenEHRCore Agent...")

    # Inicializar processadores
    hl7_processor = HL7Processor()
    dicom_processor = DICOMProcessor()
    fhir_sender = FHIRSender()

    # Exemplo: Processar mensagem HL7
    hl7_message = """MSH|^~\&|HIS|RAD|EHR|HOSP|202512131200||ORM^O01|123456|P|2.3"""
    fhir_resource = hl7_processor.process(hl7_message)
    fhir_sender.send(fhir_resource)

    # Exemplo: Processar arquivo DICOM
    dicom_file = "path/to/dicom/file.dcm"
    fhir_resource = dicom_processor.process(dicom_file)
    fhir_sender.send(fhir_resource)

if __name__ == "__main__":
    main()