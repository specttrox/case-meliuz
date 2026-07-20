# Méliuz - Analisador AI-Native de Testes A/B

Este projeto resolve o case de Engenharia de Operações Integradas do Méliuz. Ele consiste em uma solução robusta em Python para automatizar a análise, extrair a significância estatística e reportar decisões de testes A/B de cashback.

## Arquitetura da Solução

O desafio pedia uma arquitetura focada em IA ("AI-Native"). A solução foi construída separando a lógica matemática (pesada) da orquestração de IA (prompt):

1. **`analisador_ab.py` (O Motor):** Script Python puro. Lê o CSV, trata as anomalias monetárias, calcula métricas de negócio (Lucro por Usuário) e roda testes estatísticos (SciPy) para garantir a veracidade do resultado.
2. **`instrucoes_ia.md` (O Cérebro):** O prompt projetado para guiar qualquer agente (Claude, Cursor, ChatGPT) a ler dados, acionar o motor Python e apresentar a resposta final em formato gerencial.
3. **Integração Cloud (Google Sheets):** O sistema salva as decisões em nuvem em tempo real (via API `gspread`), mantendo um "Graceful Fallback" para CSV local caso haja falha de conexão.

---

## Como testar este projeto

### Pré-requisitos

Certifique-se de ter o Python instalado na sua máquina, assim como as bibliotecas necessárias:

```bash
pip install pandas scipy gspread
```

### Rodando via IA (O jeito esperado)

Se você estiver utilizando uma IDE com IA (como o Cursor) ou o Claude Code no terminal:

1. Abra este diretório na ferramenta.
2. Peça para a IA ler o arquivo `instrucoes_ia.md` e execute a análise para o dataset desejado. Por exemplo: _"Siga o fluxo do instrucoes_ia.md para processar o arquivo dataset_01_parceiroA.csv"_.
3. A IA cuidará de rodar o script e sumarizar o resultado gerado.

### Rodando Tradicionalmente (Via Terminal)

Se preferir rodar manualmente para testar o código:

```bash
python analisador_ab.py dataset_01_parceiroA.csv
```

Isso gerará automaticamente o arquivo `relatorio_ParceiroA.md` na raiz do projeto contendo toda a análise.

---

## Planilha de Acompanhamento (Google Sheets)

Como prova conceitual do envio de dados em nuvem, foi criada uma planilha de destino real.
**Acesso Público (Visualização):**
[Acompanhamento Testes A/B - Méliuz](https://docs.google.com/spreadsheets/d/1fN3F46cT74EOtC0XWnCxTPlmeUWcklmC1Q4fxJ9AjdE/edit?usp=sharing)

> **Nota de Segurança:** Por boas práticas, o arquivo `credentials.json` responsável por dar write-access à planilha foi omitido deste repositório via `.gitignore`.
>
> Se você rodar o script agora na sua máquina local, o sistema detectará a ausência da chave e salvará os resultados em um arquivo de contingência seguro na raiz do projeto chamado `planilha_acompanhamento.csv`. Caso deseje testar o envio para a nuvem em tempo real, forneça um arquivo `credentials.json` válido do Google Cloud Platform na raiz do projeto.

---

## Decisões Analíticas

- **Por que 'Lucro por Comprador' e não 'Lucro Total'?**
  Em testes A/B, o volume de tráfego injetado em cada variante pode ser diferente. A métrica de "Lucro Médio por Comprador" normaliza a base, revelando a rentabilidade intrínseca da variante e respondendo com segurança à pergunta _"Qual devemos escalar para 100%?"_.

- **Significância Estatística (Teste-T)**
  Um único "super comprador" poderia distorcer um dia inteiro e dar a vitória a um grupo por puro acaso. O algoritmo usa `scipy.stats.ttest_ind` comparando o dia a dia da Variante Líder com a 2ª melhor variante. Caso a confiança seja menor que 95%, o teste trava a escalabilidade, definindo a decisão como **"Inconclusivo"**.
