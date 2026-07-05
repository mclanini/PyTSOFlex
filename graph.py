from pathlib import Path

import plotly.graph_objects as go
from plotly.io import to_html
import pandas as pd
import webbrowser

from datetime import datetime

class PlotFlexibilidade:
    """
    Classe responsável por construir as regiões de flexibilidade
    para cada tipo de evento (Tensão, Fluxo, Geração e Divergência).

    A região é construída selecionando, para cada direção (ângulo),
    o primeiro ponto onde o evento ocorreu.
    """

    def __init__(self, df):
        """
        Inicializa a classe.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame contendo todos os resultados da varredura.
        """

        # Cria uma cópia para evitar alterações no DataFrame original.
        self.df = df.copy()

        # Remove espaços extras dos nomes das colunas.
        self.df.columns = self.df.columns.str.strip()

        # Garante que as colunas numéricas estejam no formato correto.
        self.df["PL"] = pd.to_numeric(self.df["PL"])
        self.df["QL"] = pd.to_numeric(self.df["QL"])

        # Converte o ângulo de "45°" para 45.0.
        self.df["angulo"] = pd.to_numeric(
            self.df["Ângulo"]
                .astype(str)
                .str.replace("°", "", regex=False),
            errors="coerce"
        )

        # Armazena o ponto de operação original.
        self.original = (
            self.df[
                self.df["Característica"] == "Original"
            ]
            .iloc[0]
        )

    def obter_borda(self, evento):
        """
        Obtém os pontos que formam a borda da região de flexibilidade.

        Para cada ângulo, procura o primeiro ponto onde o evento ocorreu.

        Parameters
        ----------
        evento : str
            Pode ser:
                - "Violação de Tensão"
                - "Violação de Fluxo"
                - "Violação de Geração"
                - "Divergência"

        Returns
        -------
        pandas.DataFrame
            DataFrame contendo apenas os pontos que pertencem
            à borda da região.
        """

        borda = []

        # Percorre cada direção estudada.
        for angulo, grupo in (
            self.df[self.df["Característica"] == "Modificado"]
            .groupby("angulo")
        ):

            # Garante que os pontos estejam na ordem em que
            # foram simulados.
            grupo = grupo.sort_index().reset_index(drop=True)

            # Divergência é identificada quando o fluxo
            # deixa de convergir.
            if evento == "Divergência":

                candidatos = grupo[
                    grupo["Convergiu"] == "Não"
                ]

            # Demais eventos possuem uma coluna própria.
            else:

                candidatos = grupo[
                    grupo[evento] == "Sim"
                ]

            # Caso exista o evento nesta direção,
            # utiliza apenas o primeiro ponto.
            if not candidatos.empty:

                borda.append(candidatos.iloc[0])
        
        # Caso nenhum ponto tenha sido encontrado,
        # retorna um DataFrame vazio.
        if not borda:
            return pd.DataFrame()
        # Organiza os pontos pela ordem angular,
        # formando corretamente o polígono.
        return (
            pd.DataFrame(borda)
            .sort_values("angulo")
            .reset_index(drop=True)
        )

    def plot(self, evento, cor):
        """
        Gera um gráfico Plotly da região de flexibilidade.
        """
        borda = self.obter_borda(evento)
        if borda.empty:
            return None
        # Fecha o polígono repetindo o primeiro ponto
        borda_plot = pd.concat(
            [borda, borda.iloc[[0]]],
            ignore_index=True
        )
        hover = [
            (
                f"<b>Ângulo:</b> {row.angulo:.0f}°<br>"
                f"<b>P:</b> {row.PL:.2f}<br>"
                f"<b>Q:</b> {row.QL:.2f}<br>"
                f"<b>Evento:</b> {evento}"
            )
            for _, row in borda.iterrows()
        ]
        # tooltip do último ponto (igual ao primeiro)
        hover.append(hover[0])
        fig = go.Figure()
        # Região preenchida
        fig.add_trace(
            go.Scatter(
                x=borda_plot["PL"],
                y=borda_plot["QL"],
                mode="lines+markers",
                fill="toself",
                line=dict(
                    color=cor,
                    width=2
                ),
                marker=dict(
                    color="black",
                    size=8
                ),
                hovertemplate="%{text}<extra></extra>",
                text=hover,
                name=evento
            )
        )
        # Ponto de operação
        fig.add_trace(
            go.Scatter(
                x=[self.original["PL"]],
                y=[self.original["QL"]],
                mode="markers",
                marker=dict(
                    symbol="star",
                    size=18,
                    color="black"
                ),
                name="Ponto de Operação",
                hovertemplate=(
                    "<b>Ponto de Operação</b><br>"
                    "P=%{x:.2f}<br>"
                    "Q=%{y:.2f}"
                    "<extra></extra>"
                )
            )
        )
        fig.update_layout(
            title=evento,
            template="plotly_white",
            # width=850,
            height=520,
            autosize=True,
            margin=dict(l=40, r=20, t=50, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        fig.update_xaxes(
            title="P<sub>load</sub>",
            showgrid=True
        )
        fig.update_yaxes(
            title="Q<sub>load</sub>",
            showgrid=True,
            scaleanchor="x",
            scaleratio=1
        )
        return fig
    
    def gerar_relatorio(self, pasta_saida="Graficos", abrir_html=True):
        from datetime import datetime

        pasta = Path(pasta_saida)
        pasta.mkdir(exist_ok=True)

        cores = {
            "Violação de Tensão": "#d62728",
            "Violação de Fluxo": "#1f77b4",
            "Violação de Geração": "#2ca02c",
            "Divergência": "#9467bd"
        }

        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Regiões de Flexibilidade</title>
            <style>
                * {{
                    box-sizing: border-box;
                }}
                body {{
                    margin: 0;
                    padding: 35px;
                    background: #f3f5f8;
                    font-family: "Segoe UI", Arial, sans-serif;
                    color: #333;
                }}
                .container {{
                    width: min(95vw, 1500px);
                    margin: auto;
                }}
                .plotly-graph-div {{
                    width: 100% !important;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 5px;
                }}
                .subtitle {{
                    text-align: center;
                    color: #666;
                    margin-bottom: 35px;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 25px;
                }}
                .card {{
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 4px 15px rgba(0,0,0,.08);
                }}
                .card h2 {{
                    margin-top: 0;
                    text-align: center;
                }}
                .sem-evento {{
                    height: 480px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #777;
                    font-size: 18px;
                }}

            </style>
        </head>
        <body>
            <div class="container">
                <h1>Regiões de Flexibilidade</h1>
                <p class="subtitle">
                    Relatório gerado em
                    {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
                </p>
                <div class="grid">
        """
        primeiro = True
        for evento, cor in cores.items():
            html += f"""
            <div class="card">

                <h2>{evento}</h2>
            """
            fig = self.plot(evento, cor)
            if fig is None:
                html += """
                <div class="sem-evento">
                    Nenhuma ocorrência encontrada.
                </div>
                """
            else:
                html += to_html(
                    fig,
                    include_plotlyjs="cdn" if primeiro else False,
                    full_html=False,
                    config={
                        "displaylogo": False,
                        "responsive": True,
                        "scrollZoom": True
                    }
                )
            primeiro = False
            html += """
            </div>
            """
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        caminho = pasta / "index.html"
        caminho.write_text(
            html,
            encoding="utf8"
        )
        if abrir_html:
            webbrowser.open(caminho.resolve().as_uri())