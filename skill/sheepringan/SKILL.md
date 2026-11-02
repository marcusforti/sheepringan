---
name: sheepringan
description: Use quando a pessoa quiser mudar um vídeo gravado no celular com IA, numa placa de vídeo alugada: trocar a roupa, o cenário ou a pessoa, adicionar ou remover um objeto ou personagem, mantendo rosto, boca e áudio reais quando o modo permite (o "Jutsu", o Openjutsu, o Sheepringan). Conduz tudo do zero para quem nunca alugou uma GPU: conta, crédito e chave na Vast.ai, escolher e alugar a máquina com o custo na mão e o ok da pessoa, instalar, preparar o vídeo, rodar, montar o final e apagar a máquina. Use também para "alugar GPU", "Vast.ai", "ComfyUI", "troca de roupa em vídeo" ou /sheepringan.
---

# sheepringan

Faz o "Jutsu": pega um vídeo gravado no celular e, com o Openjutsu numa placa de vídeo (GPU) alugada na Vast.ai, troca a roupa, o cenário ou a pessoa, ou adiciona e remove coisas. Nos modos de roupa, cenário e adicionar, o rosto, a boca e o áudio continuam os do vídeo real.

Quem usa normalmente nunca alugou uma GPU e não é programador. Você conduz: uma etapa por vez, em português simples, esperando a pessoa responder.

Nos comandos, `SCRIPTS` é a pasta `scripts` ao lado deste arquivo, com caminho completo. No Mac e no Linux, use `python3` no lugar de `python`.

## Antes de tudo: três perguntas

Faça estas perguntas e guarde as respostas. São regras da licença do modelo e de respeito com as pessoas.

1. **Onde você mora e onde vai usar o resultado?** A licença do modelo MiniMax H3 só vale fora da União Europeia, do Reino Unido, da Coreia do Sul e dos Estados Unidos (vale para o uso e para o resultado). Se for em um desses lugares, pare e leia `THIRD-PARTY.md` (na raiz do repositório) com a pessoa.
2. **Tem o rosto de outra pessoa no vídeo, ou vai usar a foto dela?** Só com o sim dela. Sem isso, não siga.
3. **Vai publicar?** A licença exige avisar de forma clara que o conteúdo foi feito ou alterado por IA. Nunca use para enganar ninguém nem para se passar por outra pessoa.

## Regras de ouro

1. **Dinheiro.** Nunca alugue sem o "sim" da pessoa ao custo estimado, mostrado em dólar e em palavras simples. O `--confirmo` só entra depois desse sim. Máquina ligada cobra por hora, mesmo sem uso. Máquina parada ainda cobra o disco. Só apagar encerra a cobrança.
2. **Apague no fim.** Ao terminar, pergunte se pode apagar a máquina, apague e confira com `status`. Se a pessoa sumir no meio, avise que a máquina continua cobrando.
3. **Segredo não passa pelo chat.** A chave da API da Vast quem cola no terminal é a pessoa. Se ela colar aqui, peça para trocar a chave depois. Nunca imprima nem grave chave em arquivo.
4. **Só mexa no que é seu.** Alugue só pelo `vast.py`. Apague só a máquina que esta sessão alugou (rótulo `sheepringan`). Se `conta` mostrar outra máquina ligada, avise a pessoa em vez de apagar.
5. **Seja honesto.** Leia `references/medidas.md` antes de prometer um resultado. Diga o que foi testado e o que não foi. Avise a pessoa de que o aluguel, a conversa com a máquina e o instalador ainda não rodaram de ponta a ponta numa máquina nova (só em partes e em testes de mentira). Se uma etapa falhar duas vezes pelo mesmo motivo, **pare e mostre o erro**: a máquina está cobrando enquanto você tenta de novo. Se precisar, apague-a.
6. **Escreva para leigo.** Frases curtas. Use a tabela de termos no fim deste arquivo.

## Primeiro passo, sempre

```
python "SCRIPTS/vast.py" conta
```

| O que aparecer | O que fazer |
|---|---|
| `FALTA: a ferramenta da Vast` | Leia `references/01-vast.md` e siga uma etapa por vez |
| `FALTAM ...` (chave da API, crédito, chave SSH) | Idem: `references/01-vast.md` |
| `ATENCAO: ja existe(m) ... maquina(s)` | Mostre a lista à pessoa. Não apague sem ela dizer que é dela |
| `PRONTO` | Siga para a etapa 2 |

## O fluxo

| Etapa | O que fazer | Leia |
|---|---|---|
| 1. Conta | Conta na Vast.ai, crédito, chave da API, chave SSH | `references/01-vast.md` |
| 2. Máquina | Procurar, mostrar o custo, pedir o ok, alugar | `references/02-maquina.md` |
| 3. Instalar | Instalar o Openjutsu e baixar os modelos (10 a 20 min) | `references/03-instalar.md` |
| 4. Vídeo | Escolher o trecho, deixar no formato certo, fazer a foto de referência | `references/04-video.md` |
| 5. Rodar | Roupa ou objeto, cenário, adicionar, remover ou trocar pessoa | `references/05-modos.md` |
| 6. Resultado | Baixar o clipe, inclusive quando a montagem final falha | `references/06-resultado.md` |
| 7. Montar | Juntar original e clipes, com corte na mão em movimento, flash e áudio original | `references/06-resultado.md` |
| 8. Encerrar | Apagar a máquina, conferir, ver quanto custou | `references/07-encerrar.md` |

Se algo der errado: `references/problemas.md`. O que foi testado, quanto custou e quanto demorou: `references/medidas.md`.

## Os programas, em uma linha cada

| Programa | Roda onde | Serve para |
|---|---|---|
| `SCRIPTS/vast.py` | no computador da pessoa | conta, procurar máquina com custo, alugar, status, gastos, apagar |
| `SCRIPTS/remoto.py` | no computador | falar com a máquina: enviar, baixar, rodar, comando longo, log, espera |
| `SCRIPTS/preparar_video.py` | no computador | 24 quadros, número exato de quadros, áudio do tamanho certo |
| `SCRIPTS/resultado.py` | no computador | trazer o resultado da máquina |
| `SCRIPTS/montar.py` | no computador | vídeo final |
| `SCRIPTS/instalar_maquina.sh` | na máquina alugada | instalar tudo |
| `SCRIPTS/objeto.py` | na máquina | roupa ou objeto, cenário, adicionar, remover |
| `SCRIPTS/trocar_pessoa.py`, `SCRIPTS/relay.py` | na máquina | trocar a pessoa |

`remoto.py subir` manda os programas da máquina para ela. Comando longo roda com `remoto.py fundo NOME "@arquivo.sh"` e se acompanha com `remoto.py espera NOME`. Escreva o comando num arquivo `.sh` (use a ferramenta de escrever arquivos) para não brigar com aspas no Windows.

## Termos: diga assim

| Termo | Diga assim |
|---|---|
| GPU | A placa de vídeo. É o "motor" que faz a IA mexer no vídeo. O seu computador não tem uma forte o bastante |
| Vast.ai | Uma loja que aluga computadores com placa de vídeo por hora |
| Alugar uma instância | Pegar um desses computadores emprestado. Cobra por hora enquanto existir |
| SSH | Um jeito seguro de controlar o computador alugado de longe |
| Modelo | O "cérebro" da IA: um arquivo enorme que precisa ser baixado lá. Tem uns 50 GB |
| Openjutsu | O programa livre que faz a troca no vídeo. Quem criou foi o D3voz |
| ComfyUI | O programa por baixo, que roda o Openjutsu |
| Quadro | Cada foto de um vídeo. São 24 quadros por segundo |
| Download | O tamanho do que a máquina baixa. A Vast cobra por GB, e o preço muda muito de máquina para máquina |
| Destruir ou apagar | Devolver a máquina. Para de cobrar, mas perde tudo que estava nela |
