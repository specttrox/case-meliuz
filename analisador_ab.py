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

def calcular_significancia(df, grupo_vencedor, grupo_controle="Grupo 1"):
    # Se o vencedor for o controle, comparamos com o segundo melhor.
    # Mas para simplificar, vamos sempre comparar o vencedor com o Grupo 1 (controle padrão)
    if grupo_vencedor == grupo_controle:
        # Pula se o vencedor for o próprio controle (não há 'aumento' a testar contra si mesmo)
        return None, "O Grupo de Controle (Grupo 1) foi o vencedor."

    # Filtramos as listas de lucro diário por usuário para o t-test
    lucros_vencedor = df[df["Grupos de usuários"] == grupo_vencedor]["lucro_diario_por_user"]
    lucros_controle = df[df["Grupos de usuários"] == grupo_controle]["lucro_diario_por_user"]
    
    # Teste T de Welch (equal_var=False é mais seguro)
    _, p_value = stats.ttest_ind(lucros_vencedor, lucros_controle, equal_var=False)
    
    significativo = p_value < 0.05
    confianca = (1 - p_value) * 100
    
    if significativo:
        mensagem = f"Possui significância estatística ({confianca:.1f}% de confiança). O resultado é seguro para escalar."
    else:
        mensagem = f"NÃO possui significância estatística (apenas {confianca:.1f}% de confiança). A diferença pode ser acaso."
        
    return p_value, mensagem

def analisar_dados(caminho_arquivo):
    print(f"Lendo arquivo: {caminho_arquivo}")
    df = pd.read_csv(caminho_arquivo)
    
    colunas_moeda = ["comissão", "cashback", "vendas totais"]
    for col in colunas_moeda:
        df[col] = df[col].apply(limpar_moeda)
    
    # Métricas diárias para a estatística
    df["receita_liquida"] = df["comissão"] - df["cashback"]
    # Se não houver compradores no dia, evita divisão por zero
    df["lucro_diario_por_user"] = df.apply(
        lambda row: row["receita_liquida"] / row["compradores"] if row["compradores"] > 0 else 0, axis=1
    )
    
    # Agrupamento total para as métricas finais
    agrupado = df.groupby("Grupos de usuários").agg(
        compradores=("compradores", "sum"),
        comissao=("comissão", "sum"),
        cashback=("cashback", "sum"),
        vendas_totais=("vendas totais", "sum"),
        receita_liquida=("receita_liquida", "sum")
    ).reset_index()
    
    agrupado["lucro_por_comprador"] = agrupado["receita_liquida"] / agrupado["compradores"]
    agrupado["gmv_por_comprador"] = agrupado["vendas_totais"] / agrupado["compradores"]
    
    # Determina o vencedor
    vencedor = agrupado.loc[agrupado["lucro_por_comprador"].idxmax()]
    nome_vencedor = vencedor["Grupos de usuários"]
    
    # Calcula significância estatística (comparando vencedor vs Grupo 1)
    p_value, msg_estatistica = calcular_significancia(df, nome_vencedor)
    
    parceiro = df["Parceiro"].iloc[0]
    gerar_relatorio_txt(agrupado, vencedor, parceiro, msg_estatistica)
    registrar_resultado(caminho_arquivo, vencedor, parceiro, msg_estatistica)

def gerar_relatorio_txt(df_agrupado, vencedor, parceiro, msg_estatistica):
    linhas_relatorio = [
        f"# Relatório de Teste A/B - {parceiro}",
        "",
        "## 1. Resumo Executivo",
        f"Recomendamos escalar o **{vencedor['Grupos de usuários']}** para 100% do tráfego.",
        f"Este grupo apresentou o maior Lucro por Comprador (R$ {vencedor['lucro_por_comprador']:.2f}).",
        "",
        "**Análise de Confiança (Estatística):**",
        f"> {msg_estatistica}",
        "",
        "## 2. Métricas Principais (Acumuladas no Período)",
    ]
    
    for _, row in df_agrupado.iterrows():
        linhas_relatorio.append(
            f"* **{row['Grupos de usuários']} ({int(row['compradores'])} compradores):** "
            f"Lucro de R$ {row['lucro_por_comprador']:.2f} por usuário "
            f"| GMV por usuário: R$ {row['gmv_por_comprador']:.2f}"
        )
        
    linhas_relatorio.append("")
    linhas_relatorio.append("## 3. Análise Crítica")
    linhas_relatorio.append("O teste leva em consideração o Lucro por Comprador (Receita Líquida / Compradores). Isso normaliza as variações no tamanho do tráfego de cada grupo, focando na rentabilidade real por indivíduo.")
    
    nome_arquivo = f"relatorio_{parceiro.replace(' ', '')}.md"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio))
    
    print(f"Relatório gerado com sucesso: {nome_arquivo}")

def registrar_resultado(caminho_arquivo, vencedor, parceiro, msg_estatistica):
    nome_teste = os.path.basename(caminho_arquivo)
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # Extrai o percentual de confiança da string para salvar limpo no csv
    confianca_match = [s for s in msg_estatistica.split() if '%' in s]
    confianca_str = confianca_match[0].replace(')', '') if confianca_match else "N/A"
    
    novo_dado = pd.DataFrame([{
        "Data do Registro": hoje,
        "Nome do Teste": nome_teste,
        "Parceiro": parceiro,
        "Variante Vencedora": vencedor["Grupos de usuários"],
        "Lucro por Comprador": round(vencedor["lucro_por_comprador"], 2),
        "Confiança Estatística": confianca_str,
        "Decisão": f"Escalar {vencedor['Grupos de usuários']}"
    }])
    
    arquivo_csv = "planilha_acompanhamento.csv"
    
    # utf-8-sig garante que o Excel no Windows leia acentos perfeitamente
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
