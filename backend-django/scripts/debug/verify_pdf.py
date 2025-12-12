import requests
import os

token = "dev-token-bypass"
url = "http://localhost:8000/api/v1/analytics/report/"
output_file = "check_report.pdf"

print(f"Baixando relatório de: {url}")
try:
    response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
    print(f"Tamanho: {len(response.content)} bytes")
    
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        # Check assertions
        is_pdf = response.content.startswith(b'%PDF-1.4')
        print(f"É um PDF válido (Magic Bytes)? {is_pdf}")
        
        if is_pdf:
            print(f"SUCESSO: Arquivo salvo como '{output_file}'.")
        else:
            print("FALHA: O conteúdo não parece ser um PDF.")
            print(f"Início do conteúdo: {response.content[:20]}")
    else:
        print("FALHA: Erro no download.")
        print(response.text)

except Exception as e:
    print(f"ERRO DE CONEXÃO: {e}")
