# HL7 Processor
# Processa mensagens HL7 e converte para recursos FHIR

# Adicionar logs detalhados para depuração
from fhir.resources.patient import Patient
import hl7

class HL7Processor:
    def process(self, hl7_message: str) -> Patient:
        print("Processando mensagem HL7...")
        # Parse a mensagem HL7
        try:
            if not hl7_message.startswith("MSH"):
                raise ValueError("Mensagem HL7 inválida: deve começar com o segmento MSH.")

            print("Mensagem HL7 recebida:")
            print(hl7_message)

            message = hl7.parse(hl7_message)

            print("Mensagem HL7 após parsing:")
            print(message)

            # Validar presença de segmentos obrigatórios
            required_segments = ["PID"]
            for segment in required_segments:
                try:
                    print(f"Verificando segmento: {segment}")
                    message.segment(segment)
                except KeyError:
                    raise ValueError(f"Segmento obrigatório ausente: {segment}")

            msh = message.segment("MSH")
            pid = message.segment("PID")

            # Criar recurso FHIR Patient com base nos segmentos HL7
            patient = Patient(
                id=pid[3][0],  # ID do paciente
                name=[{
                    "family": pid[5][0],  # Sobrenome
                    "given": [pid[5][1]]  # Nome
                }],
                gender="male" if pid[8][0] == "M" else "female",
                birthDate=pid[7][0]  # Data de nascimento
            )
            return patient
        except Exception as e:
            print(f"Erro ao processar mensagem HL7: {e}")
            raise

    def parse(self, hl7_message: str) -> Patient:
        return self.process(hl7_message)