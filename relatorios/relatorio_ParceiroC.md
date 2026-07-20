# Relatório de Teste A/B - Parceiro C

## 1. Resumo Executivo
**Decisão Recomendada:** Escalar Grupo 1
A variante com melhor performance absoluta foi o **Grupo 1**, apresentando Lucro Médio de R$ 7.64 por usuário.

**Confiabilidade Estatística:**
> Alta (>99.9% de confiança). A superioridade da Variante Líder é consistente e não é obra do acaso.

## 2. Detalhamento de Métricas (Acumulado)
### Grupo 1 [Variante Líder]
- **Tamanho da Amostra:** 4549 usuários compradores
- **Lucro Médio (Métrica Principal):** R$ 7.64 por usuário
- **Lucro Absoluto Total:** R$ 34,769.00
- **Vendas Totais (GMV) Médio:** R$ 382.16 por usuário

### Grupo 2
- **Tamanho da Amostra:** 4522 usuários compradores
- **Lucro Médio (Métrica Principal):** R$ 0.00 por usuário
- **Lucro Absoluto Total:** R$ 0.00
- **Vendas Totais (GMV) Médio:** R$ 372.67 por usuário

## 3. Entendendo as Métricas e a Decisão

**A. Lucro Médio por Usuário (Métrica Principal)**
Dividir a receita líquida total pelo número de compradores garante uma comparação justa entre grupos, mesmo que eles tenham volumes de tráfego diferentes.

**B. Significância Estatística e o Efeito do Acaso**
Olhar apenas para a média final de lucro pode ser enganoso se uma variante foi impactada por distorções pontuais, como um 'super usuário' que sozinho realizou uma compra gigantesca em um único dia. Isso faria a variante parecer vitoriosa apenas por sorte (acaso).
Utilizamos o Teste-T para analisar não apenas o lucro final, mas a consistência dos dados diários. Se o nível de confiança for inferior a 95%, o teste é classificado como 'Inconclusivo', indicando que o resultado pode ter sido sorte e recomendando-se aguardar mais dados.