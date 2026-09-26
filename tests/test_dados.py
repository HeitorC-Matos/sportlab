import pandas as pd
import pytest
from src.dados import filtrar_eventos, ler_eventos_csv, resumo_jogadores, resumo_times, separar_posicoes


def dados_exemplo():
    return pd.DataFrame([
        {"minute": 10, "team": "Azul", "player": "Ana", "type": "Pass", "pass_outcome": None,
         "location": [30, 20], "pass_end_location": [50, 40]},
        {"minute": 20, "team": "Azul", "player": "Ana", "type": "Pass", "pass_outcome": "Incomplete",
         "location": [40, 30], "pass_end_location": [55, 25]},
        {"minute": 35, "team": "Azul", "player": "Bia", "type": "Shot", "shot_outcome": "Goal",
         "shot_statsbomb_xg": 0.3, "location": [104, 40]},
        {"minute": 72, "team": "Vermelho", "player": "Cris", "type": "Shot", "shot_outcome": "Saved",
         "shot_statsbomb_xg": 0.2, "location": [100, 38]},
    ])


def test_coordenadas():
    df = separar_posicoes(dados_exemplo())
    assert df.loc[0, "x"] == 30
    assert df.loc[0, "fim_y"] == 40
    assert pd.isna(df.loc[2, "fim_x"])


def test_filtros():
    df = filtrar_eventos(dados_exemplo(), 0, 45, "Azul", "Ana")
    assert len(df) == 2
    assert set(df["type"]) == {"Pass"}


def test_estatisticas():
    df = dados_exemplo()
    jogadores = resumo_jogadores(df).set_index("Jogador")
    times = resumo_times(df, ["Azul", "Vermelho"]).set_index("Time")
    assert jogadores.loc["Ana", "Passes"] == 2
    assert jogadores.loc["Ana", "Passes certos"] == 1
    assert jogadores.loc["Bia", "Gols"] == 1
    assert times.loc["Azul", "Passes"] == 2
    assert times.loc["Azul", "Gols em chutes"] == 1
    assert times.loc["Vermelho", "xG"] == 0.2


def test_importar_csv():
    csv = dados_exemplo().to_csv(index=False).encode("utf-8-sig")
    df = ler_eventos_csv(csv)
    df = separar_posicoes(df)
    assert len(df) == 4
    assert df.loc[0, "x"] == 30
    assert df.loc[1, "fim_y"] == 25


def test_csv_sem_colunas():
    with pytest.raises(ValueError, match="colunas"):
        ler_eventos_csv(b"time,gols\nAzul,2\n")
