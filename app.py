import json

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

from src.dados import (
    carregar_competicoes,
    carregar_eventos,
    carregar_partidas,
    filtrar_eventos,
    ler_eventos_csv,
    resumo_jogadores,
    resumo_times,
    separar_posicoes,
)
from src.graficos import (
    comparativo_jogadores_plotly,
    comparativo_times_plotly,
    grafico_comparacao,
    grafico_passadores,
    grafico_relacao,
    grafico_resultados_chutes,
    mapa_calor,
    mapa_chutes,
    mapa_interativo,
    mapa_passes,
    mapa_pydeck,
)

st.set_page_config(page_title="SportLab | Futebol em dados", page_icon="⚽", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1300px;}
    .destaque {
        border: 1px solid #28545a;
        background: linear-gradient(100deg, #103c3b, #14242c);
        padding: 22px 28px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .destaque h1 {margin: 0; color: #eafff7; font-size: 2.5rem;}
    .destaque p {margin: 8px 0 0; color: #c0dbd4; font-size: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="destaque">
        <h1>⚽ SPORTLAB</h1>
        <p>Quem constrói as jogadas e de onde surgem as melhores chances de gol?</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("🎛️ Painel de controle")
st.sidebar.caption("Dados públicos da StatsBomb. Escolha sua partida.")

barra = st.sidebar.progress(0, text="Buscando competições...")
try:
    comps = carregar_competicoes()
except Exception as erro:
    barra.empty()
    st.error(f"Não foi possível buscar as competições: {erro}")
    st.info("Confira a conexão com a internet e atualize a página.")
    st.stop()

if comps.empty:
    barra.empty()
    st.warning("Nenhuma competição disponível no momento.")
    st.stop()

comps = comps.copy()
comps["genero_pt"] = comps["competition_gender"].map(
    {"male": "Masculino", "female": "Feminino"}
).fillna("Outro")
comps["opcao"] = (
    comps["country_name"] + " · " + comps["competition_name"]
    + " (" + comps["genero_pt"] + ")"
)
campeonatos = sorted(comps["opcao"].unique())
padrao = next(
    (i for i, nome in enumerate(campeonatos) if "FIFA World Cup" in nome and "Masculino" in nome),
    0,
)
campeonato = st.sidebar.selectbox("Campeonato", campeonatos, index=padrao, key="campeonato")
selecionadas = comps[comps["opcao"] == campeonato]
comp_id = int(selecionadas.iloc[0]["competition_id"])

anos = selecionadas.sort_values("season_name", ascending=False)
temporadas = anos["season_name"].drop_duplicates().tolist()
temporada = st.sidebar.selectbox("Temporada", temporadas, key=f"temp_{comp_id}")
temp_id = int(anos[anos["season_name"] == temporada].iloc[0]["season_id"])

barra.progress(40, text="Buscando partidas...")
try:
    partidas = carregar_partidas(comp_id, temp_id)
except Exception as erro:
    barra.empty()
    st.error(f"Não foi possível buscar as partidas: {erro}")
    st.stop()

if partidas.empty:
    barra.empty()
    st.warning("Não há partidas abertas nessa temporada. Escolha outra.")
    st.stop()

partidas = partidas.sort_values("match_date", ascending=False)
rotulos = {
    int(linha["match_id"]): f'{linha["home_team"]} × {linha["away_team"]} · {linha["match_date"]}'
    for _, linha in partidas.iterrows()
}
jogo_id = st.sidebar.selectbox(
    "Partida", partidas["match_id"].astype(int).tolist(),
    format_func=lambda cod: rotulos[cod], key=f"jogo_{comp_id}_{temp_id}",
)
partida = partidas[partidas["match_id"] == jogo_id].iloc[0]
mandante, visitante = partida["home_team"], partida["away_team"]
times = [mandante, visitante]

barra.progress(70, text="Buscando os lances...")
try:
    with st.spinner("Carregando os eventos da partida..."):
        eventos_api = carregar_eventos(jogo_id)
except Exception as erro:
    barra.empty()
    st.error(f"Não foi possível carregar os eventos: {erro}")
    st.stop()
barra.progress(100, text="Pronto!")
barra.empty()

st.sidebar.divider()
arquivo = st.sidebar.file_uploader(
    "Importar CSV da partida (opcional)", type="csv",
    help="Use um arquivo exportado pelo SportLab com os eventos desta mesma partida.",
    key=f"csv_{jogo_id}",
)
origem = "StatsBomb"
if arquivo is not None:
    try:
        df = ler_eventos_csv(arquivo.getvalue())
        if not set(df["team"].dropna().unique()).issubset(set(times)):
            st.error("O CSV contém times diferentes dos da partida selecionada.")
            st.stop()
        origem = "CSV importado"
    except (ValueError, pd.errors.ParserError, UnicodeError) as erro:
        st.error(f"Não foi possível ler o CSV: {erro}")
        st.stop()
else:
    df = eventos_api

df = separar_posicoes(df)
if df.empty:
    st.warning("Esta partida não tem eventos disponíveis para análise.")
    st.stop()

st.session_state["ultimo_jogo"] = int(jogo_id)
max_minuto = max(90, int(df["minute"].max()))

with st.sidebar.form(key=f"ajustes_{jogo_id}_{origem}"):
    st.subheader("Filtros da análise")
    minutos = st.slider("Minutos", 0, max_minuto, (0, max_minuto), key=f"min_{jogo_id}_{origem}")
    limite_passes = st.slider("Passes no mapa", 20, 300, 140, step=20, key=f"lim_{jogo_id}")
    qtd_eventos = st.number_input("Eventos na tabela", 10, 500, 50, step=10, key=f"qtd_{jogo_id}")
    somente_certos = st.checkbox("Só passes certos no mapa", key=f"certos_{jogo_id}")
    st.form_submit_button("Aplicar filtros", use_container_width=True)

janela = filtrar_eventos(df, minutos[0], minutos[1])
time_sel = st.sidebar.selectbox("Time em destaque", ["Ambos"] + times, key=f"time_{jogo_id}")
base_jog = janela if time_sel == "Ambos" else janela[janela["team"] == time_sel]
jogadores = sorted(base_jog["player"].dropna().unique().tolist())
jogador_sel = st.sidebar.selectbox(
    "Jogador", ["Todos"] + jogadores, key=f"jog_{jogo_id}_{time_sel}_{origem}"
)
filtrados = filtrar_eventos(df, minutos[0], minutos[1], time_sel, jogador_sel)
if somente_certos and "pass_outcome" in filtrados.columns:
    mapa_df = filtrados[
        (filtrados["type"] != "Pass") | (filtrados["pass_outcome"].isna())
    ]
else:
    mapa_df = filtrados

st.caption(f"{campeonato} / {temporada} / {partida['match_date']} / {origem}")
st.title(f"{mandante}  {int(partida['home_score'])} : {int(partida['away_score'])}  {visitante}")
st.caption("O placar é o oficial. As estatísticas abaixo seguem os filtros aplicados.")
if origem == "CSV importado":
    st.info("Análise pelo CSV enviado. O placar do título continua sendo o da partida selecionada.")

passes = filtrados[filtrados["type"] == "Pass"]
chutes = filtrados[filtrados["type"] == "Shot"].copy()
if "shot_outcome" not in chutes:
    chutes["shot_outcome"] = None
if "shot_statsbomb_xg" not in chutes:
    chutes["shot_statsbomb_xg"] = 0.0
acertos = int(passes["pass_outcome"].isna().sum()) if "pass_outcome" in passes else len(passes)
gols = int((chutes["shot_outcome"] == "Goal").sum())
xg = float(pd.to_numeric(chutes["shot_statsbomb_xg"], errors="coerce").fillna(0).sum())
conversao = 100 * gols / len(chutes) if len(chutes) else 0.0

with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Passes", len(passes))
    c2.metric("Passes certos", acertos)
    c3.metric("Finalizações", len(chutes))
    c4.metric("Gols em chutes", gols)
    c5.metric("Conversão", f"{conversao:.1f}%")

style_metric_cards(
    background_color="#15363c", border_color="#28545a",
    border_left_color="#57dbc1", border_radius_px=14, box_shadow=False,
)

texto_magico = f"📌 {len(filtrados)} eventos no recorte selecionado · {origem}"
texto_magico

with st.expander("Como ler os indicadores"):
    st.text(f"Intervalo analisado: {minutos[0]} a {minutos[1]} min")
    st.latex(r"\text{Conversão (\%)} = \frac{\text{Gols em chutes}}{\text{Finalizações}} \times 100")
    st.write(f"Nesse recorte: {gols} gol(s), {len(chutes)} finalização(ões) e {conversao:.1f}% de conversão.")
    st.code("conversao = 100 * gols / len(chutes) if len(chutes) else 0", language="python")
    st.caption("xG é a soma das probabilidades estimadas de gol. Gols contra podem aparecer no placar, mas não nos gols em chutes.")


def pagina_geral():
    st.header("📊 Visão geral")
    aba_a, aba_b = st.tabs(["Os dois times", "Ritmo da partida"])

    with aba_a:
        geral = resumo_times(janela, times)
        st.write("Estatísticas dos times nos minutos escolhidos:", geral)
        st.plotly_chart(comparativo_times_plotly(geral), use_container_width=True)
        st.subheader("Quem mais participou?")
        ranking = resumo_jogadores(janela)
        if ranking.empty:
            st.info("Sem jogadores nesse intervalo.")
        else:
            st.table(ranking.nlargest(5, "Passes certos")[["Jogador", "Passes certos", "Finalizações"]])
            a, b = st.columns(2)
            with a:
                if ranking["Passes certos"].sum() > 0:
                    fig = grafico_passadores(ranking)
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
                else:
                    st.info("Não há passes certos nesse período.")
            with b:
                fig = grafico_relacao(ranking)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            st.caption("No gráfico de dispersão, cada círculo representa um jogador; seu tamanho indica o xG.")

    with aba_b:
        st.subheader("Passes a cada 15 minutos")
        eventos_passe = janela[janela["type"] == "Pass"].copy()
        if eventos_passe.empty:
            st.info("Não há passes no período selecionado.")
        else:
            eventos_passe["Faixa (min)"] = (eventos_passe["minute"] // 15 * 15).astype(int)
            evolucao = eventos_passe.groupby(["Faixa (min)", "team"]).size().unstack(fill_value=0)
            st.line_chart(evolucao, color=["#57dbc1", "#f6c96f"][:len(evolucao.columns)])
            st.caption("Cada ponto soma os passes de um intervalo de 15 minutos.")
            tabela_ritmo = evolucao.reset_index()
            tabela_ritmo


def pagina_passes():
    st.header("➡️ Mapa de passes")
    st.write("As setas mostram a origem e o destino dos passes nos filtros escolhidos.")
    selecionados = mapa_df[mapa_df["type"] == "Pass"]
    if selecionados.empty:
        st.info("Não há passes para essa seleção.")
        return

    fig, exibidos = mapa_passes(mapa_df, times, limite_passes)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption(f"Últimos {exibidos} passes com coordenadas disponíveis.")

    if st.checkbox("Explorar os passes com o mouse", key=f"hover_p_{jogo_id}"):
        st.plotly_chart(mapa_interativo(mapa_df, times, "Pass", limite_passes), use_container_width=True)

    with st.expander("🧭 Posições dos passes no PyDeck"):
        st.caption("Mapa em coordenadas do campo (0–120 × 0–80), sem localização geográfica.")
        st.pydeck_chart(mapa_pydeck(mapa_df, times, limite_passes), use_container_width=True)

    st.subheader("Onde os passes começam?")
    fig = mapa_calor(mapa_df)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption("Células mais intensas indicam regiões com mais passes.")


def pagina_chutes():
    st.header("🎯 Finalizações")
    if chutes.empty:
        st.info("Não há finalizações para essa seleção.")
        return
    fig = mapa_chutes(filtrados, times)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption("Estrelas indicam gols; o tamanho de cada ponto acompanha o xG da chance.")
    if st.checkbox("Explorar os chutes com o mouse", key=f"hover_c_{jogo_id}"):
        st.plotly_chart(mapa_interativo(filtrados, times, "Shot"), use_container_width=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Resultado dos chutes")
        st.plotly_chart(grafico_resultados_chutes(chutes), use_container_width=True)
    with col_b:
        st.metric("xG total", f"{xg:.2f}")
        st.metric("Chutes", len(chutes))
        st.metric("Gols em chutes", gols)


def pagina_jogadores():
    st.header("👥 Jogadores")
    resumo = resumo_jogadores(base_jog)
    if resumo.empty:
        st.info("Não há jogadores no intervalo selecionado.")
        return
    st.dataframe(resumo.head(20), use_container_width=True, hide_index=True)

    st.subheader("Participação por período")
    passes_jog = base_jog[base_jog["type"] == "Pass"].copy()
    destaques = resumo.head(8)["Jogador"].tolist()
    passes_jog = passes_jog[passes_jog["player"].isin(destaques)]
    if not passes_jog.empty:
        passes_jog["Período"] = (passes_jog["minute"] // 15 * 15).astype(int)
        mapa = passes_jog.groupby(["player", "Período"]).size().reset_index(name="Passes")
        grafico = alt.Chart(mapa).mark_rect(stroke="#183037").encode(
            x=alt.X("Período:O", title="Minuto inicial de cada período"),
            y=alt.Y("player:N", title="Jogador"),
            color=alt.Color("Passes:Q", scale=alt.Scale(scheme="tealblues")),
            tooltip=["player:N", "Período:O", "Passes:Q"],
        ).properties(height=280)
        st.altair_chart(grafico, use_container_width=True)
    else:
        st.info("Não há passes para montar o gráfico por período.")

    st.subheader("Duelo de jogadores")
    opcoes = resumo["Jogador"].tolist()
    if len(opcoes) < 2:
        st.info("Escolha outro time ou intervalo para comparar dois jogadores.")
        return
    a, b = st.columns(2)
    jog_a = a.selectbox("Jogador A", opcoes, key=f"comp_a_{jogo_id}_{time_sel}")
    jog_b = b.selectbox("Jogador B", opcoes, index=1, key=f"comp_b_{jogo_id}_{time_sel}")
    metrica = st.radio(
        "Métrica em destaque", ["Passes", "Passes certos", "Finalizações", "Gols", "xG"],
        horizontal=True, key=f"met_{jogo_id}",
    )
    if jog_a == jog_b:
        st.info("Selecione dois jogadores diferentes.")
        return
    dois = resumo[resumo["Jogador"].isin([jog_a, jog_b])].copy()
    fig = grafico_comparacao(dois, metrica)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.plotly_chart(comparativo_jogadores_plotly(dois), use_container_width=True)
    st.dataframe(dois, use_container_width=True, hide_index=True)


def pagina_eventos():
    st.header("📋 Eventos")
    st.write("Consulte os lances e exporte os eventos com os filtros atuais.")
    tipo_sel = st.radio(
        "Tipo de evento", ["Todos", "Passes", "Finalizações", "Desarmes"],
        horizontal=True, key=f"tipo_{jogo_id}",
    )
    eventos = filtrados.copy()
    if tipo_sel == "Passes":
        eventos = eventos[eventos["type"] == "Pass"]
    elif tipo_sel == "Finalizações":
        eventos = eventos[eventos["type"] == "Shot"]
    elif tipo_sel == "Desarmes":
        eventos = eventos[eventos["type"] == "Duel"]
        eventos = eventos[eventos["duel_type"] == "Tackle"] if "duel_type" in eventos else eventos.iloc[:0]

    colunas = [
        "minute", "second", "team", "player", "type", "pass_outcome",
        "pass_end_location", "shot_outcome", "shot_statsbomb_xg", "location",
    ]
    colunas = [col for col in colunas if col in eventos.columns]
    nomes = {
        "minute": "Minuto", "second": "Segundo", "team": "Time", "player": "Jogador",
        "type": "Evento", "pass_outcome": "Resultado do passe",
        "pass_end_location": "Destino do passe", "shot_outcome": "Resultado do chute",
        "shot_statsbomb_xg": "xG", "location": "Localização",
    }
    st.subheader(f"{len(eventos)} eventos encontrados")
    st.dataframe(
        eventos[colunas].head(int(qtd_eventos)).rename(columns=nomes),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "⬇️ Baixar eventos filtrados (CSV)",
        data=eventos.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"eventos_{jogo_id}.csv", mime="text/csv", use_container_width=True,
    )
    st.caption("O CSV inclui todos os eventos filtrados, mesmo quando a tabela exibe menos linhas.")
    if not eventos.empty:
        with st.expander("🔍 Metadados de um lance em JSON"):
            indice = st.number_input(
                "Número do evento na tabela", min_value=1,
                max_value=min(len(eventos), int(qtd_eventos)), value=1, step=1,
                key=f"id_evento_{jogo_id}_{tipo_sel}",
            )
            registro = json.loads(eventos.iloc[[indice - 1]].to_json(orient="records"))[0]
            st.json(registro)


paginas = [
    st.Page(pagina_geral, title="Visão geral", icon="📊", default=True),
    st.Page(pagina_passes, title="Passes", icon="➡️"),
    st.Page(pagina_chutes, title="Finalizações", icon="🎯"),
    st.Page(pagina_jogadores, title="Jogadores", icon="👥"),
    st.Page(pagina_eventos, title="Eventos", icon="📋"),
]
st.navigation(paginas).run()
st.divider()
st.caption("StatsBomb Open Data · Dados históricos, não ao vivo · mplsoccer, Plotly, Altair e PyDeck")
