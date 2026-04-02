# AssemblPro - Roadmap de Evolução

> Sistema de Votação Eletrônica para Cooperativas e Órgãos Deliberativos
> Criado em: 02/04/2026
> Atualizado em: 02/04/2026 — Análise competitiva vs Assembleias Virtuais (GRTS Digital)

---

## Estado Atual

### Backend (FastAPI + PostgreSQL)
- 11 modelos (Usuario, Cooperado, Eleicao, Candidato, Chapa, Pauta, Voto, ConviteVotacao, OtpVotacao, LogAuditoria, Configuracao)
- 11 routers (~80+ endpoints)
- 3 services (Auditoria, Email, SMS)
- Auth: JWT + OTP/TOTP + login sem senha
- Segurança: hash de voto SHA-256, audit trail com cadeia de integridade
- Providers SMS: Comtele, Twilio, Zenvia, AWS SNS, TotalVoice

### Frontend (Flutter)
- 6 telas: Splash, Login, OTP, Home, Votar, Comprovante
- 3 providers: Auth, Eleicao, Theme
- Login: CPF+senha, biometria, código SMS/email
- Multi-plataforma: iOS, Android, Web, Desktop

### Nossas Vantagens sobre o Concorrente (GRTS)
- App nativo Flutter (eles só têm web responsivo)
- Biometria (fingerprint/face) para login e votação
- Blockchain audit trail (cadeia de integridade com hash encadeado)
- Login sem senha (código SMS/email direto)
- MFA/TOTP nativo
- Multi-provider SMS (5 provedores configuráveis)

### Concorrente (GRTS / Assembleias Virtuais) - Números
- +2000 assembleias realizadas
- +1 MI votantes habilitados
- +600 mil votos registrados
- +500 clientes
- 80% média de quórum
- Clientes: Unilever, IBM, Coca-Cola, Raízen, Samsung, Michelin, Stellantis, sindicatos

---

## FASE 1 — Fundação e Correções (Semanas 1-3)
**Objetivo:** Corrigir gaps entre backend e frontend, estabilizar o sistema

### Semana 1 — Endpoints Faltantes + Perfil
- [ ] `GET /eleicoes/ativas/cooperado/{id}` (app já chama, backend não tem)
- [ ] `GET /cooperados/me` (perfil do cooperado logado)
- [ ] `PUT /cooperados/me/senha` (alterar senha própria)
- [ ] `GET /eleicoes/{id}/resultado` (resultado público pós-apuração)
- [ ] `POST /eleicoes/{id}/apurar` (apuração oficial)
- [ ] Tela de Perfil no app Flutter (alterar senha, ver dados)

### Semana 2 — Quórum e Presença ⚡ CONCORRENTE TEM
- [ ] Modelo `Presenca` (cooperado_id, eleicao_id, metodo: qrcode/manual/geo, horario)
- [ ] Endpoints de registro e consulta de presença
- [ ] Cálculo automático de quórum (simples, 2/3, absoluto) por eleição
- [ ] Bloqueio de votação se quórum não atingido
- [ ] Campos `quorum_minimo` e `tipo_quorum` na tabela eleicoes
- [ ] **Monitoramento de quórum em tempo real** — painel com % atingido e quem já votou ⚡
- [ ] **Painel "quem já votou"** — lista em tempo real para o admin acompanhar ⚡

### Semana 3 — Resultados e Histórico no App
- [ ] Tela de Resultados (gráficos de barras, percentuais, vencedor)
- [ ] Tela de Histórico de Votos (comprovantes anteriores do cooperado)
- [ ] Tela de Notificações (lista de avisos)
- [ ] Pull-to-refresh e estados vazios em todas as telas

---

## FASE 2 — Profissionalização (Semanas 4-8)
**Objetivo:** Recursos que fazem o sistema parecer profissional e pronto para venda

### Semana 4 — Notificações Push
- [ ] Integração Firebase Cloud Messaging (Flutter)
- [ ] Endpoint para envio de push (backend)
- [ ] Notificação de convocação para assembleia
- [ ] Lembrete de votação próxima do fim
- [ ] Notificação de resultado disponível

### Semana 5 — Relatórios e Exportação ⚡ CONCORRENTE TEM
- [ ] **Relatório Zerésima** — PDF automático no início da votação comprovando 0 votos registrados (exigência legal) ⚡
- [ ] **Minuta da Assembleia** — PDF com regramento, pautas e relação dos votantes habilitados ⚡
- [ ] **Relatório Final** — regramento + resultado da eleição + relação de eleitores com IP, data e hora ⚡
- [ ] **Relatório de Participantes** — PDF com lista de votantes, IP, data/hora (para registro cartorial) ⚡
- [ ] Relatório de participação por região/matrícula
- [ ] Exportação PDF de resultado com layout profissional
- [ ] Exportação Excel de cooperados e votos
- [ ] Certidão de resultado (PDF assinado)
- [ ] Endpoint `GET /eleicoes/{id}/relatorio`
- [ ] Endpoint `GET /eleicoes/{id}/zeresima`
- [ ] Endpoint `GET /eleicoes/{id}/minuta`

### Semana 6 — Ata Automática ⚡ CONCORRENTE TEM
- [ ] **Templates de ata por tipo de votação** — escolha o modelo mais adequado em 1 clique ⚡
- [ ] Template para: Assembleia Geral, Conselho, Câmara, Acordo Coletivo, Eleição
- [ ] Geração automática com dados das votações
- [ ] Campos: data, local, presidente, secretário, quórum, deliberações, resultados
- [ ] **Ata certificada** — gerada e auditada pela plataforma ⚡
- [ ] **Ata para registro cartorial** — formato aceito para registro em cartório ⚡
- [ ] Exportação PDF com carimbo de tempo
- [ ] Endpoint `POST /eleicoes/{id}/gerar-ata`
- [ ] Endpoint `GET /eleicoes/{id}/ata`

### Semana 7 — Pautas Avançadas ⚡ CONCORRENTE TEM
- [ ] Votação sequencial (pauta a pauta, abertura/fechamento individual)
- [ ] Anexos por pauta (upload de documentos)
- [ ] Discussão/comentários por pauta
- [ ] Pedido de vista, destaque, retirada de pauta
- [ ] Emendas com votação separada
- [ ] **Criação de pautas durante a assembleia** (ao vivo, sem precisar pré-cadastrar) ⚡

### Semana 8 — Novos Tipos de Votação e Link Direto ⚡ CONCORRENTE TEM
- [ ] **Tipo ACORDO_COLETIVO** — para sindicatos e acordos trabalhistas ⚡
- [ ] **Tipo NEGOCIACAO_COLETIVA** — para convenções coletivas ⚡
- [ ] Tipo REFERENDO — para consultas simples sim/não
- [ ] Parametrização total do tipo de votação (qualquer tipo customizável)
- [ ] **Link direto de votação** — cooperado recebe link único por email/SMS que autentica e leva direto à votação ⚡
- [ ] **Separação assembleia x votação** — assembleia virtual pode encerrar, mas votação continua por período configurável ⚡
- [ ] Campo `data_fim_votacao` separado de `data_fim_assembleia` na tabela eleicoes

---

## FASE 3 — Experiência Completa (Semanas 9-12)
**Objetivo:** Tornar o sistema completo para uso diário

### Semana 9 — Módulo de Documentos
- [ ] Repositório de documentos (estatuto, regimento, editais)
- [ ] Upload e categorização
- [ ] Aceite/ciência pelo cooperado
- [ ] Publicação de editais com comprovante de leitura
- [ ] Tela de Documentos no app

### Semana 10 — Gestão de Mandatos
- [ ] Modelo `Mandato` (cooperado_id, cargo, data_inicio, data_fim, eleicao_origem)
- [ ] Registro automático de eleitos
- [ ] Composição atual do conselho/diretoria
- [ ] Alerta de vencimento de mandato
- [ ] Histórico de mandatos

### Semana 11 — WebSocket e Tempo Real
- [ ] WebSocket para atualização ao vivo de votos
- [ ] Painel de acompanhamento em tempo real no app
- [ ] Indicador de presença online
- [ ] Contador ao vivo de participação

### Semana 12 — UX/Acessibilidade
- [ ] Onboarding para primeiro acesso
- [ ] Tutorial interativo de votação
- [ ] Acessibilidade (tamanho de fonte, alto contraste)
- [ ] Suporte offline (cache + sync)
- [ ] Internacionalização (pt-BR, en, es)

---

## FASE 4 — Enterprise e Compliance (Semanas 13-17)
**Objetivo:** Apto para grandes cooperativas e órgãos públicos

### Semana 13 — LGPD e Compliance ⚡ CONCORRENTE TEM
- [ ] **Conformidade LGPD** — mencionada como feature de venda ⚡
- [ ] Termo de consentimento para coleta de dados
- [ ] Anonimização de votos na exportação
- [ ] **Criptografia e anonimização dos dados das votações** (destaque comercial) ⚡
- [ ] Direito ao esquecimento (exclusão de dados)
- [ ] Log de consentimento
- [ ] Política de privacidade no app
- [ ] Aviso de privacidade na tela de login

### Semana 14 — Segurança Avançada
- [ ] Rate limiting (login, votação, OTP)
- [ ] Bloqueio de conta após tentativas excessivas
- [ ] Política de senhas (complexidade mínima)
- [ ] HSTS e headers de segurança
- [ ] Testes automatizados (pytest) para fluxos críticos

### Semana 15 — Certificação Digital ⚡ CONCORRENTE TEM
- [ ] **Relatórios gerados com certificado digital** ⚡
- [ ] Integração com certificados ICP-Brasil
- [ ] Assinatura digital de atas e resultados
- [ ] Carimbo de tempo (TSA)
- [ ] Validação de identidade via Gov.br

### Semana 16 — Multi-tenant
- [ ] Modelo `Organizacao` (nome, cnpj, logo, cores, plano)
- [ ] Isolamento de dados por organização
- [ ] Painel administrativo por organização
- [ ] Personalização visual por cliente
- [ ] Gestão de planos/assinaturas

### Semana 17 — Integrações Externas ⚡ CONCORRENTE TEM
- [ ] **Integração com sistemas de RH/Gestão de Pessoas** (ex: LG Gente&Gestão) ⚡
- [ ] API pública para integração com sistemas terceiros
- [ ] Webhooks para notificação de eventos (voto registrado, eleição encerrada, etc.)
- [ ] Importação de associados via API (além do CSV)
- [ ] SSO (Single Sign-On) para grandes organizações

---

## FASE 5 — Diferencial Competitivo (Semanas 18-23)
**Objetivo:** Funcionalidades que diferenciam dos concorrentes

### Semanas 18-19 — Assembleia ao Vivo com Vídeo ⚡ CONCORRENTE TEM
- [ ] **Integração com Zoom** — assembleia virtual com vídeo integrado ⚡
- [ ] Integração com Jitsi (alternativa open-source)
- [ ] Integração com YouTube Live (para transmissões públicas)
- [ ] **Chat ao vivo durante assembleia** ⚡
- [ ] **Gravação de vídeo e chat** — armazenamento e replay ⚡
- [ ] **Relatório de participantes da assembleia virtual** ⚡
- [ ] Controle de presença em tempo real via vídeo
- [ ] Painel de quórum ao vivo
- [ ] Cronômetro para tempo de fala
- [ ] **Em apenas 3 cliques participar da assembleia virtual** (UX simplificado) ⚡

### Semana 20 — Procuração/Delegação de Voto
- [ ] Modelo `Procuracao` (de, para, eleicao, documento, validade)
- [ ] Limite de procurações por pessoa
- [ ] Upload de documento de procuração
- [ ] Validação jurídica (prazo, assembleia específica)

### Semana 21 — Data Intelligence ⚡ CONCORRENTE TEM
- [ ] **Monitoramento de negociações/convenções coletivas** ⚡
- [ ] Dashboard analítico com indicadores de participação histórica
- [ ] Análise preditiva de quórum baseada em assembleias anteriores
- [ ] Comparativo de participação entre eleições
- [ ] Relatórios de tendência (evolução da participação ao longo do tempo)
- [ ] Exportação de dados para BI (Business Intelligence)

### Semana 22 — Infraestrutura
- [ ] **Hospedagem em cloud profissional** (Google Cloud, AWS) ⚡
- [ ] Cache Redis para sessões
- [ ] Fila de tarefas (Celery) para emails/SMS em massa
- [ ] API versionada (`/api/v1/`, `/api/v2/`)
- [ ] Monitoramento (health check, métricas)
- [ ] CI/CD pipeline

### Semana 23 — App Admin
- [ ] App ou painel web responsivo para administradores
- [ ] Dashboard com gráficos interativos
- [ ] Gestão completa pelo celular
- [ ] Relatórios visuais

---

## Resumo: O que o concorrente tem e precisamos implementar

| # | Feature do Concorrente | Fase | Semana |
|---|---|---|---|
| 1 | Monitoramento de quórum em tempo real | 1 | 2 |
| 2 | Painel "quem já votou" | 1 | 2 |
| 3 | Relatório Zerésima (0 votos no início) | 2 | 5 |
| 4 | Minuta da Assembleia | 2 | 5 |
| 5 | Relatório Final com IP/data/hora | 2 | 5 |
| 6 | Relatório de Participantes | 2 | 5 |
| 7 | Ata automática com templates | 2 | 6 |
| 8 | Ata para registro cartorial | 2 | 6 |
| 9 | Criação de pautas ao vivo | 2 | 7 |
| 10 | Tipo Acordo Coletivo | 2 | 8 |
| 11 | Link direto de votação | 2 | 8 |
| 12 | Separação assembleia x votação | 2 | 8 |
| 13 | LGPD / Criptografia e anonimização | 4 | 13 |
| 14 | Certificado digital nos relatórios | 4 | 15 |
| 15 | Integração com sistemas RH (LG) | 4 | 17 |
| 16 | Integração Zoom | 5 | 18-19 |
| 17 | Chat ao vivo | 5 | 18-19 |
| 18 | Gravação de vídeo e chat | 5 | 18-19 |
| 19 | Relatório de participantes da assembleia virtual | 5 | 18-19 |
| 20 | Data Intelligence / Monitoramento negociações | 5 | 21 |
| 21 | Hospedagem cloud profissional | 5 | 22 |

---

## Resumo por Fase

| Fase | Semanas | Foco | Impacto |
|------|---------|------|---------|
| **1** | 1-3 | Fundação e correções | Funcional básico |
| **2** | 4-8 | Profissionalização + features concorrente | Pronto para venda |
| **3** | 9-12 | Experiência completa | Uso diário |
| **4** | 13-17 | Enterprise/Compliance/Integrações | Grandes clientes |
| **5** | 18-23 | Diferencial competitivo + Assembleia ao vivo | Liderança de mercado |
