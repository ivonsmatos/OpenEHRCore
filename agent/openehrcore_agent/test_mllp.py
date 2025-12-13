"""
Test MLLP connection by sending a sample HL7 message.
"""

import socket
import sys

# MLLP framing
MLLP_START = b'\x0b'
MLLP_END = b'\x1c\x0d'


def send_hl7_message(host: str, port: int, message: str) -> str:
    """Send HL7 message via MLLP and return response."""
    
    # Wrap message in MLLP framing
    mllp_message = MLLP_START + message.encode('utf-8') + MLLP_END
    
    # Connect and send
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(mllp_message)
        
        # Receive response
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if MLLP_END in response:
                break
    
    # Extract message from MLLP framing
    if MLLP_START in response and MLLP_END in response:
        start = response.find(MLLP_START) + 1
        end = response.find(MLLP_END)
        return response[start:end].decode('utf-8')
    
    return response.decode('utf-8')


# Sample HL7 messages for testing

SAMPLE_ADT_A01 = """MSH|^~\\&|LAB|HOSPITAL|OPENEHR|CORE|20241213120000||ADT^A01|12345|P|2.5.1
EVN|A01|20241213120000
PID|1|123456^^^HOSP^MR||Silva^João^Carlos||19850315|M|||Rua das Flores 123^^São Paulo^SP^01234-567^BR||11999998888|||S||123456789||
PV1|1|I|ENFERMARIA^101^A^HOSPITAL||||Dr. Santos^Carlos^^^^^MD|Dr. Lima^Ana^^^^^MD||MED||||7|||Dr. Santos^Carlos^^^^^MD|IP||||||||||||||||||HOSPITAL|||||20241213120000"""

SAMPLE_ORU_R01 = """MSH|^~\\&|LAB|HOSPITAL|OPENEHR|CORE|20241213120000||ORU^R01|12346|P|2.5.1
PID|1|123456^^^HOSP^MR||Silva^João^Carlos||19850315|M
OBR|1|LAB123|LAB123|24356-8^HEMOGRAMA^LN|||20241213080000
OBX|1|NM|718-7^HEMOGLOBIN^LN||14.5|g/dL|13.5-17.5|N|||F
OBX|2|NM|789-8^ERITROCITOS^LN||5.2|10*6/uL|4.5-5.5|N|||F
OBX|3|NM|6690-2^LEUCOCITOS^LN||7500|/uL|4000-10000|N|||F"""

SAMPLE_ORM_O01 = """MSH|^~\\&|HIS|HOSPITAL|LAB|LAB|20241213120000||ORM^O01|12347|P|2.5.1
PID|1|123456^^^HOSP^MR||Silva^João^Carlos||19850315|M
ORC|NW|ORD123||||||A|||||Dr. Santos^Carlos^^^^^MD
OBR|1|ORD123||24356-8^HEMOGRAMA^LN|||20241213080000|||||||||||Dr. Santos^Carlos^^^^^MD"""


def main():
    """Run MLLP test."""
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 2575
    
    print(f"Testing MLLP connection to {host}:{port}")
    print("=" * 50)
    
    # Test 1: ADT A01 (Patient Admission)
    print("\n[Test 1] Sending ADT^A01 (Patient Admission)...")
    try:
        response = send_hl7_message(host, port, SAMPLE_ADT_A01)
        print(f"Response:\n{response}")
        
        if "MSA|AA" in response:
            print("✅ ADT^A01 accepted")
        else:
            print("⚠️ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: ORU R01 (Lab Results)
    print("\n[Test 2] Sending ORU^R01 (Lab Results)...")
    try:
        response = send_hl7_message(host, port, SAMPLE_ORU_R01)
        print(f"Response:\n{response}")
        
        if "MSA|AA" in response:
            print("✅ ORU^R01 accepted")
        else:
            print("⚠️ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: ORM O01 (Lab Order)
    print("\n[Test 3] Sending ORM^O01 (Lab Order)...")
    try:
        response = send_hl7_message(host, port, SAMPLE_ORM_O01)
        print(f"Response:\n{response}")
        
        if "MSA|AA" in response:
            print("✅ ORM^O01 accepted")
        else:
            print("⚠️ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("MLLP test completed")


if __name__ == '__main__':
    main()
