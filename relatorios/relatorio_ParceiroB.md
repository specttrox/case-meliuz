# Relatório de Teste A/B - Parceiro B

## 1. Resumo Executivo
**Decisão Recomendada:** Escalar Grupo 1
A variante com melhor performance absoluta foi o **Grupo 1**, apresentando Lucro Médio de R$ 35.87 por usuário.

**Confiabilidade Estatística:**
> Alta (>99.9% de confiança). A superioridade da Variante Líder é consistente e não é obra do acaso.

## 2. Detalhamento de Métricas (Acumulado)
### Grupo 1 [Variante Líder]
- **Tamanho da Amostra:** 7990 usuários compradores
- **Lucro Médio (Métrica Principal):** R$ 35.87 por usuário
- **Lucro Absoluto Total:** R$ 286,570.00
- **Vendas Totais (GMV) Médio:** R$ 512.37 por usuário

### Grupo 2
- **Tamanho da Amostra:** 5452 usuários compradores
- **Lucro Médio (Métrica Principal):** R$ 26.26 por usuário
- **Lucro Absoluto Total:** R$ 143,157.00
- **Vendas Totais (GMV) Médio:** R$ 525.13 por usuário

### Grupo 3
- **Tamanho da Amostra:** 5029 usuários compradores
- **Lucro Médio (Métrica Principal):** R$ 10.46 por usuário
- **Lucro Absoluto Total:** R$ 52,593.00
- **Vendas Totais (GMV) Médio:** R$ 522.96 por usuário

## 3. Entendendo as Métricas e a Decisão

**A. Lucro Médio por Usuário (Métrica Principal)**
Dividir a receita líquida total pelo número de compradores garante uma comparação justa entre grupos, mesmo que eles tenham volumes de tráfego diferentes.

**B. Significância Estatística e o Efeito do Acaso**
Olhar apenas para a média final de lucro pode ser enganoso se uma variante foi impactada por distorções pontuais, como um 'super usuário' que sozinho realizou uma compra gigantesca em um único dia. Isso faria a variante parecer vitoriosa apenas por sorte (acaso).
Utilizamos o Teste-T para analisar não apenas o lucro final, mas a consistência dos dados diários. Se o nível de confiança for inferior a 95%, o teste é classificado como 'Inconclusivo', indicando que o resultado pode ter sido sorte e recomendando-se aguardar mais dados.