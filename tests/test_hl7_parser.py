import unittest
import hl7

class TestHL7Parser(unittest.TestCase):

    def test_parser_with_pid_segment(self):
        hl7_message = "MSH|^~\\&|HIS|RIH|EKG|EKG|202512131200||ADT^A01|MSG00001|P|2.5\nPID|1||123456^^^HOSP^MR||DOE^JOHN||19800101|M|||123 MAIN ST^^METROPOLIS^NY^10001||555-555-5555||S||123456789|987-65-4321"
        message = hl7.parse(hl7_message)
        print("Mensagem HL7 após parsing:")
        print(message)

        # Verificar se o segmento PID está presente
        try:
            pid_segment = message.segment("PID")
            print("Segmento PID encontrado:")
            print(pid_segment)
        except KeyError:
            self.fail("Segmento PID não foi encontrado na mensagem HL7.")

if __name__ == "__main__":
    unittest.main()