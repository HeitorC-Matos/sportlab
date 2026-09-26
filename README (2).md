# ⚽ SportLab — futebol em dados

Dashboard feito com Python e Streamlit. Usa os dados públicos da StatsBomb para analisar partidas de futebol.

**Pergunta do projeto:** quem participa mais da construção das jogadas e de onde saem as melhores chances de gol?

## Funcionalidades

- Seleção de campeonato, temporada, partida, time, jogador e intervalo de minutos.
- Placar, passes, passes certos, finalizações, gols, conversão e xG.
- Visão geral com comparação dos times e evolução dos passes a cada 15 minutos.
- Mapas de passes, chutes e calor com mplsoccer, além dos mapas interativos Plotly e PyDeck.
- Ranking, gráfico de participação por período com Altair e comparação de dois jogadores.
- Consulta dos eventos, detalhes em JSON, download e importação de CSV da partida.
- Cache para o carregamento dos dados e Session State para manter os filtros ao mudar de página.

## Arquivos

```text
sportlab_futebol/
├── app.py
├── exemplo_inicial.py
├── justificativas.txt
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── src/
│   ├── __init__.py
│   ├── dados.py
│   └── graficos.py
└── tests/
    └── test_dados.py
```

O `app.py` organiza a interface e as páginas. O arquivo `src/dados.py` busca, filtra e resume os dados; `src/graficos.py` gera os gráficos. O `justificativas.txt` contém as escolhas e explicações do trabalho.

## Como rodar no VS Code

Use de preferência o Python 3.11 ou 3.12. Abra a pasta `sportlab_futebol` no VS Code e use o terminal integrado.

**Windows (PowerShell):**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit hello
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit hello
```

O comando `streamlit hello` abre a demonstração do Streamlit. Depois, pare essa execução com `Ctrl + C` e rode o teste inicial:

```bash
streamlit run exemplo_inicial.py
```

Quando aparecer a mensagem **Hello World**, pare com `Ctrl + C` e abra o projeto:

```bash
streamlit run app.py
```

O navegador geralmente abre em `http://localhost:8501`. Se o PowerShell não permitir a ativação, abra o terminal CMD e execute `.venv\Scripts\activate.bat`.

## Como usar

1. Escolha uma competição, temporada e partida na barra lateral.
2. Defina minutos, quantidade de passes no mapa e quantidade de linhas da tabela. Clique em **Aplicar filtros**.
3. Escolha um time e, se quiser, um jogador específico.
4. Use o menu de navegação para abrir **Visão geral**, **Passes**, **Finalizações**, **Jogadores** ou **Eventos**.
5. Em **Eventos**, filtre os lances e baixe o CSV. Se desejar, importe esse mesmo arquivo pelo campo da barra lateral.

Os filtros de minutos valem para todas as páginas. A comparação dos times e o ranking de jogadores consideram o período escolhido; os indicadores do topo, os mapas e o CSV também respeitam o filtro de jogador.

O upload foi pensado para arquivos CSV de **eventos da mesma partida**, como os exportados pelo SportLab. Ele substitui temporariamente os eventos carregados pela API; não altera o placar oficial exibido no título.

## Como interpretar

**Passes certos:** passes sem resultado de erro na StatsBomb. **Conversão:** gols registrados como finalizações divididos pelo total de finalizações, multiplicado por 100. **xG:** soma das probabilidades estimadas de gol de cada chute. Gols contra podem aparecer no placar oficial, mas não no total de gols em chutes.

Os mapas usam as coordenadas do campo fornecidas pela StatsBomb, de 0 a 120 no comprimento e 0 a 80 na largura. O mapa PyDeck é um diagrama do campo, **não um mapa de localização geográfica**.

## Testes

Na pasta do projeto, execute:

```bash
python -m pytest -q
```

A aplicação usa a internet para consultar as partidas abertas da StatsBomb. Não apresenta dados ao vivo, e nem todos os campeonatos e temporadas possuem partidas públicas.

**Fonte:** [StatsBomb Open Data](https://github.com/statsbomb/open-data), acessada com a biblioteca [StatsBombPy](https://github.com/hudl/statsbombpy).
