# O que foi testado, o que custou e quanto demorou

Leia isto antes de prometer um resultado. Tudo abaixo foi medido em 01/11/2026, numa RTX 4090 alugada na Vast.ai (imagem `vastai/pytorch:latest`, PyTorch 2.11.0+cu128, ComfyUI e Openjutsu nas versões que o `instalar_maquina.sh` fixa). Preços mudam.

## O que funciona (e quanto de teste tem)

| Modo | Estado | O que se viu |
|---|---|---|
| Trocar roupa ou objeto (`change`) | **Testado, ótimo** | Trecho de 6,6 s (158 quadros) em 7 min de GPU. Rosto, boca e mãos seguiram o vídeo real; o áudio é o original |
| Trocar cenário (`background`) | **Testado, ótimo** | Trecho de 2,3 s (56 quadros) em 2,5 min. Só testamos nesse tamanho |
| Adicionar objeto ou personagem (`add`) | **Testado uma vez, funcionou** | 3 s (73 quadros) em uns 3 min. Sombra de contato e aceno gerados; o personagem ficou atrás da mão real. Caixa fixa, câmera parada |
| Trocar pessoa, relay com LoRA | **Testado** | Semelhança de rosto (SFace, acima de 0,363 conta como a mesma pessoa): **0,92 quando a pessoa entra no próprio vídeo, 0,68 em vídeo de outro ator** |
| Trocar pessoa, fluxo simples | **Testado em 1 vídeo com pessoa e 3 com um mascote** | Roupa, tatuagem e movimento saem bem; rosto parecido, não idêntico (a foto de referência era feita por IA) |
| Personagem não humano | **Funciona em parte** | O guia de movimento é humano, então a cabeça tende a sair humana. No relay, 12 s estouraram a memória da placa duas vezes |
| Remover (`remove`) | **NÃO testado** | O comando monta o fluxo certo, mas nunca rodou na GPU |
| Várias pessoas, "From picture", relight, corrigir rosto | **NÃO testados**, sem script aqui | Existem no Openjutsu, na interface web dele |
| Mac e Linux no computador da pessoa | **NÃO testados** | Só o Windows 11 (PowerShell e Git Bash). Os scripts usam só Python padrão, ssh, scp e ffmpeg |
| Placas que não sejam a RTX 4090 | **NÃO testadas** | O autor do Openjutsu testou numa RTX 4060 Ti de 16 GB |
| `--ultimas` (versões mais novas) | **NÃO testado** | Pode quebrar |
| Máquina com 64 GB de RAM | **NÃO testado por nós** | Uma das máquinas dos testes tinha 503 GB. O filtro pede 64 GB porque o autor do Openjutsu testou com isso |

### O que foi montado depois e só passou por teste de mentira

Estes programas foram escritos a partir dos scripts que rodaram de verdade em 01/11/2026 e passaram por testes automáticos contra uma Vast, um ComfyUI e um ssh de mentira (os de leitura também contra a Vast real). **Ainda não rodaram de ponta a ponta numa máquina nova**, porque isso gasta dinheiro:

- `vast.py alugar` e `destruir`;
- `remoto.py` contra uma máquina real da Vast;
- `instalar_maquina.sh` numa máquina vazia (as versões fixadas, os endereços dos modelos e o PyTorch foram conferidos um a um na internet; o que ele faz copia o instalador que deu certo);
- `trocar_pessoa.py` e `relay.py`: o fluxo que eles montam é **idêntico, nó a nó**, ao dos scripts originais testados na GPU. Só mudou a forma de passar os parâmetros;
- `objeto.py` é cópia fiel do arquivo que rodou na GPU.

Quem rodar pela primeira vez de ponta a ponta: fique de olho, e se algo quebrar, o `problemas.md` e o log (`remoto.py log NOME`) dizem onde.

## Quanto demora

| O que | Tempo |
|---|---|
| Instalar tudo (95 GB), numa máquina com internet de 2,6 Gb/s | 8,5 minutos. O básico (52 GB) deve levar menos; com internet de 500 Mb/s, estimamos uns 18 |
| Trecho de 2,3 s (56 quadros) | 2,5 min de GPU |
| Trecho de 3 s (73 quadros) | uns 3 min |
| Trecho de 6,6 s (158 quadros) | 7 min |

Dá uns 2,5 a 2,7 segundos de GPU por quadro, a 736p.

## Quanto custou (conferido nas cobranças da Vast em 01/11/2026)

| | Máquina 1 | Máquina 2 (até 23h) |
|---|---|---|
| Preço da hora | US$ 0,42 | US$ 0,49 (com o disco) |
| GPU | US$ 0,26 | US$ 0,55 |
| Disco | US$ 0,04 | US$ 0,13 |
| Download (modelos) | **US$ 0,14** (52,4 GB a US$ 0,003 por GB) | **US$ 3,71** (95 GB a US$ 0,039 por GB) |
| Upload | | US$ 0,05 |
| **Total** | **US$ 0,44** | **US$ 4,44** |

O que pesa é o **download** (o preço por GB varia mais de dez vezes entre máquinas) e o **tempo parado**. Um trecho de 6,6 s custa uns 5 centavos de GPU.

| Se deixar ligada (estimativa, os preços mudam) | Custo |
|---|---|
| RTX 4090 ligada o mês inteiro | US$ 300 a 350 por mês |
| RTX 4090 interruptível, parada fora de uso, com uns 2 h por dia | uns US$ 42 por mês |

## Medidas do fluxo simples de troca de pessoa (para quem for avaliar rosto)

Em um teste com foto de referência feita por IA, 47 quadros:

| Medida | Valor |
|---|---|
| Saída × foto de referência | 0,773 |
| Foto de referência × rosto real | 0,533 |
| Saída × rosto real | 0,519 |
| Estabilidade do rosto no tempo (média / pior) | 0,921 / 0,840 |
| Nitidez do rosto, saída / original | 51 / 29 |
| Áudio × original | idêntico |

A conclusão foi que a saída é fiel à foto, e a foto é que não era fiel à pessoa. As medidas de boca e de fundo são aproximações: servem para comparar versões, não como nota absoluta.

## Licenças e avisos que afetam o uso

- **MiniMax H3** (o modelo): licença só vale fora da UE, do Reino Unido, da Coreia do Sul e dos EUA, para o uso e para o resultado. Exige aviso claro de conteúdo feito por IA ao publicar, e proíbe se passar por alguém sem consentimento. Detalhes em `THIRD-PARTY.md`.
- **Corrigir rosto** (Openjutsu): usa o InsightFace `buffalo_l`, só para pesquisa, sem uso comercial. Esta skill não usa isso.
- **Rosto de outra pessoa**: só com o sim dela. Nunca para enganar.
