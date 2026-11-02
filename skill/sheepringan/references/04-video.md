# 4. O vídeo e a foto de referência

O resultado depende mais desta etapa do que da GPU. Faça com calma.

## Como gravar (diga à pessoa antes, se ainda for gravar)

- Uma pessoa principal, **grande no quadro**. O modelo desenha mal rostos pequenos.
- Câmera estável. Para **adicionar** algo, a câmera tem que ficar parada (a caixa de colocação é fixa na tela).
- Sem espelho, vidro ou outro reflexo da pessoa: o reflexo continua mostrando a pessoa original, e o modelo copia a roupa e o cabelo dele de volta.
- **Sem legenda queimada na imagem.** Ela cai dentro da área que o modelo refaz e fica embaralhada. Ponha a legenda depois, no vídeo final.
- Com fala, o áudio é o que guia a boca. Grave com áudio.
- Uma mão ou o braço cruzando a frente do corpo no meio do trecho ajuda muito: é onde se esconde a troca na montagem (ver `06-resultado.md`).

## Escolher o trecho

Veja o vídeo em quadros para achar o começo e o fim:

```
ffmpeg -i video.mp4 -vf "fps=4,scale=270:-1,tile=8x4" -frames:v 1 folha.jpg
```

Abra `folha.jpg`: são 32 quadros, 4 por segundo, na ordem de leitura (a linha de cima é o começo). Escolha o trecho e anote o segundo em que ele começa.

## Preparar

```
python "SCRIPTS/preparar_video.py" video.mp4 --inicio 6.25 --quadros 158 -o parte_a.mp4
```

O que ele garante, e por quê:

| Exigência do Openjutsu | O que o script faz |
|---|---|
| 24 quadros por segundo | Converte (vídeo de celular costuma ser 30, às vezes variável) |
| Exatamente 17×k + 5 quadros | Corta no número certo. Assim o trecho vira **um clipe só** |
| Áudio do tamanho do vídeo ou maior | Completa com silêncio. Áudio menor faz a montagem final falhar com `H3 Source Timeline audio window 0:158 exceeds 0:157` |
| Todo vídeo precisa de uma trilha de áudio | Se não tiver, põe um silêncio (sem trilha, o ComfyUI dá `VHS failed to extract audio`) |
| Lado menor até 720 px | Reduz (o Openjutsu trabalha em uns 736 px; mais só gasta envio) |

Números válidos de quadros e o que custam na RTX 4090 (medido em 01/11/2026 em três deles; o resto segue a mesma proporção, uns 2,5 a 2,7 segundos de GPU por quadro):

| Quadros | Segundos | GPU |
|---|---|---|
| 22 | 0,9 | |
| 39 | 1,6 | |
| **56** | 2,3 | **2,5 min** |
| **73** | 3,0 | **3 min** |
| 90 | 3,75 | |
| 107 | 4,5 | |
| 124 | 5,2 | |
| 141 | 5,9 | |
| **158** | 6,6 | **7 min** |

Para a primeira vez, fique em **56 a 158 quadros**. Trechos mais longos o Openjutsu emenda em vários clipes, mas não testamos. O `preparar_video.py` imprime o `--clip` que você vai usar no passo seguinte (por exemplo `--clip 6.603`).

Sem `--quadros`, ele usa o maior número válido que cabe, no máximo 158. `--duracao 3` pede "uns 3 segundos" e ele escolhe o válido de baixo.

Depois, mande para a máquina:

```
python "SCRIPTS/remoto.py" enviar parte_a.mp4
python "SCRIPTS/remoto.py" enviar ref_roupa.png
```

(vão para `/root/trabalho/`).

## A foto de referência

Todos os textos que vão para a IA (`--alvo`, `--sam`, `--para`, `--desc`, os pedidos de imagem) funcionam melhor **em inglês**.

### Roupa, cenário e adicionar: o que entra no vídeo

O vídeo gerado copia **só a roupa** (ou **só o cenário**, ou **só o personagem**) da imagem. O rosto, a boca, as mãos e o áudio continuam os do vídeo real. Por isso a melhor referência é:

> **um quadro do próprio vídeo, no mesmo enquadramento, editado por um gerador de imagens** para mudar só aquilo.

Passos:

1. Tire um quadro do trecho (`ffmpeg -ss 7 -i video.mp4 -frames:v 1 quadro.png`).
2. Mande o quadro a um gerador ou editor de imagens (o que a pessoa tiver: ChatGPT, Gemini, Canva...) com um pedido como estes:

**Roupa**

> Keep the [man/woman]'s face, hair, skin, expression, hands, pose, the camera framing and the whole room EXACTLY the same as the attached photo. Change ONLY [his/her] clothes: remove [the current clothes] and dress [him/her] in [new clothes, with colors, materials and details]. Same light. Photorealistic phone video frame. No text, no logo.

**Cenário**

> Keep the person EXACTLY the same as in the attached photo: same face, hair, skin, expression, pose, hands, same clothes, same camera framing. Replace ONLY the room behind them with [new place, with colors, materials and light]. Believable depth of field, like a real phone video. Photorealistic. No readable text, no letters, no people in the background.

**Adicionar um personagem** (foi o que funcionou): mande o quadro **sem o personagem** e a imagem do personagem, e peça para colocá-lo na cena (por exemplo, em cima da mesa), no tamanho certo, com sombra, sem mudar mais nada. Esse resultado é a `--foto`.

3. Confira a imagem antes de gastar GPU: cor certa (peça "vermelho, não laranja" se for o caso), mesma câmera, sem letras inventadas.

### Trocar a pessoa: o rosto vem da foto

Aqui o rosto **vem da referência**. Então:

- Use **2 a 3 quadros reais** do rosto (de frente e de três quartos, sem legenda), nunca uma imagem feita por IA. Em um teste, a saída ficou muito fiel à foto (semelhança de 0,77), mas a foto, feita por IA, parecia com o rosto real só 0,53: o modelo trocou a pessoa por um "parente" dela.
- Pode ser uma folha com 2 ou 3 fotos lado a lado, mais a roupa. O `relay.py` aceita isso.
- Só com o sim da pessoa da foto.
