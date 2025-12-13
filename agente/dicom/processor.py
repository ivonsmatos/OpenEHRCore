# DICOM Processor
# Processa arquivos DICOM e converte para recursos FHIR

from fhir.resources.imagingstudy import ImagingStudy
import pydicom

class DICOMProcessor:
    def process(self, dicom_file: str) -> ImagingStudy:
        print(f"Processando arquivo DICOM: {dicom_file}")
        try:
            # Ler o arquivo DICOM
            if isinstance(dicom_file, pydicom.dataset.Dataset):
                ds = dicom_file
            else:
                ds = pydicom.dcmread(dicom_file)

            # Validar atributos obrigatórios
            required_attributes = ['StudyInstanceUID', 'PatientID', 'StudyDate', 'StudyTime']
            for attr in required_attributes:
                if not hasattr(ds, attr):
                    raise ValueError(f"Atributo obrigatório ausente: {attr}")

            # Criar recurso FHIR ImagingStudy com base nos dados DICOM
            imaging_study = ImagingStudy(
                id=ds.StudyInstanceUID,  # UID do estudo
                status="available",
                subject={"reference": f"Patient/{ds.PatientID}"},
                started=ds.StudyDate + "T" + ds.StudyTime  # Data e hora do estudo
            )
            return imaging_study
        except Exception as e:
            print(f"Erro ao processar arquivo DICOM: {e}")
            raise

    def parse(self, dicom_file: str) -> ImagingStudy:
        return self.process(dicom_file)