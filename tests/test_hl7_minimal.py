import unittest

class TestHL7Minimal(unittest.TestCase):

    def test_minimal_message(self):
        # Construção manual da mensagem HL7 sem validação
        hl7_message = "MSH|^~\\&|HIS|RIH|EKG|EKG|202512131200||ADT^A01|MSG00001|P|2.5\nPID|1||123456"
        segments = hl7_message.split("\n")
        parsed_message = {segment.split("|")[0]: segment for segment in segments}

        # Verificar se o segmento PID está presente
        pid_segment = parsed_message.get("PID")
        self.assertIsNotNone(pid_segment, "Segmento PID não foi encontrado na mensagem HL7.")
        print("Segmento PID encontrado:")
        print(pid_segment)

if __name__ == "__main__":
    unittest.main()