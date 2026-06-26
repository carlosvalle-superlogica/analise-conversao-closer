import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Closer — Aquisições",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.metric-card {
    background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
    border: 1px solid #2D2D4E;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    margin-bottom: 8px;
}
.metric-card .label { font-size: 12px; color: #8888AA; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.metric-card .value { font-size: 32px; font-weight: 700; color: #EAEAEA; }
.metric-card .sub   { font-size: 13px; color: #6C3FC5; margin-top: 4px; }

.section-title {
    font-size: 18px; font-weight: 600; color: #EAEAEA;
    border-left: 4px solid #6C3FC5;
    padding-left: 12px; margin: 24px 0 16px 0;
}

.badge-ok   { background:#1a3a2a; color:#4CAF50; border-radius:6px; padding:2px 8px; font-size:12px; }
.badge-warn { background:#3a2a1a; color:#FF9800; border-radius:6px; padding:2px 8px; font-size:12px; }
.badge-bad  { background:#3a1a1a; color:#F44336; border-radius:6px; padding:2px 8px; font-size:12px; }

div[data-testid="stSidebar"] { background:#0D0D1A; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────
USERS = {
    "aquisições": {"password": "2024", "role": "master"},
    "operador":   {"password": "vis@2025", "role": "operador"},
}

def login_screen():
    st.markdown("<h2 style='text-align:center;margin-top:80px;'>🏆 Dashboard Closer</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888;margin-bottom:40px;'>Pipeline [Comercial] Aquisições</p>", unsafe_allow_html=True)
    col = st.columns([1, 1.2, 1])[1]
    with col:
        user = st.text_input("Usuário")
        pwd  = st.text_input("Senha", type="password")
        if st.button("Entrar", width="stretch"):
            if user in USERS and USERS[user]["password"] == pwd:
                st.session_state["logged_in"] = True
                st.session_state["user"]      = user
                st.session_state["role"]      = USERS[user]["role"]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# ─────────────────────────────────────────────
# MAPEAMENTO DE COLUNAS (nomes reais do CSV)
# ─────────────────────────────────────────────
COL_ID            = "ID do registro."
COL_NOME          = "Nome do negócio"
COL_CLOSER        = "[IS/SDR] Closer Responsável"
COL_SDR           = "[IS/SDR] SDR Responsável"
COL_ETAPA         = "Etapa do negócio"
COL_CRIACAO       = "Data de criação"
COL_REUNIAO       = "[IS/Closer] Reunião Ocorrida "   # note trailing space
COL_FECHAMENTO    = 'Date entered "Fechado ([Comercial] Aquisições)"'  # mF — persiste mesmo se avançar para Pago
COL_PAGO          = 'Date entered "Pago ([Comercial] Aquisições)"'
COL_FECHAMENTO_FALLBACK = "Data de fechamento"  # fallback se coluna nova não vier no CSV
COL_PRODUTOS      = "[IS/Closer] Produtos Fechados"
COL_JORNADA       = "[IS] Lead com Jornada:"
COL_TIPO          = "[IS] Tipo de lead"
COL_ORIGEM        = "[IS] Origem do lead"
COL_CARTEIRA      = "[IS] Carteira de Imóveis (novo)"
COL_CONTRATOS     = "[IS] Contratos de Locação"
COL_MOTIVO_PERDA  = "Motivo de Fechamento Perdido"
COL_SUBMOTIVO     = "Motivo de Fechamento Perdido (Sub-motivo)"
COL_DESC_PERDA    = "Descrição de fechamento perdido"
COL_ERP           = "[IS/SDR] Qual ERP utiliza?"
COL_CRM_USO       = "[IS/SDR] Qual CRM utiliza?"

ETAPAS_FECHADO = ["Fechado", "Pago"]

# ─────────────────────────────────────────────
# CARGA DE DADOS
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando dados…")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)

    # Normaliza espaços nos nomes de colunas
    df.columns = df.columns.str.strip()

    # Remapeia nomes com trailing space
    rename = {}
    for c in df.columns:
        stripped = c.strip()
        if stripped != c:
            rename[c] = stripped
    if rename:
        df = df.rename(columns=rename)

    # Reatribui constantes após strip
    global COL_REUNIAO
    COL_REUNIAO = "[IS/Closer] Reunião Ocorrida"

    # Garante COL_FECHAMENTO: usa Date entered Fechado; se ausente, cai para Data de fechamento
    if COL_FECHAMENTO not in df.columns and COL_FECHAMENTO_FALLBACK in df.columns:
        df[COL_FECHAMENTO] = df[COL_FECHAMENTO_FALLBACK]

    date_cols = [COL_CRIACAO, COL_REUNIAO, COL_FECHAMENTO, COL_PAGO]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Colunas derivadas de mês
    if COL_CRIACAO in df.columns:
        df["mes_criacao"]    = df[COL_CRIACAO].dt.to_period("M")
        df["ano_criacao"]    = df[COL_CRIACAO].dt.year
        df["mes_criacao_dt"] = df[COL_CRIACAO].dt.strftime("%Y-%m")
    if COL_REUNIAO in df.columns:
        df["mes_reuniao"]    = df[COL_REUNIAO].dt.to_period("M")
        df["mes_reuniao_dt"] = df[COL_REUNIAO].dt.strftime("%Y-%m")
    if COL_FECHAMENTO in df.columns:
        df["mes_fechamento"]    = df[COL_FECHAMENTO].dt.to_period("M")
        df["mes_fechamento_dt"] = df[COL_FECHAMENTO].dt.strftime("%Y-%m")
    if COL_PAGO in df.columns:
        df["mes_pago_dt"] = df[COL_PAGO].dt.strftime("%Y-%m")

    # Flag fechado
    df["is_fechado"]  = df[COL_ETAPA].isin(ETAPAS_FECHADO)
    df["is_reuniao"]  = df[COL_REUNIAO].notna()
    df["is_perdido"]  = df[COL_ETAPA] == "Perdidos"

    return df


def get_df():
    if "df" not in st.session_state:
        st.warning("Faça upload do CSV para continuar.")
        st.stop()
    return st.session_state["df"]


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Dados")
    uploaded = st.file_uploader("Upload CSV (HubSpot)", type=["csv"])
    if uploaded:
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        st.session_state["df"] = load_data(tmp_path)
        st.success(f"✅ {len(st.session_state['df']):,} registros carregados")

    st.markdown("---")
    st.markdown("### 📌 Navegação")

    modulos = [
        "📊 Dashboard Geral",
        "🏆 Performance de Closers",
        "📦 Produtos Fechados",
        "🧩 Perfil do Lead",
        "📈 Comparação Mês a Mês",
        "❌ Perdidos (pós-reunião)",
    ]
    if st.session_state.get("role") == "operador":
        modulos = [m for m in modulos if m not in ["🏆 Performance de Closers"]]

    modulo = st.radio("Módulo", modulos, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"👤 **{st.session_state['user']}** · {st.session_state['role']}")
    if st.button("Sair"):
        for k in ["logged_in", "user", "role", "df"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─────────────────────────────────────────────
# FILTROS GLOBAIS
# ─────────────────────────────────────────────
def render_filtros(df: pd.DataFrame):
    with st.expander("🔍 Filtros Globais", expanded=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            tipo_data = st.selectbox(
                "Filtrar por data",
                ["Data de Criação", "Reunião Ocorrida", "Data de Fechamento"],
                key="tipo_data",
            )
            col_data_map = {
                "Data de Criação":     COL_CRIACAO,
                "Reunião Ocorrida":    COL_REUNIAO,
                "Data de Fechamento":  COL_FECHAMENTO,
            }
            col_data = col_data_map[tipo_data]

            datas_validas = df[col_data].dropna()
            if len(datas_validas) == 0:
                st.warning("Sem datas disponíveis para este filtro.")
                return df

            min_d = datas_validas.min().date()
            max_d = datas_validas.max().date()
            data_ini, data_fim = st.date_input(
                "Período",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
                key="periodo",
            )

        with c2:
            anos = sorted(df["ano_criacao"].dropna().unique().astype(int).tolist(), reverse=True)
            ano_sel = st.multiselect("Ano (criação)", anos, default=anos, key="ano_sel")

            closers = sorted(df[COL_CLOSER].dropna().unique().tolist())
            closer_sel = st.multiselect("Closer", closers, default=closers, key="closer_sel")

        with c3:
            jornadas = sorted(df[COL_JORNADA].dropna().unique().tolist())
            jornada_sel = st.multiselect("Jornada", jornadas, default=jornadas, key="jornada_sel")

            tipos = sorted(df[COL_TIPO].dropna().unique().tolist())
            tipo_sel = st.multiselect("Tipo de Lead", tipos, default=tipos, key="tipo_sel")

    # Aplica máscaras
    mask = pd.Series([True] * len(df), index=df.index)

    if col_data in df.columns:
        mask &= df[col_data].dt.date.between(data_ini, data_fim)
    if ano_sel:
        mask &= df["ano_criacao"].isin(ano_sel)
    if closer_sel:
        mask &= df[COL_CLOSER].isin(closer_sel)
    if jornada_sel:
        mask &= df[COL_JORNADA].isin(jornada_sel)
    if tipo_sel:
        mask &= df[COL_TIPO].isin(tipo_sel)

    return df[mask].copy()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
PURPLE = "#6C3FC5"
COLORS = ["#6C3FC5", "#A855F7", "#34D399", "#F59E0B", "#60A5FA", "#F87171", "#818CF8", "#FB923C"]

def pct(a, b):
    return f"{a/b*100:.1f}%" if b > 0 else "0%"

def metric_card(label, value, sub=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {"<div class='sub'>" + sub + "</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)

def secao(txt):
    st.markdown(f'<div class="section-title">{txt}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO 1: DASHBOARD GERAL
# ─────────────────────────────────────────────
def modulo_geral(df: pd.DataFrame):
    st.title("📊 Dashboard Geral")
    dff = render_filtros(df)

    total_leads   = len(dff)
    total_reuniao = dff["is_reuniao"].sum()
    total_fechado = dff["is_fechado"].sum()

    secao("Funil de Conversão")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("Total de Leads", f"{total_leads:,}")
    with c2: metric_card("Com Reunião", f"{total_reuniao:,}", pct(total_reuniao, total_leads))
    with c3: metric_card("Fechados", f"{total_fechado:,}", pct(total_fechado, total_leads))
    with c4: metric_card("Conv. Reunião→Fechado", pct(total_fechado, total_reuniao))
    with c5: metric_card("Perdidos", f"{dff['is_perdido'].sum():,}", pct(dff['is_perdido'].sum(), total_leads))

    # Funil visual
    secao("Funil Visual")
    fig_funil = go.Figure(go.Funnel(
        y=["Leads Totais", "Reunião Ocorrida", "Fechados"],
        x=[total_leads, total_reuniao, total_fechado],
        marker_color=[COLORS[0], COLORS[1], COLORS[2]],
        textinfo="value+percent initial",
    ))
    fig_funil.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=320, margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_funil, width="stretch")

    col_a, col_b = st.columns(2)

    with col_a:
        secao("Por Jornada")
        grp = dff.groupby(COL_JORNADA).agg(
            Leads=(COL_ID, "count"),
            Reunioes=("is_reuniao", "sum"),
            Fechados=("is_fechado", "sum"),
        ).reset_index()
        grp["Conv%"] = (grp["Fechados"] / grp["Leads"] * 100).round(1).astype(str) + "%"
        st.dataframe(grp.rename(columns={COL_JORNADA: "Jornada"}), hide_index=True, width="stretch")

    with col_b:
        secao("Por Tipo de Lead")
        grp2 = dff.groupby(COL_TIPO).agg(
            Leads=(COL_ID, "count"),
            Reunioes=("is_reuniao", "sum"),
            Fechados=("is_fechado", "sum"),
        ).reset_index()
        grp2["Conv%"] = (grp2["Fechados"] / grp2["Leads"] * 100).round(1).astype(str) + "%"
        grp2 = grp2.sort_values("Leads", ascending=False)
        st.dataframe(grp2.rename(columns={COL_TIPO: "Tipo"}), hide_index=True, width="stretch")

    secao("Top Origens (Leads)")
    orig = dff[COL_ORIGEM].value_counts().head(15).reset_index()
    orig.columns = ["Origem", "Leads"]
    fig_orig = px.bar(orig, x="Leads", y="Origem", orientation="h",
                      color_discrete_sequence=[PURPLE])
    fig_orig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=420, yaxis_title="", xaxis_title="Leads",
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_orig, width="stretch")

    secao("Performance por Closer (Funil)")
    perf = dff.groupby(COL_CLOSER).agg(
        Leads=(COL_ID, "count"),
        Reunioes=("is_reuniao", "sum"),
        Fechados=("is_fechado", "sum"),
    ).reset_index()
    perf["Conv L→F"] = (perf["Fechados"] / perf["Leads"] * 100).round(1).astype(str) + "%"
    perf["Conv R→F"] = (perf["Fechados"] / perf["Reunioes"].where(perf["Reunioes"] > 0) * 100).fillna(0).round(1).astype(str) + "%"
    perf = perf.sort_values("Fechados", ascending=False)
    st.dataframe(perf.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width="stretch")


# ─────────────────────────────────────────────
# MÓDULO 2: PERFORMANCE DE CLOSERS
# ─────────────────────────────────────────────
def modulo_closers(df: pd.DataFrame):
    st.title("🏆 Performance de Closers")
    dff = render_filtros(df)

    perf = dff.groupby(COL_CLOSER).agg(
        Leads=(COL_ID, "count"),
        Reunioes=("is_reuniao", "sum"),
        Fechados=("is_fechado", "sum"),
    ).reset_index()
    perf["_conv_rf"] = (perf["Fechados"] / perf["Reunioes"].where(perf["Reunioes"] > 0) * 100).fillna(0).round(1)
    perf["_conv_lf"] = (perf["Fechados"] / perf["Leads"] * 100).round(1)
    perf = perf.sort_values("_conv_rf", ascending=False).reset_index(drop=True)
    perf["Conv R→F (%)"] = perf["_conv_rf"].astype(str) + "%"
    perf["Conv L→F (%)"] = perf["_conv_lf"].astype(str) + "%"
    perf = perf.drop(columns=["_conv_rf", "_conv_lf"])

    secao("Ranking por Conversão Reunião → Fechado")

    # Top 5 / Bottom 5
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### 🥇 Top 5")
        top5 = perf.head(5)[[COL_CLOSER, "Reunioes", "Fechados", "Conv R→F (%)"]].copy()
        # já formatado com %
        st.dataframe(top5.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width="stretch")
    with col_b:
        st.markdown("##### ⚠️ Atenção (bottom 5 com ≥5 reuniões)")
        bot5 = perf[perf["Reunioes"] >= 5].tail(5)[[COL_CLOSER, "Reunioes", "Fechados", "Conv R→F (%)"]].copy()
        # já formatado com %
        st.dataframe(bot5.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width="stretch")

    secao("Reuniões vs Fechados por Closer")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Reuniões", x=perf[COL_CLOSER], y=perf["Reunioes"], marker_color=COLORS[1]))
    fig.add_trace(go.Bar(name="Fechados", x=perf[COL_CLOSER], y=perf["Fechados"], marker_color=COLORS[2]))
    fig.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=380, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig, width="stretch")

    secao("Evolução Mensal por Closer")
    if "mes_reuniao_dt" in dff.columns:
        evo = dff[dff["is_fechado"]].groupby([COL_CLOSER, "mes_fechamento_dt"]).size().reset_index(name="Fechados")
        fig2 = px.line(evo, x="mes_fechamento_dt", y="Fechados", color=COL_CLOSER,
                       color_discrete_sequence=COLORS, markers=True)
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=380, xaxis_title="Mês", yaxis_title="Fechados",
            margin=dict(l=0, r=0, t=10, b=0), legend_title="Closer",
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig2, width="stretch")

    secao("Tabela Completa")
    perf_disp = perf.copy()
    # já formatado com % acima
    st.dataframe(perf_disp.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width="stretch")


# ─────────────────────────────────────────────
# MÓDULO 3: PRODUTOS FECHADOS
# ─────────────────────────────────────────────
def modulo_produtos(df: pd.DataFrame):
    st.title("📦 Produtos Fechados")
    dff = render_filtros(df)

    fechados = dff[dff["is_fechado"] & dff[COL_PRODUTOS].notna()].copy()

    if fechados.empty:
        st.info("Sem dados de produtos fechados para o período selecionado.")
        return

    # Explode produtos (separados por ";")
    fechados["produto_list"] = fechados[COL_PRODUTOS].str.split(";")
    exploded = fechados.explode("produto_list")
    exploded["produto_list"] = exploded["produto_list"].str.strip()

    secao("Mix de Vendas — Volume por Produto")
    mix = exploded["produto_list"].value_counts().reset_index()
    mix.columns = ["Produto", "Qtd"]
    mix["% Total"] = (mix["Qtd"] / mix["Qtd"].sum() * 100).round(1).astype(str) + "%"

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        fig = px.bar(mix.head(15), x="Qtd", y="Produto", orientation="h",
                     color_discrete_sequence=[PURPLE], text="Qtd")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=420, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, width="stretch")
    with col_b:
        st.dataframe(mix, hide_index=True, width="stretch")

    secao("Produtos por Closer")
    por_closer = exploded.groupby([COL_CLOSER, "produto_list"]).size().reset_index(name="Qtd")
    por_closer = por_closer.sort_values([COL_CLOSER, "Qtd"], ascending=[True, False])

    closer_sel2 = st.selectbox("Selecione o Closer", sorted(por_closer[COL_CLOSER].unique()))
    df_c = por_closer[por_closer[COL_CLOSER] == closer_sel2]
    fig2 = px.pie(df_c, names="produto_list", values="Qtd",
                  color_discrete_sequence=COLORS, hole=0.4)
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA",
        height=380, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig2, width="stretch")

    secao("Produtos por Closer × Ano")
    if "ano_criacao" in fechados.columns:
        exploded2 = fechados.copy()
        exploded2["produto_list"] = exploded2[COL_PRODUTOS].str.split(";")
        exploded2 = exploded2.explode("produto_list")
        exploded2["produto_list"] = exploded2["produto_list"].str.strip()
        pivot = exploded2.groupby([COL_CLOSER, "ano_criacao", "produto_list"]).size().unstack(fill_value=0)
        st.dataframe(pivot, width="stretch")


# ─────────────────────────────────────────────
# MÓDULO 4: PERFIL DO LEAD
# ─────────────────────────────────────────────
def modulo_perfil(df: pd.DataFrame):
    st.title("🧩 Perfil do Lead")
    dff = render_filtros(df)

    def conv_table(col, label):
        grp = dff.groupby(col).agg(
            Leads=(COL_ID, "count"),
            Reunioes=("is_reuniao", "sum"),
            Fechados=("is_fechado", "sum"),
        ).reset_index()
        grp["Conv R→F (%)"] = (grp["Fechados"] / grp["Reunioes"].where(grp["Reunioes"] > 0) * 100).fillna(0).round(1).astype(str) + "%"
        grp["Conv L→F (%)"] = (grp["Fechados"] / grp["Leads"] * 100).round(1).astype(str) + "%"
        return grp.rename(columns={col: label})

    aba1, aba2, aba3, aba4 = st.tabs(["🏠 Carteira de Imóveis", "📄 Contratos", "🧭 Jornada", "🔖 Tipo de Lead"])

    with aba1:
        secao("Carteira de Imóveis × Conversão")
        tb = conv_table(COL_CARTEIRA, "Carteira de Imóveis")
        st.dataframe(tb, hide_index=True, width="stretch")

        fig = px.bar(tb, x="Carteira de Imóveis", y=["Reunioes", "Fechados"],
                     barmode="group", color_discrete_sequence=COLORS[:2])
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=360, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, width="stretch")

    with aba2:
        secao("Contratos de Locação × Conversão")
        tb2 = conv_table(COL_CONTRATOS, "Contratos de Locação")
        st.dataframe(tb2, hide_index=True, width="stretch")

        fig2 = px.bar(tb2, x="Contratos de Locação", y=["Reunioes", "Fechados"],
                      barmode="group", color_discrete_sequence=COLORS[:2])
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=360, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        fig2.update_xaxes(tickangle=30)
        st.plotly_chart(fig2, width="stretch")

    with aba3:
        secao("Lead com Jornada × Conversão")
        tb3 = conv_table(COL_JORNADA, "Jornada")
        st.dataframe(tb3, hide_index=True, width="stretch")

        fig3 = px.bar(tb3, x="Jornada", y=["Leads", "Reunioes", "Fechados"],
                      barmode="group", color_discrete_sequence=COLORS[:3])
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=360, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig3, width="stretch")

    with aba4:
        secao("Tipo de Lead × Conversão")
        tb4 = conv_table(COL_TIPO, "Tipo de Lead")
        st.dataframe(tb4, hide_index=True, width="stretch")

        fig4 = px.bar(tb4, x="Tipo de Lead", y=["Leads", "Reunioes", "Fechados"],
                      barmode="group", color_discrete_sequence=COLORS[:3])
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=360, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig4, width="stretch")


# ─────────────────────────────────────────────
# MÓDULO 5: COMPARAÇÃO MÊS A MÊS
# ─────────────────────────────────────────────
def render_aba_comparacao(dff, col_mes, dimensao_col, dimensao_label, titulo):
    """Reutilizável: gera visão mensal por qualquer dimensão."""
    if col_mes not in dff.columns:
        st.warning(f"Coluna de mês '{col_mes}' não disponível.")
        return

    grp = dff.groupby([col_mes, dimensao_col]).agg(
        Leads=(COL_ID, "count"),
        Reunioes=("is_reuniao", "sum"),
        Fechados=("is_fechado", "sum"),
    ).reset_index()
    grp = grp.sort_values(col_mes)

    # Pivot para tabela histórica
    pivot = grp.pivot_table(index=dimensao_col, columns=col_mes, values="Fechados", aggfunc="sum", fill_value=0)

    secao(titulo)
    fig = px.bar(grp, x=col_mes, y="Fechados", color=dimensao_col,
                 barmode="group", color_discrete_sequence=COLORS, text_auto=True)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=380, xaxis_title="Mês", yaxis_title="Fechados",
        margin=dict(l=0, r=0, t=10, b=0), legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("Tabela pivot — Fechados por mês")
    st.dataframe(pivot, width="stretch")


def modulo_comparacao(df: pd.DataFrame):
    st.title("📈 Comparação Mês a Mês")
    dff = render_filtros(df)

    col_mes_opcoes = {
        "Mês de Criação":     "mes_criacao_dt",
        "Mês da Reunião":     "mes_reuniao_dt",
        "Mês de Fechamento":  "mes_fechamento_dt",
    }
    tipo_mes = st.selectbox("Competência por", list(col_mes_opcoes.keys()))
    col_mes  = col_mes_opcoes[tipo_mes]

    aba_geral, aba_closer, aba_jornada, aba_tipo, aba_produto = st.tabs(
        ["Visão Geral", "Por Closer", "Por Jornada", "Por Tipo", "Por Produto"]
    )

    with aba_geral:
        secao("Leads, Reuniões e Fechados por Mês")
        grp = dff.groupby(col_mes).agg(
            Leads=(COL_ID, "count"),
            Reunioes=("is_reuniao", "sum"),
            Fechados=("is_fechado", "sum"),
        ).reset_index().sort_values(col_mes)
        grp["Conv%"] = (grp["Fechados"] / grp["Reunioes"].where(grp["Reunioes"] > 0) * 100).fillna(0).round(1).astype(str) + "%"

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Leads", x=grp[col_mes], y=grp["Leads"], marker_color=COLORS[0]))
        fig.add_trace(go.Bar(name="Reuniões", x=grp[col_mes], y=grp["Reunioes"], marker_color=COLORS[1]))
        fig.add_trace(go.Bar(name="Fechados", x=grp[col_mes], y=grp["Fechados"], marker_color=COLORS[2]))
        fig.update_layout(
            barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=380, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig, width="stretch")
        st.dataframe(grp.rename(columns={col_mes: "Mês"}), hide_index=True, width="stretch")

    with aba_closer:
        render_aba_comparacao(dff, col_mes, COL_CLOSER, "Closer", "Fechados por Mês × Closer")

    with aba_jornada:
        render_aba_comparacao(dff, col_mes, COL_JORNADA, "Jornada", "Fechados por Mês × Jornada")

    with aba_tipo:
        render_aba_comparacao(dff, col_mes, COL_TIPO, "Tipo de Lead", "Fechados por Mês × Tipo de Lead")

    with aba_produto:
        # Produtos precisam de explode
        fechados = dff[dff["is_fechado"] & dff[COL_PRODUTOS].notna()].copy()
        if not fechados.empty:
            fechados["produto_list"] = fechados[COL_PRODUTOS].str.split(";")
            exp = fechados.explode("produto_list")
            exp["produto_list"] = exp["produto_list"].str.strip()
            render_aba_comparacao(exp, col_mes, "produto_list", "Produto", "Fechados por Mês × Produto")
        else:
            st.info("Sem fechados com produto no período.")


# ─────────────────────────────────────────────
# MÓDULO 6: PERDIDOS PÓS-REUNIÃO
# ─────────────────────────────────────────────
def modulo_perdidos(df: pd.DataFrame):
    st.title("❌ Perdidos (pós-reunião)")
    dff = render_filtros(df)

    perdidos = dff[dff["is_perdido"] & dff["is_reuniao"]].copy()

    if perdidos.empty:
        st.info("Sem perdidos com reunião ocorrida no período selecionado.")
        return

    total_p = len(perdidos)
    secao(f"Total de perdidos após reunião: {total_p:,}")

    col_a, col_b = st.columns(2)

    with col_a:
        secao("Motivos de Perda")
        motivos = perdidos[COL_MOTIVO_PERDA].value_counts().reset_index()
        motivos.columns = ["Motivo", "Qtd"]
        motivos["% Total"] = (motivos["Qtd"] / total_p * 100).round(1).astype(str) + "%"
        fig = px.bar(motivos, x="Qtd", y="Motivo", orientation="h",
                     color_discrete_sequence=[COLORS[3]], text="Qtd")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=400, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, width="stretch")
        st.dataframe(motivos, hide_index=True, width="stretch")

    with col_b:
        secao("Perdidos por Closer")
        por_closer = perdidos[COL_CLOSER].value_counts().reset_index()
        por_closer.columns = ["Closer", "Perdidos"]
        fig2 = px.bar(por_closer, x="Perdidos", y="Closer", orientation="h",
                      color_discrete_sequence=[COLORS[5]], text="Perdidos")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=400, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig2, width="stretch")

    secao("Origem × Motivo de Perda")
    cross = perdidos.groupby([COL_ORIGEM, COL_MOTIVO_PERDA]).size().reset_index(name="Qtd")
    cross = cross.sort_values("Qtd", ascending=False).head(30)
    fig3 = px.bar(cross, x="Qtd", y=COL_ORIGEM, color=COL_MOTIVO_PERDA,
                  orientation="h", color_discrete_sequence=COLORS, barmode="stack")
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=460, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig3, width="stretch")

    secao("Auditoria Individual")
    closer_audit = st.selectbox("Filtrar Closer", ["Todos"] + sorted(perdidos[COL_CLOSER].dropna().unique().tolist()))
    df_audit = perdidos if closer_audit == "Todos" else perdidos[perdidos[COL_CLOSER] == closer_audit]
    cols_show = [COL_NOME, COL_CLOSER, COL_REUNIAO, COL_MOTIVO_PERDA, COL_SUBMOTIVO, COL_DESC_PERDA, COL_ORIGEM]
    cols_show = [c for c in cols_show if c in df_audit.columns]
    st.dataframe(df_audit[cols_show].reset_index(drop=True), hide_index=True, width="stretch")


# ─────────────────────────────────────────────
# ROTEAMENTO
# ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.info("👈 Faça upload do CSV do HubSpot na sidebar para começar.")
    st.stop()

df = st.session_state["df"]

if   modulo == "📊 Dashboard Geral":           modulo_geral(df)
elif modulo == "🏆 Performance de Closers":    modulo_closers(df)
elif modulo == "📦 Produtos Fechados":          modulo_produtos(df)
elif modulo == "🧩 Perfil do Lead":             modulo_perfil(df)
elif modulo == "📈 Comparação Mês a Mês":       modulo_comparacao(df)
elif modulo == "❌ Perdidos (pós-reunião)":     modulo_perdidos(df)
