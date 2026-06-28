# v2.0 - Python 3.14 + Pandas 3.0 compatible
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container {
    padding-top: 1.5rem !important; padding-bottom: 50rem !important;
    padding-left: 2rem !important; padding-right: 2rem !important;
    max-width: 1400px !important;
}
[data-testid="stWidgetLabel"] p { font-size: 11px !important; }
span[data-baseweb="tag"] { font-size: 10px !important; padding: 2px 5px !important; }
div[data-baseweb="menu"] li { font-size: 11px !important; }
.filter-block-title {
    font-size: 10px; font-weight: 700; color: #5BC0DE;
    text-transform: uppercase; letter-spacing: 1px; margin: 2px 0 6px 0;
}
.metric-card {
    background: linear-gradient(135deg, #0A1628 0%, #0D1F3C 100%);
    border: 1px solid #1A3A5C; border-radius: 12px;
    padding: 18px 20px; text-align: center; margin-bottom: 12px;
}
.metric-card .label { font-size: 10px; color: #6A8FAF; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.metric-card .value { font-size: 26px; font-weight: 700; color: #E8F4FD; }
.metric-card .sub   { font-size: 11px; color: #3B9ECC; margin-top: 4px; }
.section-title {
    font-size: 15px; font-weight: 600; color: #E8F4FD;
    border-left: 4px solid #2196F3; padding-left: 10px; margin: 28px 0 12px 0;
}
div[data-testid="stSidebar"] { background: #060E1C; }
[data-testid="stMultiSelect"] span[data-baseweb="tag"] { background-color: #1565C0 !important; color: #E8F4FD !important; }
hr { border-color: #1A3A5C !important; margin: 8px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────
USERS = {
    "aquisições": {"password": "2024",     "role": "master"},
    "operador":   {"password": "vis@2025", "role": "operador"},
}

def login_screen():
    st.markdown("<h2 style='text-align:center;margin-top:80px;'>🏆 Dashboard Closer</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888;margin-bottom:40px;'>Pipeline [Comercial] Aquisições</p>", unsafe_allow_html=True)
    col = st.columns([1, 1.2, 1])[1]
    with col:
        user = st.text_input("Usuário")
        pwd  = st.text_input("Senha", type="password")
        if st.button("Entrar", width='stretch'):
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
# MAPEAMENTO DE COLUNAS
# ─────────────────────────────────────────────
COL_ID           = "ID do registro."
COL_NOME         = "Nome do negócio"
COL_CLOSER       = "[IS/SDR] Closer Responsável"
COL_SDR          = "[IS/SDR] SDR Responsável"
COL_ETAPA        = "Etapa do negócio"
COL_CRIACAO      = "Data de criação"
COL_REUNIAO      = "[IS/Closer] Reunião Ocorrida"
COL_FECHAMENTO   = 'Date entered "Fechado ([Comercial] Aquisições)"'
COL_PAGO         = 'Date entered "Pago ([Comercial] Aquisições)"'
COL_DATA_FECH    = "Data de fechamento"   # coluna nativa (backup)
COL_PRODUTOS     = "[IS/Closer] Produtos Fechados"
COL_VALOR        = "Valor"
COL_INTERESSE    = "[IS/SDR] Produtos de Interesse do Lead"
COL_JORNADA      = "[IS] Lead com Jornada:"
COL_TIPO         = "[IS] Tipo de lead"
COL_ORIGEM       = "[IS] Origem do lead"
COL_CARTEIRA     = "[IS] Carteira de Imóveis (novo)"
COL_CONTRATOS    = "[IS] Contratos de Locação"
COL_MOTIVO_PERDA = "Motivo de Fechamento Perdido"
COL_SUBMOTIVO    = "Motivo de Fechamento Perdido (Sub-motivo)"
COL_DESC_PERDA   = "Descrição de fechamento perdido"
COL_ERP          = "[IS/SDR] Qual ERP utiliza?"
COL_CRM_USO      = "[IS/SDR] Qual CRM utiliza?"
COL_TAG          = "TAG - Comercial B2B"

ETAPAS_FECHADO = ["Fechado", "Pago"]


# ─────────────────────────────────────────────
# CARGA DE DADOS
# ─────────────────────────────────────────────
# Colunas necessárias — descarta o restante na leitura para economizar RAM
_COLS_USADAS = {
    COL_ID, COL_NOME, COL_CLOSER, COL_SDR, COL_ETAPA,
    COL_CRIACAO, COL_REUNIAO, COL_FECHAMENTO, COL_PAGO, COL_DATA_FECH,
    COL_PRODUTOS, COL_JORNADA, COL_TIPO, COL_ORIGEM,
    COL_CARTEIRA, COL_CONTRATOS,
    COL_MOTIVO_PERDA, COL_SUBMOTIVO, COL_DESC_PERDA,
    COL_ERP, COL_CRM_USO, COL_INTERESSE, COL_TAG, COL_VALOR,
}

@st.cache_data(show_spinner="Carregando dados…", max_entries=1)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        low_memory=False,
        usecols=lambda c: c.strip() in _COLS_USADAS,
    )
    df.columns = df.columns.str.strip()

    # Converter colunas de texto repetitivo para category (economiza RAM)
    cat_cols = [
        COL_CLOSER, COL_SDR, COL_ETAPA, COL_JORNADA, COL_TIPO,
        COL_ORIGEM, COL_CARTEIRA, COL_CONTRATOS, COL_MOTIVO_PERDA,
        COL_SUBMOTIVO, COL_ERP, COL_CRM_USO, COL_TAG,
    ]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    date_cols = [COL_CRIACAO, COL_REUNIAO, COL_FECHAMENTO, COL_PAGO, COL_DATA_FECH]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Flags base
    # is_fechado: qualquer registro com Date entered "Fechado" preenchida (4.972)
    # Igual ao filtro do HubSpot — independente da etapa atual
    df["is_fechado"] = df[COL_FECHAMENTO].notna()
    # is_pago: apenas etapa Pago com Date entered "Pago" (para Receita)
    df["is_pago"]    = (df[COL_ETAPA] == "Pago") & df[COL_PAGO].notna()
    df["is_reuniao"] = df[COL_REUNIAO].notna()
    df["is_perdido"] = (df[COL_ETAPA] == "Perdidos") & df["is_reuniao"]

    if COL_CRIACAO in df.columns:
        df["ano_criacao"]    = df[COL_CRIACAO].dt.year.astype("Int16")
        df["mes_criacao_dt"] = df[COL_CRIACAO].dt.strftime("%Y-%m")
    if COL_REUNIAO in df.columns:
        df["mes_reuniao_dt"] = df[COL_REUNIAO].dt.strftime("%Y-%m")
    if COL_FECHAMENTO in df.columns:
        df["mes_fechamento_dt"] = df[COL_FECHAMENTO].dt.strftime("%Y-%m")

    return df


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Dados")
    uploaded = st.file_uploader("Upload CSV (HubSpot)", type=["csv"])
    if uploaded:
        import tempfile
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
        "💰 Receita",
        "📦 Produtos Fechados",
        "🧩 Perfil do Lead",
        "📈 Comparação Mês a Mês",
        "❌ Perdidos (pós-reunião)",
        "🚨 Alerta Pós-Fechamento",
        "🔄 Kenlo vs Não-Kenlo",
    ]
    if st.session_state.get("role") == "operador":
        modulos = [m for m in modulos if m != "🏆 Performance de Closers"]

    modulo = st.radio("Módulo", modulos, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"👤 **{st.session_state['user']}** · {st.session_state['role']}")
    if st.button("Sair"):
        for k in ["logged_in", "user", "role", "df"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# FILTROS GLOBAIS
# Retorna 4 datasets independentes por data.
# ─────────────────────────────────────────────
def render_filtros(df: pd.DataFrame):
    with st.expander("Filtros Globais", expanded=False):

        def date_range(col, label, key):
            datas = df[col].dropna()
            if len(datas) == 0:
                return None, None
            mn, mx = datas.min().date(), datas.max().date()
            v = st.date_input(label, value=(mn, mx), min_value=mn, max_value=mx, key=key)
            if isinstance(v, (list, tuple)) and len(v) == 2:
                return (v[0], v[1])
            elif hasattr(v, '__class__') and 'date' in type(v).__name__.lower():
                return (v, v)
            else:
                return (mn, mx)

        def explode_vals(col):
            return sorted(set(
                v.strip()
                for val in df[col].dropna()
                for v in str(val).split(";") if v.strip()
            ))

        # Bloco 1: Datas
        st.markdown("<div class='filter-block-title'>Periodo</div>", unsafe_allow_html=True)
        dc1, dc2 = st.columns(2)
        with dc1:
            st.caption("Reuniao Ocorrida")
            r_R = date_range(COL_REUNIAO, "Periodo de Reuniao", "periodo_reuniao")
        with dc2:
            st.caption("Data de Fechamento")
            r_F = date_range(COL_FECHAMENTO, "Periodo de Fechamento", "periodo_fechamento")

        st.markdown("---")

        # Bloco 2: Equipe
        st.markdown("<div class='filter-block-title'>Equipe</div>", unsafe_allow_html=True)
        ec1, ec2 = st.columns(2)
        with ec1:
            closers = sorted(df[COL_CLOSER].dropna().unique().tolist())
            closer_sel = st.multiselect("Closer", closers, default=closers, key="closer_sel")
        with ec2:
            sdrs = sorted(df[COL_SDR].dropna().unique().tolist())
            sdr_sel = st.multiselect("SDR Responsavel", sdrs, default=sdrs, key="sdr_sel")

        st.markdown("---")

        # Bloco 3: Lead
        st.markdown("<div class='filter-block-title'>Lead</div>", unsafe_allow_html=True)
        lc1, lc2, lc3 = st.columns(3)
        with lc1:
            origens = sorted(df[COL_ORIGEM].dropna().unique().tolist())
            origem_sel = st.multiselect("Origem do Lead", origens, default=origens, key="origem_sel")
            tipos = sorted(df[COL_TIPO].dropna().unique().tolist())
            tipo_sel = st.multiselect("Tipo de Lead", tipos, default=tipos, key="tipo_sel")
        with lc2:
            jornadas = sorted(df[COL_JORNADA].dropna().unique().tolist())
            jornada_sel = st.multiselect("Jornada", jornadas, default=jornadas, key="jornada_sel")
            etapa_sel = st.selectbox("Etapa", ["Todas", "Fechado", "Pago"], key="etapa_sel")
        with lc3:
            interesse_todos = explode_vals(COL_INTERESSE) if COL_INTERESSE in df.columns else []
            interesse_sel = st.multiselect("Produto de Interesse", interesse_todos, default=[],
                                           key="interesse_sel", placeholder="Todos (sem filtro)")
            produtos_todos = sorted(set(
                p.strip()
                for val in df[COL_PRODUTOS].dropna()
                for p in str(val).split(";") if p.strip()
            ))
            produto_sel = st.multiselect("Produto Fechado", produtos_todos, default=[],
                                         key="produto_sel", placeholder="Todos (sem filtro)")

        st.markdown("---")

        # Bloco 4: Tecnologia
        st.markdown("<div class='filter-block-title'>Tecnologia</div>", unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            erp_sel = st.multiselect("ERP que utiliza",
                                     explode_vals(COL_ERP) if COL_ERP in df.columns else [],
                                     default=[], key="erp_sel", placeholder="Todos (sem filtro)")
        with tc2:
            crm_sel = st.multiselect("CRM que utiliza",
                                     explode_vals(COL_CRM_USO) if COL_CRM_USO in df.columns else [],
                                     default=[], key="crm_sel", placeholder="Todos (sem filtro)")
        with tc3:
            tag_todos = sorted(df[COL_TAG].dropna().unique().tolist()) if COL_TAG in df.columns else []
            tag_sel = st.multiselect("TAG Comercial", tag_todos,
                                     default=[], key="tag_sel", placeholder="Todos (sem filtro)")

    # Conjuntos completos de cada dimensão (para detectar filtro real vs "todos selecionados")
    _all_closers = set(df[COL_CLOSER].dropna().unique().tolist())
    _all_sdrs    = set(df[COL_SDR].dropna().unique().tolist())
    _all_origens = set(df[COL_ORIGEM].dropna().unique().tolist())
    _all_jornadas= set(df[COL_JORNADA].dropna().unique().tolist())
    _all_tipos   = set(df[COL_TIPO].dropna().unique().tolist())

    def mask_dim(d):
        m = pd.Series([True] * len(d), index=d.index)
        if etapa_sel != "Todas":
            m &= d[COL_ETAPA] == etapa_sel
        # Só filtra se o usuário REMOVEU algum valor (não é seleção completa)
        if closer_sel and set(closer_sel) != _all_closers:
            m &= d[COL_CLOSER].isin(closer_sel)
        if sdr_sel and set(sdr_sel) != _all_sdrs:
            m &= d[COL_SDR].isin(sdr_sel)
        if origem_sel and set(origem_sel) != _all_origens:
            m &= d[COL_ORIGEM].astype(object).fillna("").apply(
                lambda x: any(p in [s.strip() for s in x.split(";")] for p in origem_sel)
            )
        if jornada_sel and set(jornada_sel) != _all_jornadas:
            m &= d[COL_JORNADA].astype(object).fillna("").apply(
                lambda x: any(p in [s.strip() for s in x.split(";")] for p in jornada_sel)
            )
        if tipo_sel and set(tipo_sel) != _all_tipos:
            m &= d[COL_TIPO].isin(tipo_sel)
        if produto_sel:
            m &= d[COL_PRODUTOS].astype(object).fillna("").apply(
                lambda x: any(p in [s.strip() for s in x.split(";")] for p in produto_sel)
            )
        if interesse_sel and COL_INTERESSE in d.columns:
            m &= d[COL_INTERESSE].astype(object).fillna("").apply(
                lambda x: any(p in [s.strip() for s in x.split(";")] for p in interesse_sel)
            )
        if erp_sel and COL_ERP in d.columns:
            m &= d[COL_ERP].astype(object).fillna("").apply(
                lambda x: any(p in [s.strip() for s in x.split(";")] for p in erp_sel)
            )
        if crm_sel and COL_CRM_USO in d.columns:
            m &= d[COL_CRM_USO].astype(object).fillna("").apply(
                lambda x: any(p in [s.strip() for s in x.split(";")] for p in crm_sel)
            )
        if tag_sel and COL_TAG in d.columns:
            m &= d[COL_TAG].isin(tag_sel)
        return m

    df_leads = df[mask_dim(df)].copy()

    m_reun = df["is_reuniao"].copy()
    if r_R[0] and r_R[1]:
        m_reun &= df[COL_REUNIAO].dt.date.between(r_R[0], r_R[1])
    df_reunioes = df[m_reun & mask_dim(df)].copy()

    m_fech = df["is_fechado"].copy()
    if r_F[0] and r_F[1]:
        m_fech &= df[COL_FECHAMENTO].dt.date.between(r_F[0], r_F[1])
    if etapa_sel == "Fechado":
        m_fech &= df[COL_ETAPA] == "Fechado"
    elif etapa_sel == "Pago":
        m_fech &= df[COL_ETAPA] == "Pago"
    df_fechados = df[m_fech & mask_dim(df)].copy()

    m_perd = df["is_perdido"]  # is_perdido ja inclui filtro de reuniao ocorrida
    if r_R[0] and r_R[1]:
        m_perd &= df[COL_REUNIAO].dt.date.between(r_R[0], r_R[1])
    df_perdidos = df[m_perd & mask_dim(df)].copy()

    return df_leads, df_reunioes, df_fechados, df_perdidos

# HELPERS
# ─────────────────────────────────────────────
PURPLE = "#2196F3"
COLORS = ["#2196F3", "#42A5F5", "#00BCD4", "#26C6DA", "#0288D1", "#EF5350", "#66BB6A", "#FFA726"]

def pct(a, b):
    try:
        return f"{float(a)/float(b)*100:.1f}%" if float(b) > 0 else "0%"
    except Exception:
        return "0%"

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
    _, df_reunioes, df_fechados, df_perdidos = render_filtros(df)

    n_reunioes = len(df_reunioes)
    n_fechados = len(df_fechados)
    n_perdidos = len(df_perdidos)

    secao("Funil de Conversão")
    st.caption("Reuniões = período de reunião · Fechados = período de fechamento")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Reuniões Ocorridas",    f"{n_reunioes:,}")
    with c2: metric_card("Fechados",               f"{n_fechados:,}", pct(n_fechados, n_reunioes))
    with c3: metric_card("Conv. Reunião→Fechado",  pct(n_fechados, n_reunioes))
    with c4: metric_card("Perdidos (pós-reunião)", f"{n_perdidos:,}", pct(n_perdidos, n_reunioes))

    secao("Funil Visual")
    fig_funil = go.Figure(go.Funnel(
        y=["Reuniões", "Fechados"],
        x=[n_reunioes, n_fechados],
        marker_color=[COLORS[1], COLORS[2]],
        textinfo="value+percent initial",
    ))
    fig_funil.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=260, margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_funil, width='stretch')

    col_a, col_b = st.columns(2)

    def reun_fech_conv(dim_col, dim_label):
        """Tabela: Dimensão | Reuniões | Fechados | Conv R→F%"""
        r = df_reunioes.groupby(dim_col, observed=True).size().reset_index(name="Reuniões")
        f = df_fechados.groupby(dim_col, observed=True).size().reset_index(name="Fechados")
        tb = r.merge(f, on=dim_col, how="outer").fillna(0)
        tb["Reuniões"] = tb["Reuniões"].astype(int)
        tb["Fechados"] = tb["Fechados"].astype(int)
        tb["Conv R→F"] = pd.to_numeric(
            tb["Fechados"] / tb["Reuniões"].replace(0, float("nan")) * 100,
            errors="coerce").fillna(0).round(1).astype(str) + "%"
        return tb.sort_values("Fechados", ascending=False).rename(columns={dim_col: dim_label})

    with col_a:
        secao("Por Jornada")
        st.dataframe(reun_fech_conv(COL_JORNADA, "Jornada"), hide_index=True, width='stretch', height=800)

    with col_b:
        secao("Por Tipo de Lead")
        st.dataframe(reun_fech_conv(COL_TIPO, "Tipo"), hide_index=True, width='stretch', height=800)

    secao("Performance por Closer")
    perf_reun = df_reunioes.groupby(COL_CLOSER, observed=True).size().reset_index(name="Reuniões")
    perf_fech = df_fechados.groupby(COL_CLOSER, observed=True).size().reset_index(name="Fechados")
    perf = perf_reun.merge(perf_fech, on=COL_CLOSER, how="outer").fillna(0)
    perf["Reuniões"] = perf["Reuniões"].astype(int)
    perf["Fechados"] = perf["Fechados"].astype(int)
    perf["Conv R→F"] = pd.to_numeric(perf["Fechados"] / perf["Reuniões"].replace(0, float("nan")) * 100, errors="coerce").fillna(0).round(1).astype(str) + "%"
    perf = perf.sort_values("Fechados", ascending=False)
    st.dataframe(perf.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width='stretch', height=min(len(perf)*38+50, 900))


# ─────────────────────────────────────────────
# MÓDULO 2: PERFORMANCE DE CLOSERS
# ─────────────────────────────────────────────
def modulo_closers(df: pd.DataFrame):
    st.title("🏆 Performance de Closers")
    _, df_reunioes, df_fechados, _ = render_filtros(df)

    perf_reun = df_reunioes.groupby(COL_CLOSER, observed=True).size().reset_index(name="Reuniões")
    perf_fech = df_fechados.groupby(COL_CLOSER, observed=True).size().reset_index(name="Fechados")
    perf = perf_reun.merge(perf_fech, on=COL_CLOSER, how="outer").fillna(0)
    perf["Reuniões"] = perf["Reuniões"].astype(int)
    perf["Fechados"] = perf["Fechados"].astype(int)
    perf["_conv_rf"] = pd.to_numeric(perf["Fechados"] / perf["Reuniões"].replace(0, float("nan")) * 100, errors="coerce").fillna(0).round(1)
    perf = perf.sort_values("Fechados", ascending=False).reset_index(drop=True)
    perf["Conv R→F"] = perf["_conv_rf"].astype(str) + "%"
    perf = perf.drop(columns=["_conv_rf"])

    secao("Ranking por Fechados")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### 🥇 Top 5 em Fechados")
        top5 = perf.head(5)[[COL_CLOSER, "Reuniões", "Fechados", "Conv R→F"]].copy()
        st.dataframe(top5.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width='stretch', height=min(len(top5)*38+50, 300))
    with col_b:
        st.markdown("##### ⚠️ Atenção (menor conv. c/ ≥5 reuniões)")
        bot5 = perf[perf["Reuniões"] >= 5].sort_values("Conv R→F").head(5)[[COL_CLOSER, "Reuniões", "Fechados", "Conv R→F"]].copy()
        st.dataframe(bot5.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width='stretch', height=min(len(bot5)*38+50, 300))

    secao("Reuniões vs Fechados por Closer")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Reuniões", x=perf[COL_CLOSER], y=perf["Reuniões"], marker_color=COLORS[1]))
    fig.add_trace(go.Bar(name="Fechados", x=perf[COL_CLOSER], y=perf["Fechados"], marker_color=COLORS[2]))
    fig.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=380, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig, width='stretch')

    secao("Evolução Mensal de Fechados por Closer")
    if "mes_fechamento_dt" in df_fechados.columns:
        evo = df_fechados.groupby([COL_CLOSER, "mes_fechamento_dt"], observed=True).size().reset_index(name="Fechados")
        fig2 = px.line(evo, x="mes_fechamento_dt", y="Fechados", color=COL_CLOSER,
                       color_discrete_sequence=COLORS, markers=True)
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=380, xaxis_title="Mês de Fechamento",
            margin=dict(l=0, r=0, t=10, b=0), legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig2, width='stretch')

    secao("Tabela Completa")
    st.dataframe(perf.rename(columns={COL_CLOSER: "Closer"}), hide_index=True, width='stretch', height=min(len(perf)*38+50, 900))

    # ── Eficiência SDR × Closer ─────────────────────────────────────────────
    secao("Eficiência por Pessoa")
    st.caption("Reuniões = período de reunião · Fechados = período de fechamento")

    def efic_table(col, label):
        r = df_reunioes.groupby(col, observed=True).size().reset_index(name="Reuniões")
        f = df_fechados.groupby(col, observed=True).size().reset_index(name="Fechados")
        tb = r.merge(f, on=col, how="outer").fillna(0)
        tb["Reuniões"] = tb["Reuniões"].astype(int)
        tb["Fechados"] = tb["Fechados"].astype(int)
        tb["Conv R→F"] = pd.to_numeric(
            tb["Fechados"] / tb["Reuniões"].replace(0, float("nan")) * 100,
            errors="coerce").fillna(0).round(1).astype(str) + "%"
        return tb.sort_values("Reuniões", ascending=False).rename(columns={col: label})

    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown("##### 🎯 Eficiência SDR")
        tb_sdr = efic_table(COL_SDR, "SDR Responsável")
        st.dataframe(tb_sdr, hide_index=True, width='stretch',
                     height=min(len(tb_sdr) * 38 + 50, 800))
    with ec2:
        st.markdown("##### 🏆 Eficiência Closer")
        tb_closer = efic_table(COL_CLOSER, "Closer Responsável")
        st.dataframe(tb_closer, hide_index=True, width='stretch',
                     height=min(len(tb_closer) * 38 + 50, 800))


# ─────────────────────────────────────────────
# MÓDULO 3: PRODUTOS FECHADOS
# ─────────────────────────────────────────────
def modulo_produtos(df: pd.DataFrame):
    st.title("📦 Produtos Fechados")
    _, _, df_fechados, _ = render_filtros(df)

    fechados = df_fechados[df_fechados[COL_PRODUTOS].notna()].copy()

    if fechados.empty:
        st.info("Sem dados de produtos fechados para o período selecionado.")
        return

    fechados["produto_list"] = fechados[COL_PRODUTOS].str.split(";")
    exploded = fechados.explode("produto_list")
    exploded["produto_list"] = exploded["produto_list"].str.strip()
    exploded = exploded[exploded["produto_list"] != ""]

    secao("Mix de Vendas — Volume por Produto")
    mix = exploded["produto_list"].value_counts().reset_index()
    mix.columns = ["Produto", "Qtd"]
    mix["% Total"] = pd.to_numeric(mix["Qtd"] / mix["Qtd"].sum() * 100, errors="coerce").fillna(0).round(1).astype(str) + "%"

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        fig = px.bar(mix.head(15), x="Qtd", y="Produto", orientation="h",
                     color_discrete_sequence=[PURPLE], text="Qtd")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=420, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, width='stretch')
    with col_b:
        st.dataframe(mix, hide_index=True, width='stretch', height=min(len(mix)*38+50, 800))

    secao("Produtos por Closer")
    por_closer = exploded.groupby([COL_CLOSER, "produto_list"], observed=True).size().reset_index(name="Qtd")
    closer_opts = sorted(por_closer[COL_CLOSER].unique())
    if closer_opts:
        closer_sel2 = st.selectbox("Selecione o Closer", closer_opts)
        df_c = por_closer[por_closer[COL_CLOSER] == closer_sel2]
        fig2 = px.pie(df_c, names="produto_list", values="Qtd",
                      color_discrete_sequence=COLORS, hole=0.4)
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#EAEAEA",
            height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig2, width='stretch')


# ─────────────────────────────────────────────
# MÓDULO 4: PERFIL DO LEAD
# ─────────────────────────────────────────────
def modulo_perfil(df: pd.DataFrame):
    st.title("🧩 Perfil do Lead")
    _, df_reunioes, df_fechados, _ = render_filtros(df)

    st.caption("Reuniões = período de reunião · Fechados = período de fechamento")

    def rfconv(col, label):
        """Reuniões | Fechados | Conv R→F% por dimensão"""
        r = df_reunioes.groupby(col, observed=True).size().reset_index(name="Reuniões")
        f = df_fechados.groupby(col, observed=True).size().reset_index(name="Fechados")
        tb = r.merge(f, on=col, how="outer").fillna(0)
        tb["Reuniões"] = tb["Reuniões"].astype(int)
        tb["Fechados"] = tb["Fechados"].astype(int)
        tb["Conv R→F"] = pd.to_numeric(
            tb["Fechados"] / tb["Reuniões"].replace(0, float("nan")) * 100,
            errors="coerce").fillna(0).round(1).astype(str) + "%"
        return tb.sort_values("Fechados", ascending=False).rename(columns={col: label})

    def render_aba(col, label, color):
        tb = rfconv(col, label)
        col_a, col_b = st.columns([1, 1.4])
        with col_a:
            st.dataframe(tb, hide_index=True, width='stretch', height=min(len(tb)*38+50, 800))
        with col_b:
            fig = px.bar(tb, x=label, y=["Reuniões", "Fechados"],
                         barmode="group", color_discrete_sequence=[COLORS[1], color])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#EAEAEA", height=360,
                              margin=dict(l=0, r=0, t=10, b=0),
                              legend=dict(bgcolor="rgba(0,0,0,0)"))
            fig.update_xaxes(tickangle=30)
            st.plotly_chart(fig, width='stretch')

    aba1, aba2, aba3, aba4 = st.tabs(["🏠 Carteira de Imóveis", "📄 Contratos", "🧭 Jornada", "🔖 Tipo de Lead"])

    with aba1:
        secao("Carteira de Imóveis")
        render_aba(COL_CARTEIRA, "Carteira de Imóveis", COLORS[2])

    with aba2:
        secao("Contratos de Locação")
        render_aba(COL_CONTRATOS, "Contratos de Locação", COLORS[3])

    with aba3:
        secao("Jornada")
        render_aba(COL_JORNADA, "Jornada", COLORS[4])

    with aba4:
        secao("Tipo de Lead")
        render_aba(COL_TIPO, "Tipo de Lead", COLORS[5])


# ─────────────────────────────────────────────
# MÓDULO 5: COMPARAÇÃO MÊS A MÊS
# ─────────────────────────────────────────────
def modulo_comparacao(df: pd.DataFrame):
    st.title("📈 Comparação Mês a Mês")
    _, df_reunioes, df_fechados, _ = render_filtros(df)

    aba_geral, aba_closer, aba_jornada, aba_tipo = st.tabs(
        ["Visão Geral", "Por Closer", "Por Jornada", "Por Tipo de Lead"]
    )

    with aba_geral:
        secao("Reuniões e Fechados por Mês")
        gR = df_reunioes.groupby("mes_reuniao_dt", observed=True).size().reset_index(name="Reuniões")
        gF = df_fechados.groupby("mes_fechamento_dt", observed=True).size().reset_index(name="Fechados")

        # Tabela unificada
        tabela = gR.rename(columns={"mes_reuniao_dt": "Mês"}).merge(
            gF.rename(columns={"mes_fechamento_dt": "Mês"}), on="Mês", how="outer"
        ).fillna(0).sort_values("Mês")
        tabela["Reuniões"] = tabela["Reuniões"].astype(int)
        tabela["Fechados"] = tabela["Fechados"].astype(int)
        tabela["Conv R→F"] = pd.to_numeric(
            tabela["Fechados"] / tabela["Reuniões"].replace(0, float("nan")) * 100,
            errors="coerce").fillna(0).round(1).astype(str) + "%"

        col_tab, col_chart = st.columns([1, 2])

        with col_tab:
            st.dataframe(tabela, hide_index=True, width='stretch',
                         height=(len(tabela) + 1) * 38 + 10)

        with col_chart:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Reuniões", x=gR["mes_reuniao_dt"],    y=gR["Reuniões"], marker_color=COLORS[1]))
            fig.add_trace(go.Bar(name="Fechados", x=gF["mes_fechamento_dt"], y=gF["Fechados"], marker_color=COLORS[2]))
            fig.update_layout(
                barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#EAEAEA", height=(len(tabela) + 1) * 38 + 10,
                margin=dict(l=0, r=0, t=10, b=10),
                legend=dict(bgcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig, width='stretch')


    with aba_closer:
        secao("Fechados por Mês × Closer")
        if "mes_fechamento_dt" in df_fechados.columns:
            evo = df_fechados.groupby([COL_CLOSER, "mes_fechamento_dt"], observed=True).size().reset_index(name="Fechados")
            pivot = evo.pivot_table(index=COL_CLOSER, columns="mes_fechamento_dt", values="Fechados", fill_value=0)
            fig = px.bar(evo, x="mes_fechamento_dt", y="Fechados", color=COL_CLOSER,
                         barmode="group", color_discrete_sequence=COLORS, text_auto=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#EAEAEA", height=400, margin=dict(l=0, r=0, t=10, b=0),
                              legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, width='stretch')
            st.dataframe(pivot, width='stretch', height=min(len(pivot)*38+50, 800))

    with aba_jornada:
        secao("Fechados por Mês × Jornada")
        if "mes_fechamento_dt" in df_fechados.columns:
            evo = df_fechados.groupby([COL_JORNADA, "mes_fechamento_dt"], observed=True).size().reset_index(name="Fechados")
            pivot = evo.pivot_table(index=COL_JORNADA, columns="mes_fechamento_dt", values="Fechados", fill_value=0)
            fig = px.bar(evo, x="mes_fechamento_dt", y="Fechados", color=COL_JORNADA,
                         barmode="group", color_discrete_sequence=COLORS)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#EAEAEA", height=400, margin=dict(l=0, r=0, t=10, b=0),
                              legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, width='stretch')
            st.dataframe(pivot, width='stretch', height=min(len(pivot)*38+50, 800))

    with aba_tipo:
        secao("Fechados por Mês × Tipo de Lead")
        if "mes_fechamento_dt" in df_fechados.columns:
            evo = df_fechados.groupby([COL_TIPO, "mes_fechamento_dt"], observed=True).size().reset_index(name="Fechados")
            pivot = evo.pivot_table(index=COL_TIPO, columns="mes_fechamento_dt", values="Fechados", fill_value=0)
            fig = px.bar(evo, x="mes_fechamento_dt", y="Fechados", color=COL_TIPO,
                         barmode="group", color_discrete_sequence=COLORS)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#EAEAEA", height=400, margin=dict(l=0, r=0, t=10, b=0),
                              legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, width='stretch')
            st.dataframe(pivot, width='stretch', height=min(len(pivot)*38+50, 800))


# ─────────────────────────────────────────────
# MÓDULO 6: PERDIDOS PÓS-REUNIÃO
# ─────────────────────────────────────────────
def modulo_perdidos(df: pd.DataFrame):
    st.title("❌ Perdidos (pós-reunião)")
    _, _, _, df_perdidos = render_filtros(df)

    if df_perdidos.empty:
        st.info("Sem perdidos com reunião ocorrida no período selecionado.")
        return

    total_p = len(df_perdidos)
    secao(f"Total de perdidos após reunião: {total_p:,}")

    col_a, col_b = st.columns(2)

    with col_a:
        secao("Motivos de Perda")
        motivos = df_perdidos[COL_MOTIVO_PERDA].value_counts().reset_index()
        motivos.columns = ["Motivo", "Qtd"]
        motivos["% Total"] = pd.to_numeric(motivos["Qtd"] / total_p * 100, errors="coerce").fillna(0).round(1).astype(str) + "%"
        fig = px.bar(motivos, x="Qtd", y="Motivo", orientation="h",
                     color_discrete_sequence=[COLORS[3]], text="Qtd")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#EAEAEA", height=400, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width='stretch')
        st.dataframe(motivos, hide_index=True, width='stretch', height=min(len(motivos)*38+50, 800))

    with col_b:
        secao("Perdidos por Closer")
        por_closer = df_perdidos[COL_CLOSER].value_counts().reset_index()
        por_closer.columns = ["Closer", "Perdidos"]
        fig2 = px.bar(por_closer, x="Perdidos", y="Closer", orientation="h",
                      color_discrete_sequence=[COLORS[5]], text="Perdidos")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#EAEAEA", height=400, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, width='stretch')

    secao("Origem × Motivo de Perda")
    cross = df_perdidos.groupby([COL_ORIGEM, COL_MOTIVO_PERDA], observed=True).size().reset_index(name="Qtd")
    cross = cross.sort_values("Qtd", ascending=False).head(30)
    fig3 = px.bar(cross, x="Qtd", y=COL_ORIGEM, color=COL_MOTIVO_PERDA,
                  orientation="h", color_discrete_sequence=COLORS, barmode="stack")
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#EAEAEA", height=460, yaxis_title="", margin=dict(l=0, r=0, t=10, b=0),
                       legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig3, width='stretch')

    secao("Auditoria Individual")
    closer_audit = st.selectbox("Filtrar Closer", ["Todos"] + sorted(df_perdidos[COL_CLOSER].dropna().unique().tolist()))
    df_audit = df_perdidos if closer_audit == "Todos" else df_perdidos[df_perdidos[COL_CLOSER] == closer_audit]
    cols_show = [c for c in [COL_NOME, COL_CLOSER, COL_REUNIAO, COL_MOTIVO_PERDA, COL_SUBMOTIVO, COL_DESC_PERDA, COL_ORIGEM] if c in df_audit.columns]
    st.dataframe(df_audit[cols_show].reset_index(drop=True), hide_index=True, width='stretch', height=min(len(df_audit)*38+50, 800))



# ─────────────────────────────────────────────
# MÓDULO: RECEITA
# ─────────────────────────────────────────────
def modulo_receita(df: pd.DataFrame):
    st.title("💰 Receita")
    _, _, df_fechados, _ = render_filtros(df)

    # Garante coluna Valor numérica
    if COL_VALOR not in df_fechados.columns:
        st.warning("Coluna 'Valor' não encontrada no CSV.")
        return

    # Receita: apenas registros com etapa Pago (Date entered Pago como referência)
    dff = df_fechados[df_fechados["is_pago"] == True].copy() if "is_pago" in df_fechados.columns else df_fechados.copy()
    dff[COL_VALOR] = pd.to_numeric(dff[COL_VALOR], errors="coerce").fillna(0)

    receita_total = dff[COL_VALOR].sum()
    n_fechados    = len(dff)
    ticket_medio  = receita_total / n_fechados if n_fechados > 0 else 0

    # ── KPIs ────────────────────────────────────────────────────────────────
    secao("Visão Geral")
    k1, k2, k3 = st.columns(3)
    with k1: metric_card("Receita Total",   f"R$ {receita_total:,.0f}".replace(",", "."))
    with k2: metric_card("Contratos Fechados", f"{n_fechados:,}")
    with k3: metric_card("Ticket Médio",    f"R$ {ticket_medio:,.0f}".replace(",", "."))

    # ── Evolução Mensal ──────────────────────────────────────────────────────
    secao("Evolução Mensal")
    if "mes_fechamento_dt" in dff.columns:
        mensal = dff.groupby("mes_fechamento_dt", observed=True).agg(
            Receita=(COL_VALOR, "sum"),
            Contratos=(COL_ID, "count"),
        ).reset_index().sort_values("mes_fechamento_dt")
        mensal["Ticket Médio"] = pd.to_numeric(
            mensal["Receita"] / mensal["Contratos"].replace(0, float("nan")),
            errors="coerce").fillna(0).round(0)
        mensal["Receita_fmt"]      = mensal["Receita"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
        mensal["Ticket Médio_fmt"] = mensal["Ticket Médio"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))

        col_tab, col_chart = st.columns([1, 2])
        with col_tab:
            disp = mensal[["mes_fechamento_dt", "Receita_fmt", "Contratos", "Ticket Médio_fmt"]].copy()
            disp.columns = ["Mês", "Receita", "Contratos", "Ticket Médio"]
            st.dataframe(disp, hide_index=True, width='stretch',
                         height=(len(disp) + 1) * 38 + 10)
        with col_chart:
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(name="Receita (R$)", x=mensal["mes_fechamento_dt"],
                                   y=mensal["Receita"], marker_color=COLORS[2], yaxis="y1"))
            fig_m.add_trace(go.Scatter(name="Ticket Médio", x=mensal["mes_fechamento_dt"],
                                       y=mensal["Ticket Médio"], mode="lines+markers",
                                       marker_color=COLORS[3], yaxis="y2"))
            fig_m.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#EAEAEA", height=(len(mensal) + 1) * 38 + 10,
                margin=dict(l=0, r=0, t=10, b=10),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                yaxis=dict(title="Receita (R$)", showgrid=False),
                yaxis2=dict(title="Ticket Médio", overlaying="y", side="right", showgrid=False),
            )
            st.plotly_chart(fig_m, width='stretch')

    # ── Helper: tabela Receita + Contratos + Ticket Médio por dimensão ───────
    def fmt_brl(val):
        return f"R$ {int(val):,}".replace(",", ".")

    def dim_table(col, label):
        grp = dff.groupby(col, observed=True).agg(
            Receita=(COL_VALOR, "sum"),
            Contratos=(COL_ID, "count"),
        ).reset_index().sort_values("Receita", ascending=False)
        grp["Ticket Médio"] = pd.to_numeric(
            grp["Receita"] / grp["Contratos"].replace(0, float("nan")),
            errors="coerce").fillna(0).round(0)
        grp["Receita_num"]  = grp["Receita"].round(0)   # keep numeric for chart
        grp["Receita"]      = grp["Receita_num"].apply(fmt_brl)
        grp["Ticket Médio"] = grp["Ticket Médio"].apply(fmt_brl)
        return grp.rename(columns={col: label})

    def render_dim(col, label, color_idx=2):
        tb = dim_table(col, label)
        col_a, col_b = st.columns([1, 1.4])
        with col_a:
            cols_disp = [c for c in tb.columns if c != "Receita_num"]
            st.dataframe(tb[cols_disp], hide_index=True, width="stretch",
                         height=min(len(tb) * 38 + 50, 800))
        with col_b:
            fig = px.bar(tb.head(15), x=label, y="Receita_num",
                         color_discrete_sequence=[COLORS[color_idx]], text="Receita_num")
            fig.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#EAEAEA", height=400, margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title="Receita (R$)", xaxis_title="")
            fig.update_xaxes(tickangle=30)
            st.plotly_chart(fig, width="stretch")

    # ── Por Closer ───────────────────────────────────────────────────────────
    secao("Por Closer")
    render_dim(COL_CLOSER, "Closer", color_idx=1)

    # ── Por Produto ──────────────────────────────────────────────────────────
    secao("Por Produto Fechado")
    dff_prod = dff[dff[COL_PRODUTOS].notna()].copy()
    if not dff_prod.empty:
        dff_prod["produto_list"] = dff_prod[COL_PRODUTOS].str.split(";")
        exp = dff_prod.explode("produto_list")
        exp["produto_list"] = exp["produto_list"].str.strip()
        exp = exp[exp["produto_list"] != ""]
        grp_prod = exp.groupby("produto_list", observed=True).agg(
            Receita=(COL_VALOR, "sum"),
            Contratos=(COL_ID, "count"),
        ).reset_index().sort_values("Receita", ascending=False)
        grp_prod["Ticket Médio"] = pd.to_numeric(
            grp_prod["Receita"] / grp_prod["Contratos"].replace(0, float("nan")),
            errors="coerce").fillna(0).round(0)
        grp_prod["Receita_num"]  = grp_prod["Receita"].round(0)
        grp_prod["Receita"]      = grp_prod["Receita_num"].apply(fmt_brl)
        grp_prod["Ticket Médio"] = grp_prod["Ticket Médio"].apply(fmt_brl)
        grp_prod = grp_prod.rename(columns={"produto_list": "Produto"})
        col_a, col_b = st.columns([1, 1.4])
        with col_a:
            cols_disp = [c for c in grp_prod.columns if c != "Receita_num"]
            st.dataframe(grp_prod[cols_disp], hide_index=True, width="stretch",
                         height=min(len(grp_prod) * 38 + 50, 800))
        with col_b:
            fig_p = px.bar(grp_prod.head(15), x="Produto", y="Receita_num",
                           color_discrete_sequence=[COLORS[2]], text="Receita_num")
            fig_p.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
            fig_p.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#EAEAEA", height=420, margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title="Receita (R$)", xaxis_title="")
            fig_p.update_xaxes(tickangle=30)
            st.plotly_chart(fig_p, width='stretch')

    # ── Por Tipo de Lead ─────────────────────────────────────────────────────
    secao("Por Tipo de Lead")
    render_dim(COL_TIPO, "Tipo de Lead", color_idx=3)

    # ── Por Origem ───────────────────────────────────────────────────────────
    secao("Por Origem do Lead")
    render_dim(COL_ORIGEM, "Origem", color_idx=4)


# ─────────────────────────────────────────────
# MÓDULO: ALERTA PÓS-FECHAMENTO
# Quem entrou em Fechado e saiu (virou Perdido)
# ─────────────────────────────────────────────
def modulo_alerta(df: pd.DataFrame):
    st.title("🚨 Alerta Pós-Fechamento")
    _, _, df_fechados, _ = render_filtros(df)

    st.caption("Todos que tiveram 'Date entered Fechado' preenchida no período — independente da etapa atual.")

    # Base: todos que entraram em Fechado no período (já filtrado por mF em df_fechados)
    total_entraram = len(df_fechados)

    # Permanecem: etapa atual Fechado ou Pago
    permaneceram   = df_fechados[df_fechados[COL_ETAPA].isin(["Fechado", "Pago"])]
    # Saíram: etapa atual != Fechado e != Pago (viraram Perdidos ou outro)
    saiu           = df_fechados[~df_fechados[COL_ETAPA].isin(["Fechado", "Pago"])]

    n_total       = total_entraram
    n_permaneceram = len(permaneceram)
    n_saiu        = len(saiu)
    pct_saiu      = pct(n_saiu, n_total)

    # ── KPIs ──────────────────────────────────────────────────────────────
    secao("Visão Geral")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Entraram em Fechado",    f"{n_total:,}")
    with c2: metric_card("Permanecem (Fechado/Pago)", f"{n_permaneceram:,}", pct(n_permaneceram, n_total))
    with c3: metric_card("🚨 Saíram após Fechar",  f"{n_saiu:,}", pct_saiu)
    with c4: metric_card("Taxa de Retenção",        pct(n_permaneceram, n_total))

    if n_saiu == 0:
        st.success("Nenhum registro saiu da etapa Fechado/Pago no período selecionado.")
        return

    # ── Motivos ────────────────────────────────────────────────────────────
    secao("Motivos de Saída")
    col_a, col_b = st.columns([1, 1.4])
    motivos = saiu[COL_MOTIVO_PERDA].value_counts().reset_index()
    motivos.columns = ["Motivo", "Qtd"]
    motivos["% do Total"] = pd.to_numeric(
        motivos["Qtd"] / n_saiu * 100, errors="coerce"
    ).fillna(0).round(1).astype(str) + "%"

    with col_a:
        st.dataframe(motivos, hide_index=True, width='stretch',
                     height=min(len(motivos)*38+50, 500))
    with col_b:
        fig = px.bar(motivos, x="Qtd", y="Motivo", orientation="h",
                     color_discrete_sequence=[COLORS[5]], text="Qtd")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=min(len(motivos)*45+60, 500),
            margin=dict(l=0, r=0, t=10, b=0), yaxis_title="")
        st.plotly_chart(fig, width='stretch')

    # ── Por Closer ─────────────────────────────────────────────────────────
    secao("Saídas por Closer")
    col_c, col_d = st.columns([1, 1.4])
    por_closer = saiu.groupby(COL_CLOSER, observed=True).agg(
        Saídas=(COL_ID, "count"),
    ).reset_index().sort_values("Saídas", ascending=False)

    # Adiciona total fechados por closer para calcular % de saída
    total_por_closer = df_fechados.groupby(COL_CLOSER, observed=True).size().reset_index(name="Fechados")
    por_closer = por_closer.merge(total_por_closer, on=COL_CLOSER, how="left").fillna(0)
    por_closer["% Saída"] = pd.to_numeric(
        por_closer["Saídas"] / por_closer["Fechados"].replace(0, float("nan")) * 100,
        errors="coerce").fillna(0).round(1).astype(str) + "%"
    por_closer = por_closer.rename(columns={COL_CLOSER: "Closer"})

    with col_c:
        st.dataframe(por_closer, hide_index=True, width='stretch',
                     height=min(len(por_closer)*38+50, 600))
    with col_d:
        fig2 = px.bar(por_closer, x="Saídas", y="Closer", orientation="h",
                      color_discrete_sequence=[COLORS[5]], text="Saídas")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#EAEAEA", height=min(len(por_closer)*45+60, 600),
            margin=dict(l=0, r=0, t=10, b=0), yaxis_title="")
        st.plotly_chart(fig2, width='stretch')

    # ── Auditoria individual ───────────────────────────────────────────────
    secao("Registros para Investigação")
    cols_show = [c for c in [
        COL_NOME, COL_CLOSER, COL_FECHAMENTO, COL_ETAPA,
        COL_MOTIVO_PERDA, COL_SUBMOTIVO, COL_DESC_PERDA, COL_ORIGEM
    ] if c in saiu.columns]
    audit = saiu[cols_show].copy()
    audit[COL_FECHAMENTO] = audit[COL_FECHAMENTO].dt.strftime("%Y-%m-%d")
    st.dataframe(audit.reset_index(drop=True), hide_index=True, width='stretch',
                 height=min(len(audit)*38+50, 800))


# ─────────────────────────────────────────────
# MÓDULO: KENLO vs NÃO-KENLO
# Lógica independente dos filtros globais:
#   RO  → agrupado pelo ANO da Reunião Ocorrida
#   Fech → agrupado pelo ANO do Date entered Fechado
#   Kenlo = valor exato "Kenlo (Ingaia)" no campo ERP (split por ;)
# ─────────────────────────────────────────────
def modulo_kenlo(df: pd.DataFrame):
    st.title("🔄 Kenlo vs Não-Kenlo")
    st.caption("Reuniões = agrupadas pelo ano da Reunião Ocorrida · Fechados = agrupados pelo ano do Date entered Fechado")
    st.caption("Kenlo = ERP que utiliza contém exatamente 'Kenlo (Ingaia)'")

    # Flags (independente dos filtros globais)
    df = df.copy()
    df["is_kenlo"] = df[COL_ERP].astype(object).fillna("").apply(
        lambda x: "Kenlo (Ingaia)" in [p.strip() for p in x.split(";")]
    )
    df["ano_reuniao"] = df[COL_REUNIAO].dt.year
    df["ano_fechado"] = df[COL_FECHAMENTO].dt.year

    anos = [2024, 2025, 2026]

    def build_table(kenlo_flag, label):
        rows = []
        for ano in anos:
            ro   = df[(df["ano_reuniao"] == ano) & df["is_reuniao"] & (df["is_kenlo"] == kenlo_flag)].shape[0]
            fech = df[(df["ano_fechado"] == ano) & df["is_fechado"] & (df["is_kenlo"] == kenlo_flag)].shape[0]
            conv = round(fech / ro * 100, 2) if ro > 0 else 0
            rows.append({"Ano": str(ano), "Reuniões Ocorridas": ro, "Fechados": fech, "Conv R→F": f"{conv:.2f}%"})
        # Linha total
        ro_t   = sum(r["Reuniões Ocorridas"] for r in rows)
        fech_t = sum(r["Fechados"] for r in rows)
        conv_t = round(fech_t / ro_t * 100, 2) if ro_t > 0 else 0
        rows.append({"Ano": "TOTAL", "Reuniões Ocorridas": ro_t, "Fechados": fech_t, "Conv R→F": f"{conv_t:.2f}%"})
        return pd.DataFrame(rows)

    # ── Tabelas lado a lado ──────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        secao("ERP Utiliza: Kenlo (Ingaia)")
        tb_k = build_table(True, "Kenlo")
        st.dataframe(tb_k, hide_index=True, width='stretch',
                     height=(len(tb_k)+1)*38+10)

    with c2:
        secao("ERP Utiliza: NÃO é Kenlo")
        tb_nk = build_table(False, "Nao Kenlo")
        st.dataframe(tb_nk, hide_index=True, width='stretch',
                     height=(len(tb_nk)+1)*38+10)

    # ── Gráfico de conversão comparativo ────────────────────────────────
    secao("Conversão R→F: Kenlo vs Não-Kenlo por Ano")
    fig_data = []
    for grupo, kflag in [("Kenlo (Ingaia)", True), ("Nao Kenlo", False)]:
        for ano in anos:
            ro   = df[(df["ano_reuniao"] == ano) & df["is_reuniao"] & (df["is_kenlo"] == kflag)].shape[0]
            fech = df[(df["ano_fechado"] == ano) & df["is_fechado"] & (df["is_kenlo"] == kflag)].shape[0]
            conv = round(fech / ro * 100, 2) if ro > 0 else 0
            fig_data.append({"Ano": str(ano), "Grupo": grupo, "Conv%": conv})

    df_fig = pd.DataFrame(fig_data)
    fig = px.bar(df_fig, x="Ano", y="Conv%", color="Grupo", barmode="group",
                 color_discrete_sequence=[COLORS[2], COLORS[1]],
                 text=df_fig["Conv%"].apply(lambda x: f"{x:.2f}%"))
    fig.update_traces(textposition="outside")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#EAEAEA", height=380,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="Conv R→F (%)", xaxis_title="Ano",
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig, width='stretch')

    # ── Variação ano a ano ───────────────────────────────────────────────
    secao("Variação Ano a Ano (pp = pontos percentuais)")
    var_rows = []
    for grupo, kflag in [("Kenlo (Ingaia)", True), ("Nao Kenlo", False)]:
        convs = {}
        for ano in anos:
            ro   = df[(df["ano_reuniao"] == ano) & df["is_reuniao"] & (df["is_kenlo"] == kflag)].shape[0]
            fech = df[(df["ano_fechado"] == ano) & df["is_fechado"] & (df["is_kenlo"] == kflag)].shape[0]
            convs[ano] = round(fech / ro * 100, 2) if ro > 0 else 0
        var_rows.append({
            "Grupo":         grupo,
            "Conv 2024":     f"{convs[2024]:.2f}%",
            "Conv 2025":     f"{convs[2025]:.2f}%",
            "Var 24→25":     f"{convs[2025]-convs[2024]:+.2f}pp",
            "Conv 2026":     f"{convs[2026]:.2f}%",
            "Var 25→26":     f"{convs[2026]-convs[2025]:+.2f}pp",
        })
    st.dataframe(pd.DataFrame(var_rows), hide_index=True, width='stretch',
                 height=3*38+10)


# ─────────────────────────────────────────────
# ROTEAMENTO
# ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.info("👈 Faça upload do CSV do HubSpot na sidebar para começar.")
    st.stop()

df = st.session_state["df"]

if   modulo == "📊 Dashboard Geral":           modulo_geral(df)
elif modulo == "🏆 Performance de Closers":    modulo_closers(df)
elif modulo == "💰 Receita":                   modulo_receita(df)
elif modulo == "📦 Produtos Fechados":          modulo_produtos(df)
elif modulo == "🧩 Perfil do Lead":             modulo_perfil(df)
elif modulo == "📈 Comparação Mês a Mês":       modulo_comparacao(df)
elif modulo == "❌ Perdidos (pós-reunião)":     modulo_perdidos(df)
elif modulo == "🚨 Alerta Pós-Fechamento":      modulo_alerta(df)
elif modulo == "🔄 Kenlo vs Não-Kenlo":         modulo_kenlo(df)
