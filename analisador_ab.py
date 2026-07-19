import argparse
import os
import pandas as pd
from datetime import datetime
from scipy import stats

def limpar_moeda(valor_str):
    if pd.isna(valor_str):
        return 0.0
    texto_limpo = str(valor_str).replace("R$", "").strip()
    texto_limpo = texto_limpo.replace(".", "")
    texto_limpo = texto_limpo.replace(",", ".")
    try:
        return float(texto_limpo)
    except ValueError:
        return 0.0

def calcular_significancia(df, grupo_vencedor, grupo_desafiante):
    lucros_vencedor = df[df["Grupos de usuários"] == grupo_vencedor]["lucro_diario_por_user"]
    lucros_desafiante = df[df["Grupos de usuários"] == grupo_desafiante]["lucro_diario_por_user"]
    
    # Compara a variante com melhor métrica contra a segunda melhor
    _, p_value = stats.ttest_ind(lucros_vencedor, lucros_desafiante, equal_var=False)
    
    significativo = p_value < 0.05
    confianca = (1 - p_value) * 100
    
    if significativo:
        mensagem = f"Alta ({confianca:.1f}% de confiança). A diferença de performance da Variante Líder é estatisticamente válida."
        decisao = f"Escalar {grupo_vencedor}"
        status_csv = "Significativo"
    else:
        mensagem = f"Baixa ({confianca:.1f}% de confiança). Não há distância estatística suficiente para confirmar a liderança."
        decisao = f"Inconclusivo (Requer mais dados)"
        status_csv = "Inconclusivo"
        
    return status_csv, mensagem, decisao

def analisar_dados(caminho_arquivo):
    print(f"Lendo arquivo: {caminho_arquivo}")
    df = pd.read_csv(caminho_arquivo)
    
    colunas_moeda = ["comissão", "cashback", "vendas totais"]
    for col in colunas_moeda:
        df[col] = df[col].apply(limpar_moeda)
    
    df["receita_liquida"] = df["comissão"] - df["cashback"]
    df["lucro_diario_por_user"] = df.apply(
        lambda row: row["receita_liquida"] / row["compradores"] if row["compradores"] > 0 else 0, axis=1
    )
    
    agrupado = df.groupby("Grupos de usuários").agg(
        compradores=("compradores", "sum"),
        comissao=("comissão", "sum"),
        cashback=("cashback", "sum"),
        vendas_totais=("vendas totais", "sum"),
        receita_liquida=("receita_liquida", "sum")
    ).reset_index()
    
    agrupado["lucro_por_comprador"] = agrupado["receita_liquida"] / agrupado["compradores"]
    agrupado["gmv_por_comprador"] = agrupado["vendas_totais"] / agrupado["compradores"]
    
    # Calcula ROI (Retorno sobre o Investimento)
    agrupado["roi"] = agrupado.apply(
        lambda row: (row["receita_liquida"] / row["cashback"]) * 100 if row["cashback"] > 0 else 0, axis=1
    )
    
    # Ordena pelo Lucro por Comprador decrescente
    agrupado = agrupado.sort_values(by="lucro_por_comprador", ascending=False).reset_index(drop=True)
    
    vencedor = agrupado.iloc[0]
    desafiante = agrupado.iloc[1] if len(agrupado) > 1 else vencedor
    
    status_csv, msg_estatistica, decisao = calcular_significancia(df, vencedor["Grupos de usuários"], desafiante["Grupos de usuários"])
    
    parceiro = df["Parceiro"].iloc[0]
    gerar_relatorio_txt(agrupado, vencedor, parceiro, msg_estatistica, decisao)
    registrar_resultado(caminho_arquivo, vencedor, parceiro, status_csv, decisao)

def gerar_relatorio_txt(df_agrupado, vencedor, parceiro, msg_estatistica, decisao):
    linhas_relatorio = [
        f"# Relatório de Teste A/B - {parceiro}",
        "",
        "## 1. Resumo Executivo",
        f"**Decisão Recomendada:** {decisao}",
        f"A variante com melhor performance absoluta foi o **{vencedor['Grupos de usuários']}**, apresentando Lucro Médio de R$ {vencedor['lucro_por_comprador']:.2f} por usuário.",
        "",
        "**Confiabilidade Estatística:**",
        f"> {msg_estatistica}",
        "",
        "## 2. Detalhamento de Métricas (Acumulado)",
    ]
    
    for idx, row in df_agrupado.iterrows():
        # Adiciona um marcador de liderança apenas por texto, sem emojis
        marcador = " [Variante Líder]" if row['Grupos de usuários'] == vencedor['Grupos de usuários'] else ""
        
        linhas_relatorio.append(f"### {row['Grupos de usuários']}{marcador}")
        linhas_relatorio.append(f"- **Tamanho da Amostra:** {int(row['compradores'])} usuários compradores")
        linhas_relatorio.append(f"- **Lucro Médio (Métrica Principal):** R$ {row['lucro_por_comprador']:.2f} por usuário")
        linhas_relatorio.append(f"- **Lucro Absoluto Total:** R$ {row['receita_liquida']:,.2f}")
        linhas_relatorio.append(f"- **ROI do Cashback:** {row['roi']:.1f}%")
        linhas_relatorio.append(f"- **Vendas Totais (GMV) Médio:** R$ {row['gmv_por_comprador']:.2f} por usuário")
        linhas_relatorio.append("")
        
    linhas_relatorio.append("## 3. Entendendo as Métricas e a Decisão")
    linhas_relatorio.append("")
    linhas_relatorio.append("**A. Lucro Médio por Usuário (Métrica Rei)**")
    linhas_relatorio.append("A decisão não é baseada no lucro absoluto total, pois os grupos possuem volumes de tráfego diferentes. Dividir a receita líquida total pelo número de compradores garante que estamos comparando a eficiência intrínseca de cada grupo.")
    linhas_relatorio.append("")
    linhas_relatorio.append("**B. ROI do Cashback (Retorno sobre Investimento)**")
    linhas_relatorio.append("Representa a relação entre a Receita Líquida gerada e o custo do Cashback pago. Um ROI de 150%, por exemplo, significa que para cada R$ 1,00 gasto pelo Méliuz com cashback nesta variante, a empresa obteve R$ 1,50 de lucro líquido. É um indicador vital da saúde financeira do incentivo.")
    linhas_relatorio.append("")
    linhas_relatorio.append("**C. Significância Estatística (P-Value)**")
    linhas_relatorio.append("Na ciência de dados, não basta uma variante ter um lucro médio maior que as outras; é necessário provar matematicamente (através do Teste-T) que essa diferença não ocorreu por puro acaso ou por distorções pontuais de poucos usuários que compraram muito.")
    linhas_relatorio.append("Comparamos sempre a Variante Líder com a segunda melhor variante. Se a confiança for menor que 95%, o teste é classificado como 'Inconclusivo', o que impede a escala imediata da variante e recomenda que o teste continue rodando para coletar mais dados.")
    
    nome_arquivo = f"relatorio_{parceiro.replace(' ', '')}.md"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio))
    
    print(f"Relatório gerado com sucesso: {nome_arquivo}")

def registrar_resultado(caminho_arquivo, vencedor, parceiro, status_csv, decisao):
    nome_teste = os.path.basename(caminho_arquivo)
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    novo_dado = pd.DataFrame([{
        "Data do Registro": hoje,
        "Nome do Teste": nome_teste,
        "Parceiro": parceiro,
        "Variante Vencedora": vencedor["Grupos de usuários"],
        "Lucro por Comprador": round(vencedor["lucro_por_comprador"], 2),
        "Confiança Estatística": status_csv,
        "Decisão": decisao
    }])
    
    arquivo_csv = "planilha_acompanhamento.csv"
    
    if os.path.exists(arquivo_csv):
        novo_dado.to_csv(arquivo_csv, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        novo_dado.to_csv(arquivo_csv, index=False, encoding="utf-8-sig")
        
    print(f"Resultado registrado em: {arquivo_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisador de Testes A/B - Méliuz")
    parser.add_argument("arquivo", help="Caminho para o arquivo CSV do teste")
    args = parser.parse_args()
    
    analisar_dados(args.arquivo)
