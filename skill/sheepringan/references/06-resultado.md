# 6. Pegar o resultado e montar o vídeo final

## Pegar o resultado

```
python "SCRIPTS/resultado.py" roupa --saida saida
```

(`roupa` é o `--rotulo` que você usou.) O programa procura nesta ordem:

1. O vídeo **pronto, com áudio**, em `/root/ComfyUI/output/h3_oneclick_edit/` (`objeto.py`), `h3_oneclick_swap/` (`trocar_pessoa.py`) ou `relay/` (`relay.py`).
2. Se não achar, é porque **a montagem final falhou** (quase sempre por causa do áudio menor que o vídeo, que o `preparar_video.py` evita). Mas o trecho já foi gerado e está, **sem áudio**, em `/root/ComfyUI/output/h3_chains/<run>/generation/clips/`. O `objeto.py` imprimiu o `<run>` na linha `RUN edit_xxxxxxxxxx`. Passe esse nome:

```
python "SCRIPTS/resultado.py" roupa --run edit_xxxxxxxxxx --saida saida
```

O arquivo vem como `roupa_clipe_sem_audio.mp4`. Sem problema: o `montar.py` usa o áudio do vídeo original, e é esse áudio que deve ficar no final de qualquer jeito.

**Baixe logo.** O que está na máquina some quando ela é apagada (ou se o crédito acabar).

## Olhar o clipe antes de montar

Faça uma folha de quadros do clipe (`ffmpeg -i clipe.mp4 -vf "fps=4,scale=270:-1,tile=8x4" -frames:v 1 folha.jpg`) e olhe com a pessoa: a roupa ou o cenário está certo? O rosto e as mãos continuam bons? Apareceu texto inventado? Se não gostou, rode de novo com outro `--seed` (custa uns centavos).

## Montar: corte na mão em movimento, flash curto, áudio original

A troca fica quase invisível quando o corte cai com **uma mão (ou algo grande) em movimento na frente da câmera** e há um **clarão branco de uma fração de segundo**. O áudio é sempre o do vídeo original, sem emenda.

### Achar os pontos de corte

Olhe a folha de quadros do **vídeo original** e ache, dentro do trecho que você gerou, um instante em que a mão (ou o braço) cruza a frente da área que mudou. Esse instante, em segundos do original, é o `--corte`.

- Para **roupa**: a mão cruzando o peito.
- Para **cenário**: qualquer movimento grande da pessoa ou da mão.
- Para **adicionar**: entre quando a mão real já saiu da caixa onde o personagem aparece.
- O corte tem que estar **dentro** do que o clipe cobre: do segundo em que você cortou o trecho (`--inicio` do `preparar_video.py`) até esse início mais a duração do clipe.

### Montar

Cada `--parte` é `ARQUIVO@SEGUNDO`: o clipe gerado e o segundo do **original** em que o primeiro quadro dele corresponde. Cada `--corte` é o segundo do original em que aquela parte entra.

```
python "SCRIPTS/montar.py" --original take.mp4 --saida final.mp4 \
  --parte roupa.mp4@6.25 --parte cenario.mp4@10.5 --corte 6.47 --corte 11.53
```

Resultado: o original de 0 a 6,47 s, a roupa nova de 6,47 a 11,53 s, o cenário novo de 11,53 s até o fim. Esse foi o caso real: moletom vira jaqueta vermelha com a mão cruzando o peito e depois o fundo vira um escritório na segunda passada da mão.

Para **voltar** ao original no fim, use o próprio original como última parte: `--parte take.mp4@0` e mais um `--corte`.

| Opção | Para quê |
|---|---|
| `--flash-saida 0.07`, `--flash-entrada 0.12` | Duração do clarão (segundos) no fim do trecho que sai e no começo do que entra |
| `--ganho-db 11` | Sobe o volume do áudio original (com limitador). Útil se a gravação saiu baixa |
| `--tamanho 1080x1920` | Muda o tamanho do final (padrão: o do original) |
| `--fim 12.8` | Onde termina (padrão: até onde o último trecho alcança) |
| `--crf 18` | Qualidade (menor = melhor e maior arquivo) |

O programa avisa se o corte pedido sai do que a parte cobre, e confere a duração do arquivo final.

O vídeo final tem a **mesma duração do original** e o **áudio original**. Não há câmera lenta.

## Conferir e entregar

1. Assista ao final inteiro com a pessoa: os cortes, o áudio, o rosto.
2. Se for publicar: avise de forma clara que foi feito ou alterado por IA (a licença do modelo exige), e só com o sim de qualquer pessoa que apareça. Nunca para enganar ninguém.
3. Siga para `07-encerrar.md`. A máquina ainda está cobrando.
