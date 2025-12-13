import unittest
from agente.hl7.processor import HL7Processor

class TestHL7Processor(unittest.TestCase):

    def setUp(self):
        self.processor = HL7Processor()

    def test_parse_valid_message(self):
        hl7_message = "MSH|^~\\&|HIS|RIH|EKG|EKG|202512131200||ADT^A01|MSG00001|P|2.5\nPID|1||123456^^^HOSP^MR||DOE^JOHN||19800101|M|||123 MAIN ST^^METROPOLIS^NY^10001||555-555-5555||S||123456789|987-65-4321"
        result = self.processor.parse(hl7_message)
        self.assertEqual(result.resource_type, "Patient")
        self.assertEqual(result.name[0].family, "DOE")
        self.assertEqual(result.name[0].given[0], "JOHN")

    def test_parse_invalid_message(self):
        hl7_message = "MSH|^~\\&|HIS|RIH|EKG|EKG|202512131200||ADT^A01|MSG00001|P|2.5"
        with self.assertRaises(ValueError):
            self.processor.parse(hl7_message)

if __name__ == "__main__":
    unittest.main()