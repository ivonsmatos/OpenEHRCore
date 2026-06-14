# Checklist de Produção — OpenEHRCore / HealthStack

> **Prioridades:** P0 = bloqueia produção · P1 = antes de cliente real · P2 = melhoria.
> Ambiente atual (`*.actahub.com.br`) é **DEMO com dados sintéticos** numa VPS
> compartilhada. **Não usar com dado real de paciente** até concluir os P0 de infra/LGPD.

## A. Funcional (E2E)
- [ ] **P0** Login/logout por papel (médico, enfermeiro, admin); token expirado → re-login
- [ ] **P0** Navegação de todas as rotas do SPA sem erro (regressão do Service Worker)
- [ ] **P1** CRUD de cada recurso FHIR: Patient, Practitioner, Encounter, Observation, Condition, Allergy, Medication, CarePlan, Appointment, Coverage
- [ ] **P1** Validação de registro (CRM → `pending` + link), CBO, CPF/CNS
- [ ] **P1** Assistente/Resumo IA (Gemini): resposta + citação + disclaimer "apoio à decisão"
- [ ] **P2** Agendamento, leitos/internação, faturamento/TISS, portal do paciente, transcrição

## B. Segurança
- [ ] **P0** RBAC no servidor (não só UI) — testar 403 por papel
- [ ] **P0** IDOR/multi-tenant: clínica A não acessa dados da clínica B
- [ ] **P0** Keycloak em modo produção (hoje `start-dev`), TLS, senhas fortes, realm versionado
- [ ] **P0** Rate-limit na API do assistente (regra WAF) — API key já implementada
- [ ] **P1** Headers (CSP/HSTS/X-Content-Type), CORS restrito, cookies seguros
- [ ] **P1** Segredos fora de código/imagem (feito p/ Gemini) + secrets manager
- [ ] **P1** `npm audit` / `pip-audit` / Trivy + scan OWASP ZAP (`backend-django/security/`)

## C. LGPD / Conformidade em saúde
- [ ] **P0** Dados em região **Brasil** (não na VPS compartilhada)
- [ ] **P0** Trilha de auditoria (AuditEvent) em todo acesso/alteração de dado de paciente
- [ ] **P0** De-identificar a pergunta/dados antes de enviar à IA (aplicar `llm_client.redact_pii`)
- [ ] **P1** Consentimento + base legal; DPA com Google (Vertex SP) e com cada clínica
- [ ] **P1** Direito de exclusão/exportação + retenção/expurgo
- [ ] **P2** Certificação SBIS-CFM (S-RES); ISO 27001

## D. Infra / Deploy
- [ ] **P0** Infra dedicada no Brasil (não compartilhada) p/ dado real
- [ ] **P0** Service Worker: navegação network-first (corrigido — não quebrar deploys)
- [ ] **P0** Backups testados (Postgres) + restore drill + DR
- [ ] **P1** Monitoramento/alertas (uptime, erros, latência) + health checks
- [ ] **P1** CI verde + pipeline de release zero-downtime; migrações idempotentes

## E. Performance / Escala
- [ ] **P1** RAG: índice JSON (214 MB em RAM, cosseno O(n)) → **pgvector**
- [ ] **P1** Teste de carga (k6/Locust); HAPI FHIR com índices/paginação
- [ ] **P2** Frontend: Lighthouse, bundle size, lazy-load

## F. Dados / Qualidade
- [ ] **P1** Seed clinicamente coerente (atual é aleatório)
- [ ] **P1** Terminologias (CID-10, CIAP-2, CBO) + testes de mapeamento FHIR

## G. Produto
- [ ] **P1** Consolidar **uma** marca (hoje: HealthStack / OpenEHRCore / Grephub / Sintonia / actahub)
