import pandas as pd
import streamlit as st
from statsbombpy import sb


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_competicoes():
    return sb.competitions()


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_partidas(comp_id, temp_id):
    return sb.matches(competition_id=comp_id, season_id=temp_id)


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_eventos(jogo_id):
    dados = sb.events(match_id=jogo_id)
    return dados.sort_values(["period", "index"]).reset_index(drop=True)


def separar_posicoes(dados):
    dados = dados.copy()
    for coluna, prefixo in [("location", ""), ("pass_end_location", "fim_")]:
        if coluna not in dados.columns:
            dados[coluna] = None
        dados[prefixo + "x"] = dados[coluna].apply(
            lambda p: p[0] if isinstance(p, (list, tuple)) and len(p) >= 2 else None
        )
        dados[prefixo + "y"] = dados[coluna].apply(
            lambda p: p[1] if isinstance(p, (list, tuple)) and len(p) >= 2 else None
        )
    return dados


def filtrar_eventos(dados, inicio, fim, time="Ambos", jogador="Todos"):
    filtrados = dados[dados["minute"].between(inicio, fim)].copy()
    if time != "Ambos":
        filtrados = filtrados[filtrados["team"] == time]
    if jogador != "Todos":
        filtrados = filtrados[filtrados["player"] == jogador]
    return filtrados


def resumo_jogadores(dados):
    jogadores = dados["player"].dropna().unique()
    resumo = pd.DataFrame({"Jogador": jogadores})
    passes = dados[dados["type"] == "Pass"].copy()
    chutes = dados[dados["type"] == "Shot"].copy()

    if "pass_outcome" not in passes.columns:
        passes["pass_outcome"] = None
    if "shot_outcome" not in chutes.columns:
        chutes["shot_outcome"] = None
    if "shot_statsbomb_xg" not in chutes.columns:
        chutes["shot_statsbomb_xg"] = 0.0

    passes_certos = passes[passes["pass_outcome"].isna()]
    gols = chutes[chutes["shot_outcome"] == "Goal"]
    chutes["xg_num"] = pd.to_numeric(chutes["shot_statsbomb_xg"], errors="coerce").fillna(0)

    medidas = {
        "Passes": passes.groupby("player").size(),
        "Passes certos": passes_certos.groupby("player").size(),
        "Finalizações": chutes.groupby("player").size(),
        "Gols": gols.groupby("player").size(),
        "xG": chutes.groupby("player")["xg_num"].sum(),
    }
    for nome, serie in medidas.items():
        resumo[nome] = resumo["Jogador"].map(serie).fillna(0)
        if nome != "xG":
            resumo[nome] = resumo[nome].astype(int)
    return resumo.sort_values(["Passes", "Finalizações"], ascending=False)


def resumo_times(dados, times):
    linhas = []
    for time in times:
        eventos = dados[dados["team"] == time]
        passes = eventos[eventos["type"] == "Pass"]
        chutes = eventos[eventos["type"] == "Shot"]
        acertos = passes["pass_outcome"].isna().sum() if "pass_outcome" in passes else len(passes)
        gols = (chutes["shot_outcome"] == "Goal").sum() if "shot_outcome" in chutes else 0
        if "shot_statsbomb_xg" in chutes:
            xg = pd.to_numeric(chutes["shot_statsbomb_xg"], errors="coerce").fillna(0).sum()
        else:
            xg = 0.0
        linhas.append({
            "Time": time,
            "Passes": len(passes),
            "Passes certos": int(acertos),
            "Finalizações": len(chutes),
            "Gols em chutes": int(gols),
            "xG": round(float(xg), 2),
        })
    return pd.DataFrame(linhas)


def ler_eventos_csv(conteudo):
    from ast import literal_eval
    from io import BytesIO

    dados = pd.read_csv(BytesIO(conteudo))
    obrigatorias = {"minute", "team", "player", "type"}
    if not obrigatorias.issubset(dados.columns):
        faltando = ", ".join(sorted(obrigatorias - set(dados.columns)))
        raise ValueError(f"O CSV precisa das colunas: {faltando}.")
    dados["minute"] = pd.to_numeric(dados["minute"], errors="coerce")
    dados = dados.dropna(subset=["minute", "team", "type"]).copy()
    if dados.empty:
        raise ValueError("O CSV não contém eventos válidos.")
    dados["minute"] = dados["minute"].astype(int)
    for coluna in ["location", "pass_end_location"]:
        if coluna in dados.columns:
            def converter(valor):
                if isinstance(valor, str) and valor.startswith("["):
                    try:
                        return literal_eval(valor)
                    except (ValueError, SyntaxError):
                        return None
                return None
            dados[coluna] = dados[coluna].apply(converter)
    if "index" not in dados.columns:
        dados["index"] = range(len(dados))
    if "id" not in dados.columns:
        dados["id"] = [f"csv_{i}" for i in range(len(dados))]
    return dados.reset_index(drop=True)
