import argparse
import os
import pandas as pd
from datetime import datetime
from scipy import stats
import gspread

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
    
    _, p_value = stats.ttest_ind(lucros_vencedor, lucros_desafiante, equal_var=False)
    
    significativo = p_value < 0.05
    confianca = (1 - p_value) * 100
    
    if confianca >= 99.9:
        conf_str = ">99.9"
    else:
        conf_str = f"{confianca:.1f}"
    
    if significativo:
        mensagem = f"Alta ({conf_str}% de confiança). A superioridade da Variante Líder é consistente e não é obra do acaso."
        decisao = f"Escalar {grupo_vencedor}"
        status_csv = "Significativo"
    else:
        mensagem = f"Baixa ({conf_str}% de confiança). A diferença para a segunda colocada pode ser acaso."
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
    
    for _, row in df_agrupado.iterrows():
        marcador = " [Variante Líder]" if row['Grupos de usuários'] == vencedor['Grupos de usuários'] else ""
        
        linhas_relatorio.append(f"### {row['Grupos de usuários']}{marcador}")
        linhas_relatorio.append(f"- **Tamanho da Amostra:** {int(row['compradores'])} usuários compradores")
        linhas_relatorio.append(f"- **Lucro Médio (Métrica Principal):** R$ {row['lucro_por_comprador']:.2f} por usuário")
        linhas_relatorio.append(f"- **Lucro Absoluto Total:** R$ {row['receita_liquida']:,.2f}")
        linhas_relatorio.append(f"- **Vendas Totais (GMV) Médio:** R$ {row['gmv_por_comprador']:.2f} por usuário")
        linhas_relatorio.append("")
        
    linhas_relatorio.append("## 3. Entendendo as Métricas e a Decisão")
    linhas_relatorio.append("")
    linhas_relatorio.append("**A. Lucro Médio por Usuário (Métrica Principal)**")
    linhas_relatorio.append("Dividir a receita líquida total pelo número de compradores garante uma comparação justa entre grupos, mesmo que eles tenham volumes de tráfego diferentes.")
    linhas_relatorio.append("")
    linhas_relatorio.append("**B. Significância Estatística e o Efeito do Acaso**")
    linhas_relatorio.append("Olhar apenas para a média final de lucro pode ser enganoso se uma variante foi impactada por distorções pontuais, como um 'super usuário' que sozinho realizou uma compra gigantesca em um único dia. Isso faria a variante parecer vitoriosa apenas por sorte (acaso).")
    linhas_relatorio.append("Utilizamos o Teste-T para analisar não apenas o lucro final, mas a consistência dos dados diários. Se o nível de confiança for inferior a 95%, o teste é classificado como 'Inconclusivo', indicando que o resultado pode ter sido sorte e recomendando-se aguardar mais dados.")
    
    os.makedirs("relatorios", exist_ok=True)
    nome_arquivo = os.path.join("relatorios", f"relatorio_{parceiro.replace(' ', '')}.md")
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio))
    
    print(f"Relatório gerado com sucesso: {nome_arquivo}")

def registrar_resultado(caminho_arquivo, vencedor, parceiro, status_csv, decisao):
    nome_teste = os.path.basename(caminho_arquivo)
    hoje = datetime.now().strftime("%Y-%m-%d")
    lucro_str = f"R$ {vencedor['lucro_por_comprador']:.2f}"
    
    # 1. Fallback Local (Sempre salva no CSV local como garantia)
    novo_dado = pd.DataFrame([{
        "Data do Registro": hoje,
        "Nome do Teste": nome_teste,
        "Parceiro": parceiro,
        "Variante Vencedora": vencedor["Grupos de usuários"],
        "Lucro por Comprador": lucro_str,
        "Confiança Estatística": status_csv,
        "Decisão": decisao
    }])
    
    os.makedirs("dados", exist_ok=True)
    arquivo_csv = os.path.join("dados", "planilha_acompanhamento.csv")
    if os.path.exists(arquivo_csv):
        novo_dado.to_csv(arquivo_csv, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        novo_dado.to_csv(arquivo_csv, index=False, encoding="utf-8-sig")
        
    print(f"Resultado registrado no backup local: {arquivo_csv}")
    
    # 2. Integração Cloud (Google Sheets)
    try:
        if not os.path.exists("credentials.json"):
            print("Aviso: 'credentials.json' não encontrado. O envio para a nuvem foi pulado.")
            return
            
        cliente = gspread.service_account(filename="credentials.json")
        link_planilha = "https://docs.google.com/spreadsheets/d/1fN3F46cT74EOtC0XWnCxTPlmeUWcklmC1Q4fxJ9AjdE"
        planilha = cliente.open_by_url(link_planilha).sheet1
        
        linha = [hoje, nome_teste, parceiro, vencedor["Grupos de usuários"], lucro_str, status_csv, decisao]
        planilha.append_row(linha)
        
        print("Sucesso! Resultado sincronizado com o Google Sheets na nuvem.")
        
    except Exception as e:
        print(f"Aviso: Falha ao sincronizar com o Google Sheets. (Erro: {e})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisador de Testes A/B - Méliuz")
    parser.add_argument("arquivo", help="Caminho para o arquivo CSV do teste")
    args = parser.parse_args()
    
    analisar_dados(args.arquivo)
