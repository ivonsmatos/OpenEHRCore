# 🎬 DEMO: Como Ver o "Robô" Clicando na Tela

Este é um guia visual rápido para você ver o Playwright em ação.

---

## 🚀 QUICK START (5 minutos)

### 1️⃣ Certifique-se de que tudo está rodando:

```powershell
# Terminal 1: Backend
cd backend-django
python manage.py runserver

# Terminal 2: Frontend
cd frontend-pwa
npm start
```

### 2️⃣ Instale o Playwright (apenas uma vez):

```powershell
pip install pytest-playwright
playwright install
```

### 3️⃣ Execute o teste com visualização:

```powershell
pytest tests/test_e2e_playwright.py --headed --slowmo 100
```

**O que acontece:**

- 🌐 Um navegador Chromium abre automaticamente
- 🤖 O robô faz login
- 📱 Navega por todas as telas (Dashboard → Pacientes → Agendamento...)
- 🖱️ Clica em botões
- ⌨️ Preenche formulários
- ✅ Valida que nada quebrou

---

## 🎥 COMANDOS ÚTEIS

### Ver apenas um teste específico:

```powershell
# Apenas navegação
pytest tests/test_e2e_playwright.py::test_route_loads_without_crash --headed

# Apenas botões do Dashboard
pytest tests/test_e2e_playwright.py::test_dashboard_buttons_dont_crash --headed --slowmo 200
```

### Modo ultra-lento (para apresentações):

```powershell
pytest tests/test_e2e_playwright.py --headed --slowmo 500
```

### Pausar execução para inspecionar:

Adicione esta linha no código onde quiser pausar:

```python
page.pause()  # Abre o Playwright Inspector
```

---

## 📸 GRAVAR SCREENSHOTS E VÍDEOS

### Tirar screenshot de cada teste:

```powershell
pytest tests/test_e2e_playwright.py --headed --screenshot=on
```

_Screenshots salvos em `test-results/`_

### Gravar vídeo completo:

```powershell
pytest tests/test_e2e_playwright.py --headed --video=on
```

_Vídeos salvos em `test-results/`_

### Apenas vídeos de falhas:

```powershell
pytest tests/test_e2e_playwright.py --video=retain-on-failure
```

---

## 🐛 DEBUG AVANÇADO: Trace Viewer

### Gravar trace completo:

```powershell
pytest tests/test_e2e_playwright.py --tracing=on
```

### Visualizar trace (replay completo):

```powershell
playwright show-trace test-results/<nome-do-teste>/trace.zip
```

**O Trace Viewer mostra:**

- ✅ Linha do tempo completa de todas as ações
- ✅ DOM antes/depois de cada clique
- ✅ Network requests
- ✅ Console logs
- ✅ Screenshots de cada passo

---

## 🎯 EXEMPLO PRÁTICO: Testar Cadastro de Paciente

```python
# Adicione este teste em test_e2e_playwright.py

def test_create_patient_flow(authenticated_page: Page):
    """Testa fluxo completo de cadastro de paciente"""
    page = authenticated_page

    # 1. Ir para lista de pacientes
    page.goto("http://localhost:5173/patients")
    page.wait_for_load_state("networkidle")

    # 2. Clicar em "Novo Paciente"
    page.locator('button:has-text("Novo")').first.click()
    page.wait_for_timeout(1000)

    # 3. Preencher formulário
    page.locator('input[name="firstName"]').fill("João")
    page.locator('input[name="lastName"]').fill("Silva")
    page.locator('input[name="cpf"]').fill("123.456.789-00")

    # 4. Tirar screenshot
    page.screenshot(path="cadastro_paciente.png")

    # 5. Clicar em Salvar
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(2000)

    # 6. Verificar sucesso
    expect(page.locator('text=Paciente criado')).to_be_visible()

    print("✅ Paciente criado com sucesso!")
```

Execute:

```powershell
pytest tests/test_e2e_playwright.py::test_create_patient_flow --headed --slowmo 300
```

---

## 🎨 CUSTOMIZAR NAVEGADOR

### Usar Firefox em vez de Chrome:

```powershell
pytest tests/test_e2e_playwright.py --headed --browser firefox
```

### Testar em Safari (WebKit):

```powershell
pytest tests/test_e2e_playwright.py --headed --browser webkit
```

### Testar em modo mobile:

Adicione no código:

```python
page.set_viewport_size({"width": 375, "height": 667})  # iPhone
```

---

## 🔥 DEMO SHOW (Para Mostrar ao Cliente)

### Script completo de demonstração:

```powershell
# 1. Abrir 3 terminais

# Terminal 1: Backend
cd backend-django
python manage.py runserver

# Terminal 2: Frontend
cd frontend-pwa
npm start

# Terminal 3: Testes (AGUARDE 10s para tudo subir)
pytest tests/test_e2e_playwright.py --headed --slowmo 200 -k "dashboard"
```

**Apresentação:**

1. Mostre os 3 terminais lado a lado
2. Explique: "Vou rodar o teste automatizado"
3. Execute o comando do Terminal 3
4. Navegador abre sozinho
5. Robô faz login
6. Robô clica em todos os botões do Dashboard
7. Cliente vê em tempo real

---

## 📊 RELATÓRIO VISUAL (HTML)

### Gerar relatório HTML bonito:

```powershell
pytest tests/test_e2e_playwright.py --html=report.html --self-contained-html
```

Abra `report.html` no navegador para ver:

- ✅ Lista de todos os testes
- ✅ Screenshots de falhas
- ✅ Logs de console
- ✅ Tempo de execução

---

## 💡 DICAS PRO

### 1. Esperar elemento aparecer:

```python
page.wait_for_selector('button:has-text("Salvar")', timeout=5000)
```

### 2. Verificar se elemento está visível:

```python
expect(page.locator('h1')).to_be_visible()
```

### 3. Tirar screenshot de elemento específico:

```python
page.locator('.dashboard-card').screenshot(path="card.png")
```

### 4. Executar JavaScript:

```python
page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
```

### 5. Interceptar requisições:

```python
page.route('**/api/patients', lambda route: route.fulfill(
    status=200,
    body='{"id": "123"}'
))
```

---

## 🎓 APRENDER MAIS

### Documentação oficial:

- [Playwright Python](https://playwright.dev/python/)
- [Locators](https://playwright.dev/python/docs/locators)
- [Assertions](https://playwright.dev/python/docs/test-assertions)

### Tutoriais em vídeo:

- [Playwright Crash Course](https://www.youtube.com/watch?v=wawbt1cATsk)
- [E2E Testing with Playwright](https://www.youtube.com/watch?v=iDlAA7Mbl0U)

---

## ✅ CHECKLIST PRÉ-DEMO

Antes de mostrar para o cliente/time:

- [ ] Backend rodando sem erros
- [ ] Frontend rodando sem erros de console
- [ ] Credenciais de teste configuradas
- [ ] Playwright instalado (`playwright install`)
- [ ] Testar comando uma vez antes (ensaio)
- [ ] Limpar screenshots/vídeos antigos (`rm -rf test-results/`)
- [ ] Ajustar `--slowmo` para velocidade ideal (200-300ms)

---

**Divirta-se! 🎉**
