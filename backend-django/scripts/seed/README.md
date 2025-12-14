# 🌱 Scripts de Seed - OpenEHR Core

Scripts para popular o banco de dados com dados de teste e demonstração.

## 📁 Estrutura

```
scripts/seed/
├── seed_dashboard_data.py         # Dados para dashboard e analytics
├── seed_fhir_data.py              # Recursos FHIR completos
├── seed_fhir_direct.py            # Seed direto de recursos FHIR
├── seed_practitioners_beds.py     # Profissionais e leitos
├── seed_practitioners.py          # Profissionais de saúde
├── seed_hospital_structure.py     # Estrutura hospitalar
└── seed_admissions.py             # Admissões de pacientes
```

## 🚀 Como Usar

### Seed Completo (Recomendado)

```bash
cd backend-django
python scripts/seed/seed_fhir_data.py
```

### Seeds Específicos

```bash
# Estrutura hospitalar (locais, departamentos)
python scripts/seed/seed_hospital_structure.py

# Profissionais de saúde
python scripts/seed/seed_practitioners.py

# Profissionais e leitos juntos
python scripts/seed/seed_practitioners_beds.py

# Admissões de pacientes
python scripts/seed/seed_admissions.py

# Dados para dashboard
python scripts/seed/seed_dashboard_data.py

# Recursos FHIR direto
python scripts/seed/seed_fhir_direct.py
```

### Com Conda

```bash
conda run -p C:\Users\ivonm\anaconda3 --no-capture-output python scripts/seed/seed_fhir_data.py
```

## 📊 O Que Cada Script Cria

### seed_fhir_data.py

**Cria:**

- ✅ 50 Pacientes (Patient)
- ✅ 20 Profissionais (Practitioner)
- ✅ 30 Encontros (Encounter)
- ✅ 40 Observações (Observation)
- ✅ 25 Medicamentos (MedicationRequest)
- ✅ 15 Procedimentos (Procedure)
- ✅ 10 Condições (Condition)

### seed_hospital_structure.py

**Cria:**

- ✅ Locais (Location)
- ✅ Departamentos
- ✅ Salas e enfermarias
- ✅ Hierarquia hospitalar

### seed_practitioners.py

**Cria:**

- ✅ Médicos de diferentes especialidades
- ✅ Enfermeiros
- ✅ Técnicos
- ✅ Profissionais administrativos

### seed_practitioners_beds.py

**Cria:**

- ✅ Profissionais completos
- ✅ Leitos hospitalares
- ✅ Associações leito-paciente

### seed_admissions.py

**Cria:**

- ✅ Admissões hospitalares
- ✅ Histórico de internações
- ✅ Status de leitos

### seed_dashboard_data.py

**Cria:**

- ✅ Métricas para dashboard
- ✅ Dados para gráficos
- ✅ Estatísticas agregadas
- ✅ Indicadores de performance

### seed_fhir_direct.py

**Cria:**

- ✅ Recursos FHIR completos
- ✅ Validação FHIR R4
- ✅ Referências entre recursos

## ⚙️ Configuração

### Pré-requisitos

1. **Banco de dados configurado:**

```bash
python manage.py migrate
```

2. **Dependências instaladas:**

```bash
pip install -r requirements.txt
```

3. **Variáveis de ambiente:**

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/openehrcore
SECRET_KEY=your-secret-key
```

## 🔄 Ordem de Execução Recomendada

Para popular um sistema do zero:

```bash
# 1. Estrutura hospitalar
python scripts/seed/seed_hospital_structure.py

# 2. Profissionais
python scripts/seed/seed_practitioners.py

# 3. Dados FHIR completos
python scripts/seed/seed_fhir_data.py

# 4. Admissões
python scripts/seed/seed_admissions.py

# 5. Dados para dashboard
python scripts/seed/seed_dashboard_data.py
```

Ou simplesmente:

```bash
# Seed completo (recomendado)
python scripts/seed/seed_fhir_data.py
```

## 🧹 Limpar Dados

Para remover todos os dados de teste:

```bash
# Cuidado: remove TODOS os dados!
python manage.py flush --no-input
```

## 📝 Personalização

### Modificar Quantidade de Dados

Edite o arquivo de seed desejado:

```python
# seed_fhir_data.py
NUM_PATIENTS = 100  # Altere de 50 para 100
NUM_ENCOUNTERS = 200  # Altere de 30 para 200
```

### Adicionar Novos Tipos de Dados

```python
# Exemplo: adicionar novo recurso
def create_goals():
    for i in range(20):
        Goal.objects.create(
            lifecycle_status='active',
            description={'text': f'Meta {i}'},
            # ...
        )
```

## 🐛 Troubleshooting

### Erro: IntegrityError (duplicate key)

**Causa:** Dados já existem no banco  
**Solução:**

```bash
python manage.py flush
# ou
python manage.py shell -c "from fhir_api.models import *; Patient.objects.all().delete()"
```

### Erro: OperationalError (database doesn't exist)

**Causa:** Banco não criado  
**Solução:**

```bash
python manage.py migrate
```

### Erro: ImportError

**Causa:** Dependências não instaladas  
**Solução:**

```bash
pip install -r requirements.txt
```

## 🎯 Verificar Dados Criados

```bash
python manage.py shell
```

```python
from fhir_api.models import Patient, Practitioner, Encounter

print(f"Pacientes: {Patient.objects.count()}")
print(f"Profissionais: {Practitioner.objects.count()}")
print(f"Encontros: {Encounter.objects.count()}")
```

## 📚 Documentação Adicional

- [API Documentation](../../../docs/API.md)
- [FHIR Resources](../../../docs/FHIR_RESOURCES.md)
- [Setup Guide](../../../docs/SETUP.md)

## ⚠️ Avisos

- ⚠️ **Não use em produção!** Estes scripts são apenas para desenvolvimento/testes
- ⚠️ Os dados gerados são fictícios
- ⚠️ Alguns scripts podem sobrescrever dados existentes
- ⚠️ Sempre faça backup antes de executar em ambiente com dados reais

## ✅ Checklist

Antes de executar seeds:

- [ ] Migrations aplicadas
- [ ] Banco de dados criado
- [ ] Variáveis de ambiente configuradas
- [ ] Dependências instaladas
- [ ] Backup dos dados (se necessário)
