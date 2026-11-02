# 8. Encerrar: apagar a máquina e conferir

**Máquina ligada cobra por hora, mesmo sem ninguém usando. Máquina parada ainda cobra o disco. Só apagar encerra a cobrança.** Esta etapa não é opcional.

## 1. Garantir que tudo foi baixado

Antes de apagar, confira com a pessoa: os vídeos finais e os clipes estão no computador dela? Tudo que está na máquina (modelos, vídeos, resultados) some para sempre ao apagar.

## 2. Perguntar

Diga à pessoa, com estas palavras:

> Terminamos. A máquina continua cobrando uns US$ X por hora, mesmo parada. Se eu apagar agora, a cobrança para, mas ela perde os modelos: na próxima vez, vamos baixar tudo de novo (o que custou US$ Y). Se você vai fazer mais vídeos hoje, posso deixar ligada, mas lembro de apagar no fim. Apago agora?

Opções:

| Escolha | Resultado | Quando |
|---|---|---|
| **Apagar** | Para de cobrar. Perde tudo | Padrão. Terminou, ou só vai voltar outro dia |
| Deixar ligada | Cobra por hora | Vai gravar e rodar mais vídeos nas próximas horas. Combine um horário para apagar |
| Parar (`vastai stop instance`) | Para a GPU, **mas o disco continua cobrando** e a placa pode ser alugada por outra pessoa, então talvez nem volte | Quase nunca vale a pena para quem usa pouco. Um mês de disco parado custa dezenas de dólares |

## 3. Apagar e conferir

```
python "SCRIPTS/vast.py" destruir ID --confirmo
python "SCRIPTS/vast.py" status
```

Tem que aparecer `Conferido: nao ha mais nenhuma maquina cobrando` e, no `status`, `Nenhuma maquina alugada agora`. Se aparecer outra máquina, mostre à pessoa: pode ser de outro projeto dela. Não apague sem ela dizer que é dela.

## 4. Quanto custou de verdade

```
python "SCRIPTS/vast.py" gastos
```

Mostra, por máquina, o que foi cobrado de GPU, disco, download e upload. A Vast fecha as cobranças por dia, então a última pode demorar um pouco para aparecer. Compare com a estimativa que você deu: se ficou bem diferente, anote para a próxima.

## 5. Se a pessoa sumiu no meio

Se a pessoa parou de responder e a máquina está ligada, avise com clareza (mesmo que ela volte só depois) que a máquina **continua cobrando** e quanto custa por dia. Não apague sozinho o que não é seu e não apague sem o combinado, mas deixe o aviso escrito.

## Quanto custa deixar uma máquina por perto (estimativa; os preços mudam)

| Uso | Custo aproximado |
|---|---|
| RTX 4090 ligada o mês inteiro | US$ 300 a 350 por mês |
| RTX 4090 interruptível, parada fora de uso, com uns 2 h por dia | uns US$ 42 por mês |
| Apagar depois de cada sessão e baixar tudo de novo | Entre US$ 0,14 e US$ 3,71 de download por sessão, mais as horas |

Com uma sessão por semana, alugar e apagar a cada vez costuma sair bem mais barato que manter a máquina (4 sessões de US$ 1 a US$ 5, contra uns US$ 42 por mês). Estimativas de 01/11/2026.
