from graph import *

plot_df = pd.read_excel("plot_Tutorial 2 barras.xlsx")
plot = PlotFlexibilidade(plot_df)
plot.gerar_relatorio()