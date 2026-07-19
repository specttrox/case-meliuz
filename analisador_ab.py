import argparse
import os
import pandas as pd
from datetime import datetime

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

def analisar_dados(caminho_arquivo):
    print(f"Lendo arquivo: {caminho_arquivo}")
    df = pd.read_csv(caminho_arquivo)
    
    colunas_moeda = ["comissão", "cashback", "vendas totais"]
    for col in colunas_moeda:
        df[col] = df[col].apply(limpar_moeda)
    
    df["receita_liquida"] = df["comissão"] - df["cashback"]
    
    agrupado = df.groupby("Grupos de usuários").agg(
        compradores=("compradores", "sum"),
        comissao=("comissão", "sum"),
        cashback=("cashback", "sum"),
        vendas_totais=("vendas totais", "sum"),
        receita_liquida=("receita_liquida", "sum")
    ).reset_index()
    
    agrupado["lucro_por_comprador"] = agrupado["receita_liquida"] / agrupado["compradores"]
    agrupado["gmv_por_comprador"] = agrupado["vendas_totais"] / agrupado["compradores"]
    
    vencedor = agrupado.loc[agrupado["lucro_por_comprador"].idxmax()]
    
    parceiro = df["Parceiro"].iloc[0]
    gerar_relatorio_txt(agrupado, vencedor, parceiro)
    registrar_resultado(caminho_arquivo, vencedor, parceiro)

def gerar_relatorio_txt(df_agrupado, vencedor, parceiro):
    linhas_relatorio = [
        f"# Relatório de Teste A/B - {parceiro}",
        "",
        "## 1. Resumo Executivo",
        f"Recomendamos escalar o **{vencedor['Grupos de usuários']}** para 100% do tráfego.",
        f"Este grupo apresentou o maior Lucro por Comprador (R$ {vencedor['lucro_por_comprador']:.2f}).",
        "",
        "## 2. Métricas Principais (Acumuladas)",
    ]
    
    for _, row in df_agrupado.iterrows():
        linhas_relatorio.append(
            f"* **{row['Grupos de usuários']}:** "
            f"Lucro de R$ {row['lucro_por_comprador']:.2f} por usuário "
            f"| GMV por usuário: R$ {row['gmv_por_comprador']:.2f}"
        )
    
    nome_arquivo = f"relatorio_{parceiro.replace(' ', '')}.md"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio))
    
    print(f"Relatório gerado com sucesso: {nome_arquivo}")

def registrar_resultado(caminho_arquivo, vencedor, parceiro):
    nome_teste = os.path.basename(caminho_arquivo)
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    novo_dado = pd.DataFrame([{
        "Data do Registro": hoje,
        "Nome do Teste": nome_teste,
        "Parceiro": parceiro,
        "Variante Vencedora": vencedor["Grupos de usuários"],
        "Lucro por Comprador": round(vencedor["lucro_por_comprador"], 2),
        "Decisão": f"Escalar {vencedor['Grupos de usuários']}"
    }])
    
    arquivo_csv = "planilha_acompanhamento.csv"
    
    if os.path.exists(arquivo_csv):
        novo_dado.to_csv(arquivo_csv, mode="a", header=False, index=False, encoding="utf-8")
    else:
        novo_dado.to_csv(arquivo_csv, index=False, encoding="utf-8")
        
    print(f"Resultado registrado em: {arquivo_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisador de Testes A/B - Méliuz")
    parser.add_argument("arquivo", help="Caminho para o arquivo CSV do teste")
    args = parser.parse_args()
    
    analisar_dados(args.arquivo)
