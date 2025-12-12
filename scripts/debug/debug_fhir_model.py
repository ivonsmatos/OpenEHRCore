
from fhirclient.models.composition import Composition, CompositionSection
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.narrative import Narrative
from datetime import datetime

try:
    print("Initializing Composition...")
    comp = Composition()
    
    print("Setting status...")
    comp.status = "final"
    
    print("Setting date...")
    # Test current fix (no microseconds)
    date_str = "2025-12-05"
    print(f"Date string: {date_str}")
    fd = FHIRDate(date_str)
    print(f"FHIRDate created: {fd.as_json()}")
    comp.date = fd  
    print("FHIRDate assigned successfully")
    
    print("Setting title...")
    comp.title = "Test Document"
    
    print("Setting type...")
    doc_type_concept = CodeableConcept()
    doc_type_concept.coding = [Coding()]
    doc_type_concept.coding[0].system = "http://loinc.org"
    doc_type_concept.coding[0].code = "11506-3"
    doc_type_concept.coding[0].display = "Progress note"
    comp.type = doc_type_concept
    
    print("Setting subject...")
    subject_ref = FHIRReference()
    subject_ref.reference = "Patient/patient-1"
    comp.subject = subject_ref
    
    print("Setting author...")
    author_ref = FHIRReference()
    author_ref.reference = "Practitioner/practitioner-1"
    comp.author = [author_ref]

    print("Setting section...")
    section = CompositionSection()
    section.title = "Conteúdo Principal"
    div_content = "<div xmlns=\"http://www.w3.org/1999/xhtml\">Test content</div>"
    narrative = Narrative()
    narrative.status = "generated"
    narrative.div = div_content
    section.text = narrative
    comp.section = [section]
    
    print("Serializing to JSON...")
    comp_json = comp.as_json()
    print("✅ Success!")
    
except Exception as e:
    print(f"❌ Error: {e}")
