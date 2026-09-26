import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mplsoccer import Pitch


VERDE = "#57dbc1"
AMARELO = "#f6c96f"
VERMELHO = "#f28b82"
FUNDO = "#12292b"
LINHA = "#a0c8bd"


def criar_campo():
    return Pitch(pitch_type="statsbomb", pitch_color=FUNDO, line_color=LINHA)


def mapa_passes(dados, times, limite):
    passes = dados[dados["type"] == "Pass"].dropna(
        subset=["x", "y", "fim_x", "fim_y"]
    ).tail(limite)
    campo = criar_campo()
    fig, ax = campo.draw(figsize=(11, 6.5))
    fig.set_facecolor(FUNDO)
    cores = [(VERDE, "#8db0aa"), (AMARELO, VERMELHO)]

    for pos, time in enumerate(times):
        grupo = passes[passes["team"] == time]
        if grupo.empty:
            continue
        if "pass_outcome" in grupo.columns:
            certos = grupo[grupo["pass_outcome"].isna()]
            errados = grupo[grupo["pass_outcome"].notna()]
        else:
            certos = grupo
            errados = grupo.iloc[0:0]
        for sub, cor, nome in [
            (certos, cores[pos][0], "completos"),
            (errados, cores[pos][1], "incompletos"),
        ]:
            if not sub.empty:
                campo.arrows(
                    sub["x"], sub["y"], sub["fim_x"], sub["fim_y"],
                    color=cor, width=1.5, headwidth=4, alpha=0.85,
                    label=f"{time}: {nome}", ax=ax,
                )
    ax.legend(loc="upper left", facecolor=FUNDO, labelcolor="white", edgecolor=LINHA, fontsize=8)
    fig.tight_layout()
    return fig, len(passes)


def mapa_chutes(dados, times):
    chutes = dados[dados["type"] == "Shot"].dropna(subset=["x", "y"]).copy()
    if "shot_outcome" not in chutes.columns:
        chutes["shot_outcome"] = None
    if "shot_statsbomb_xg" not in chutes.columns:
        chutes["shot_statsbomb_xg"] = 0.0
    chutes["xg_num"] = pd.to_numeric(chutes["shot_statsbomb_xg"], errors="coerce").fillna(0)

    campo = criar_campo()
    fig, ax = campo.draw(figsize=(11, 6.5))
    fig.set_facecolor(FUNDO)
    for time, cor in zip(times, [VERDE, AMARELO]):
        grupo = chutes[chutes["team"] == time]
        sem_gol = grupo[grupo["shot_outcome"] != "Goal"]
        com_gol = grupo[grupo["shot_outcome"] == "Goal"]
        if not sem_gol.empty:
            campo.scatter(
                sem_gol["x"], sem_gol["y"],
                s=100 + sem_gol["xg_num"] * 900,
                color=cor, alpha=0.65, edgecolors="white", linewidth=0.6,
                label=f"{time}: chutes", ax=ax,
            )
        if not com_gol.empty:
            campo.scatter(
                com_gol["x"], com_gol["y"],
                s=170 + com_gol["xg_num"] * 900,
                color=cor, edgecolors="white", linewidth=1,
                marker="*", label=f"{time}: gols", ax=ax,
            )
    ax.legend(loc="upper left", facecolor=FUNDO, labelcolor="white", edgecolor=LINHA, fontsize=8)
    fig.tight_layout()
    return fig


def mapa_calor(dados):
    passes = dados[dados["type"] == "Pass"].dropna(subset=["x", "y"])
    campo = criar_campo()
    fig, ax = campo.draw(figsize=(11, 6.5))
    fig.set_facecolor(FUNDO)
    if not passes.empty:
        grade = campo.bin_statistic(passes["x"], passes["y"], statistic="count", bins=(8, 6))
        campo.heatmap(grade, ax=ax, cmap="YlGn", alpha=0.85)
        campo.label_heatmap(grade, ax=ax, color="#152622", fontsize=8, ha="center", va="center")
    fig.tight_layout()
    return fig


def grafico_passadores(resumo):
    dados = resumo.nlargest(8, "Passes certos").sort_values("Passes certos")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    if not dados.empty:
        sns.barplot(data=dados, x="Passes certos", y="Jogador", color=VERDE, ax=ax)
    ax.set_title("Quem mais acertou passes?", color="white", pad=15)
    ax.set_xlabel("Passes completos", color="white")
    ax.set_ylabel("")
    ax.tick_params(colors="white")
    for borda in ax.spines.values():
        borda.set_visible(False)
    fig.tight_layout()
    return fig


def grafico_relacao(resumo):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    if not resumo.empty:
        sns.scatterplot(
            data=resumo, x="Passes", y="Finalizações", size="xG",
            sizes=(70, 550), color=AMARELO, alpha=0.85,
            edgecolor="white", linewidth=0.6, legend="brief", ax=ax,
        )
        legenda = ax.get_legend()
        if legenda:
            legenda.get_frame().set_facecolor(FUNDO)
            for texto in legenda.get_texts():
                texto.set_color("white")
    ax.set_title("Passes × finalizações por jogador", color="white", pad=15)
    ax.set_xlabel("Passes realizados", color="white")
    ax.set_ylabel("Finalizações", color="white")
    ax.tick_params(colors="white")
    ax.grid(alpha=0.15)
    for borda in ax.spines.values():
        borda.set_visible(False)
    fig.tight_layout()
    return fig


def grafico_comparacao(resumo, estatistica):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    sns.barplot(data=resumo, x="Jogador", y=estatistica, hue="Jogador",
                palette=[VERDE, AMARELO], legend=False, ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel(estatistica, color="white")
    ax.tick_params(colors="white", axis="both")
    ax.grid(axis="y", alpha=0.15)
    for borda in ax.spines.values():
        borda.set_visible(False)
    fig.tight_layout()
    return fig


def mapa_interativo(dados, times, tipo, limite=140):
    import plotly.graph_objects as go

    fig = go.Figure()
    figuras = [
        dict(type="rect", x0=0, y0=0, x1=120, y1=80),
        dict(type="line", x0=60, y0=0, x1=60, y1=80),
        dict(type="circle", x0=50, y0=30, x1=70, y1=50),
        dict(type="rect", x0=0, y0=18, x1=18, y1=62),
        dict(type="rect", x0=102, y0=18, x1=120, y1=62),
        dict(type="rect", x0=0, y0=30, x1=6, y1=50),
        dict(type="rect", x0=114, y0=30, x1=120, y1=50),
    ]
    for figura in figuras:
        fig.add_shape(**figura, line=dict(color=LINHA, width=1.4))

    if tipo == "Pass":
        eventos = dados[dados["type"] == "Pass"].dropna(
            subset=["x", "y", "fim_x", "fim_y"]
        ).tail(limite)
    else:
        eventos = dados[dados["type"] == "Shot"].dropna(subset=["x", "y"])

    for time, cor in zip(times, [VERDE, AMARELO]):
        grupo = eventos[eventos["team"] == time].copy()
        if grupo.empty:
            continue
        if tipo == "Pass":
            xs, ys = [], []
            for _, lance in grupo.iterrows():
                xs.extend([lance["x"], lance["fim_x"], None])
                ys.extend([lance["y"], lance["fim_y"], None])
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", line=dict(color=cor, width=1.5),
                showlegend=False, hoverinfo="skip",
            ))
            resultado = grupo["pass_outcome"].fillna("Completo") if "pass_outcome" in grupo else "Completo"
            grupo["detalhes"] = (
                grupo["player"].fillna("Sem jogador") + " · "
                + grupo["minute"].astype(str) + " min · " + resultado
            )
            tamanho = 8
            simbolo = "circle"
        else:
            if "shot_statsbomb_xg" not in grupo:
                grupo["shot_statsbomb_xg"] = 0.0
            if "shot_outcome" not in grupo:
                grupo["shot_outcome"] = "Sem informação"
            xg = pd.to_numeric(grupo["shot_statsbomb_xg"], errors="coerce").fillna(0)
            grupo["detalhes"] = (
                grupo["player"].fillna("Sem jogador") + " · "
                + grupo["minute"].astype(str) + " min · xG "
                + xg.round(2).astype(str) + " · " + grupo["shot_outcome"].fillna("")
            )
            tamanho = (12 + xg * 25).tolist()
            simbolo = ["star" if r == "Goal" else "circle" for r in grupo["shot_outcome"]]

        fig.add_trace(go.Scatter(
            x=grupo["x"], y=grupo["y"], text=grupo["detalhes"],
            name=time, mode="markers", marker=dict(
                color=cor, size=tamanho, symbol=simbolo,
                line=dict(color="white", width=0.7),
            ), hovertemplate="%{text}<extra>%{fullData.name}</extra>",
        ))

    fig.update_layout(
        paper_bgcolor=FUNDO, plot_bgcolor=FUNDO, font_color="white",
        height=560, margin=dict(l=15, r=15, t=15, b=15),
        legend=dict(orientation="h", y=-0.04), dragmode="zoom",
    )
    fig.update_xaxes(range=[-3, 123], visible=False, fixedrange=False)
    fig.update_yaxes(range=[83, -3], visible=False, fixedrange=False,
                     scaleanchor="x", scaleratio=1)
    return fig


def comparativo_times_plotly(resumo):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Passes certos", "Finalizações"))
    for i, coluna in enumerate(["Passes certos", "Finalizações"], start=1):
        fig.add_trace(go.Bar(
            x=resumo["Time"], y=resumo[coluna],
            marker_color=[VERDE, AMARELO][:len(resumo)],
            text=resumo[coluna], textposition="auto", showlegend=False,
            hovertemplate="%{x}: %{y}<extra></extra>",
        ), row=1, col=i)
    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=55, b=25),
        paper_bgcolor=FUNDO, plot_bgcolor=FUNDO, font_color="white",
    )
    fig.update_yaxes(gridcolor="#315157")
    return fig


def comparativo_jogadores_plotly(resumo):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    colunas = ["Passes certos", "Finalizações", "xG"]
    fig = make_subplots(rows=1, cols=3, subplot_titles=colunas)
    for i, coluna in enumerate(colunas, start=1):
        fig.add_trace(go.Bar(
            x=resumo["Jogador"], y=resumo[coluna],
            marker_color=[VERDE, AMARELO][:len(resumo)],
            text=resumo[coluna].round(2), textposition="auto", showlegend=False,
            hovertemplate="%{x}: %{y}<extra></extra>",
        ), row=1, col=i)
    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=55, b=25),
        paper_bgcolor=FUNDO, plot_bgcolor=FUNDO, font_color="white",
    )
    fig.update_yaxes(gridcolor="#315157")
    return fig


def grafico_resultados_chutes(chutes):
    import plotly.graph_objects as go

    resultado = chutes["shot_outcome"].fillna("Não informado").value_counts()
    fig = go.Figure(go.Pie(
        labels=resultado.index, values=resultado.values, hole=0.55,
        marker=dict(colors=[VERDE, AMARELO, VERMELHO, "#7da0a4", "#adb9c0"]),
        textinfo="percent+label", hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        height=350, margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor=FUNDO, font_color="white", showlegend=False,
    )
    return fig


def mapa_pydeck(dados, times, limite=140):
    import pydeck as pdk

    passes = dados[dados["type"] == "Pass"].dropna(subset=["x", "y"]).tail(limite)
    pontos = []
    for _, lance in passes.iterrows():
        pontos.append({
            "x": float(lance["x"]), "y": float(lance["y"]),
            "jogador": str(lance.get("player", "Não informado")),
            "time": str(lance["team"]), "minuto": int(lance["minute"]),
            "cor": [87, 219, 193, 210] if lance["team"] == times[0] else [246, 201, 111, 210],
        })
    caminhos = [
        [[0, 0], [120, 0], [120, 80], [0, 80], [0, 0]],
        [[60, 0], [60, 80]],
        [[0, 18], [18, 18], [18, 62], [0, 62]],
        [[120, 18], [102, 18], [102, 62], [120, 62]],
    ]
    campo = pdk.Layer(
        "PolygonLayer", data=[{"area": [[0, 0], [120, 0], [120, 80], [0, 80]]}],
        get_polygon="area", get_fill_color=[19, 50, 52, 255], stroked=False,
    )
    linhas = pdk.Layer(
        "PathLayer", data=[{"caminho": c} for c in caminhos],
        get_path="caminho", get_color=[177, 214, 202, 230],
        get_width=1.5, width_min_pixels=1,
    )
    marcas = pdk.Layer(
        "ScatterplotLayer", data=pontos, get_position="[x, y]",
        get_fill_color="cor", get_radius=1.3, radius_min_pixels=4,
        pickable=True, auto_highlight=True,
    )
    return pdk.Deck(
        layers=[campo, linhas, marcas],
        views=[pdk.View(type="OrthographicView", controller=True)],
        initial_view_state=pdk.ViewState(target=[60, 40, 0], zoom=2),
        map_provider=None, map_style=None,
        tooltip={"text": "{jogador} · {time} · {minuto} min"},
        height=440,
    )
