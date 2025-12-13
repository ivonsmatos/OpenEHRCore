import unittest
from agente.dicom.processor import DICOMProcessor
from pydicom.dataset import Dataset

class TestDICOMProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = DICOMProcessor()

    def test_parse_valid_dicom(self):
        dicom_data = Dataset()
        dicom_data.PatientName = "DOE^JOHN"
        dicom_data.PatientID = "123456"
        dicom_data.StudyInstanceUID = "1.2.3.4"
        dicom_data.SeriesInstanceUID = "1.2.3.4.5"
        dicom_data.SOPInstanceUID = "1.2.3.4.5.6"
        dicom_data.StudyDate = "2025-12-13"
        dicom_data.StudyTime = "12:00:00+00:00"
        result = self.processor.parse(dicom_data)
        self.assertEqual(result.__resource_type__, "ImagingStudy")
        self.assertEqual(result.id, "1.2.3.4")

    def test_parse_invalid_dicom(self):
        dicom_data = Dataset()  # Missing required fields
        with self.assertRaises(ValueError):
            self.processor.parse(dicom_data)

if __name__ == "__main__":
    unittest.main()