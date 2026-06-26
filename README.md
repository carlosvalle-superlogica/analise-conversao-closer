# 🏆 Dashboard Closer — Aquisições

Dashboard de BI comercial para o time de Closers do pipeline **[Comercial] Aquisições** no HubSpot.

## Stack

- Python + Streamlit
- Pandas + Plotly
- Deploy via Streamlit Cloud

## Módulos

| Módulo | Descrição |
|--------|-----------|
| 📊 Dashboard Geral | Funil completo, KPIs, tabelas por Jornada, Tipo e Origem |
| 🏆 Performance de Closers | Ranking, Top/Bottom 5, evolução mensal |
| 📦 Produtos Fechados | Mix de vendas, produtos por closer, pivot por ano |
| 🧩 Perfil do Lead | Carteira, Contratos, Jornada, Tipo de Lead |
| 📈 Comparação Mês a Mês | Visão contábil por competência, abas por dimensão |
| ❌ Perdidos pós-reunião | Motivos, análise por closer, cruzamento Origem × Motivo |

## Como usar

### Local
```bash
pip install -r requirements.txt
streamlit run closer_dashboard.py
```

### Streamlit Cloud
1. Fork este repositório
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório e selecione `closer_dashboard.py`

## Fonte de Dados

Exportação CSV manual do HubSpot — pipeline [Comercial] Aquisições.

### Colunas esperadas no CSV

| Campo | Coluna HubSpot |
|-------|---------------|
| ID | `ID do registro.` |
| Closer | `[IS/SDR] Closer Responsável` |
| SDR | `[IS/SDR] SDR Responsável` |
| Etapa | `Etapa do negócio` |
| Data de criação | `Data de criação` |
| Reunião Ocorrida | `[IS/Closer] Reunião Ocorrida` |
| Data de fechamento | `Data de fechamento` |
| Produtos Fechados | `[IS/Closer] Produtos Fechados` |
| Jornada | `[IS] Lead com Jornada:` |
| Tipo de Lead | `[IS] Tipo de lead` |
| Origem | `[IS] Origem do lead` |
| Carteira de Imóveis | `[IS] Carteira de Imóveis (novo)` |
| Contratos de Locação | `[IS] Contratos de Locação` |
| Motivo de Perda | `Motivo de Fechamento Perdido` |

## Lógica de Datas (competência)

- **mL** = Data de criação → quando o lead entrou
- **mR** = Reunião Ocorrida → quando a reunião aconteceu  
- **mF** = Data de fechamento → quando entrou em "Fechado"

## Acesso

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | closer@2025 | Master (acesso total) |
| operador | vis@2025 | Operador (visualização) |

> ⚠️ Altere as senhas antes do deploy em produção.
