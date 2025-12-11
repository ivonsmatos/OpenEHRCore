# OpenEHRCore Mobile App

Portal do Paciente para dispositivos móveis (iOS e Android).

## 🚀 Tecnologias

- **React Native** com Expo SDK 51
- **TypeScript** para tipagem estática
- **Expo Router** para navegação baseada em arquivos
- **Expo Notifications** para push notifications
- **Expo Secure Store** para armazenamento seguro de tokens
- **Zustand** para gerenciamento de estado

## 📱 Funcionalidades

### Sprint 26 - Patient Portal Mobile

- **Portal do Paciente**
  - Dashboard com informações de saúde
  - Ações rápidas (agendar, exames, receitas)
  - Resumo de sinais vitais

- **Agendamento**
  - Lista de consultas (próximas e histórico)
  - Status de consultas (agendado, confirmado, realizado)
  - Agendamento de novas consultas

- **Prontuário**
  - Categorias (consultas, exames, receitas, vacinas, alergias)
  - Documentos recentes
  - Ações LGPD (exportar dados, histórico de acessos)

- **Notificações Push**
  - Lembretes de consultas
  - Resultados de exames
  - Lembretes de medicamentos
  - Alertas do sistema

- **Perfil**
  - Dados pessoais e contato
  - Plano de saúde
  - Configurações de privacidade
  - Segurança (senha, biometria)

## 🛠️ Setup

### Pré-requisitos

- Node.js 18+
- npm ou yarn
- Expo CLI
- iOS Simulator (Mac) ou Android Emulator

### Instalação

```bash
# Instalar dependências
cd mobile-app
npm install

# Iniciar servidor de desenvolvimento
npm start

# Executar no iOS
npm run ios

# Executar no Android
npm run android
```

### Configuração

1. Copie o arquivo de exemplo de ambiente:

```bash
cp .env.example .env
```

2. Configure as variáveis:

```env
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📁 Estrutura

```
mobile-app/
├── app/                    # Expo Router pages
│   ├── (auth)/            # Autenticação
│   │   ├── _layout.tsx
│   │   └── login.tsx
│   ├── (tabs)/            # Tabs principais
│   │   ├── _layout.tsx
│   │   ├── index.tsx      # Home
│   │   ├── appointments.tsx
│   │   ├── records.tsx
│   │   ├── notifications.tsx
│   │   └── profile.tsx
│   └── _layout.tsx        # Root layout
├── src/
│   ├── components/        # Componentes reutilizáveis
│   ├── hooks/             # Custom hooks
│   ├── services/          # API e serviços
│   │   └── api.ts
│   ├── store/             # Estado global
│   │   ├── AuthContext.tsx
│   │   └── NotificationContext.tsx
│   ├── theme/             # Design system
│   │   └── colors.ts
│   └── types/             # Tipos TypeScript
├── assets/                # Imagens e fontes
├── app.json              # Configuração Expo
├── package.json
└── tsconfig.json
```

## 🔔 Push Notifications

### Configuração iOS

1. Configure o Bundle ID no Apple Developer Portal
2. Crie um Push Notification Key
3. Configure no Expo

### Configuração Android

1. Configure o Firebase Cloud Messaging
2. Adicione `google-services.json` ao projeto
3. Configure no Expo

## 🔒 Segurança

- Tokens armazenados com `expo-secure-store`
- Refresh token automático
- Suporte a biometria (Face ID, Touch ID, Fingerprint)
- LGPD compliance integrado

## 📄 Licença

MIT
