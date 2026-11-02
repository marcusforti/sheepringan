# 5. Rodar cada modo

Todos rodam na máquina alugada, em segundo plano, e você acompanha. O jeito de rodar é sempre o mesmo:

1. Escreva o comando num arquivo `.sh` no computador da pessoa (use a ferramenta de escrever arquivos: nada de brigar com aspas).
2. Rode, dando um nome ao trabalho, e espere:

```
python "SCRIPTS/remoto.py" fundo roupa "@roupa.sh"
python "SCRIPTS/remoto.py" espera roupa --max 9
```

Os arquivos que você mandou com `enviar` estão em `/root/trabalho/`. Os programas estão em `/root/sheepringan/`.

Saída esperada do `objeto.py`: `ENVIADO ...`, depois (minutos depois) `STATUS success True 420 s` e `RUN edit_xxxxxxxxxx`. Se aparecer `ERRO_EXEC`, o motivo vem junto (ver `problemas.md`). Guarde o nome do `RUN`: ele serve para achar o resultado se a montagem final falhar.

Quando acabar: `python "SCRIPTS/resultado.py" roupa --saida saida` (`06-resultado.md`).

Sobre o gasto: um trecho de 6,6 s leva uns 7 minutos de GPU, uns 5 centavos de dólar. O que pesa na conta é instalar e deixar a máquina parada esperando.

## Os parâmetros do `objeto.py`

| Parâmetro | O que é |
|---|---|
| `--modo` | `change` (roupa ou objeto), `background` (cenário), `add` (adicionar) ou `remove` (remover) |
| `--video` | O trecho preparado (`preparar_video.py`), em `/root/trabalho/` |
| `--foto` | A imagem de referência. Não use no `remove` |
| `--rotulo` | O nome do resultado. Use o mesmo no `resultado.py` |
| `--alvo` | `change`: o que pegar da foto (`top`, `jacket`...). `background`: o que fica (`person`). `add`: onde vai (`on the wooden table`). `remove`: o que sai |
| `--sam` | Como o programa acha a coisa **no vídeo**: uma ou duas palavras curtas em inglês (`hoodie`). Se não pôr, usa o `--alvo` |
| `--para` | No que vira. Em `add`, não comece com "add" |
| `--desc` | Uma frase em inglês descrevendo o que está na foto. Fixa a descrição; sem ela o programa descreve sozinho e às vezes descreve a camada errada |
| `--margem` | Pixels de folga em volta da área refeita: 10 justo, 20 normal, 40 folgado |
| `--clip` | Segundos do trecho: copie o valor que o `preparar_video.py` imprimiu |
| `--seed` | Muda para sair outro resultado. Rodar de novo com tudo igual continua do último clipe pronto |
| `--resolucao` | `736p` (padrão). `1080p` é uns 2,5 vezes mais lento e pede muito mais memória (não testado) |
| `--sem-contorno` | Só `change`: não manda o contorno antigo. Troca a silhueta, mas perde o guia das mãos e dos braços |
| `--todos` | Mantém **todas** as ocorrências que o `--sam` achar, em vez de só a maior. Para vários alvos, separados por vírgula (`"t-shirt, arms"`). Opção nova: **não testada** na GPU |
| `--caixa x,y,largura,altura` | Só `add`: onde o objeto aparece, em fração da tela (0 a 1). Tem que caber o personagem, os gestos e a sombra |
| `--acao` | Só `add`: o que o objeto ou personagem faz, em inglês |

Por padrão o script mantém só a maior ocorrência do que o `--sam` achar (uma coisa por vez). Para trocar várias de uma vez, veja `--todos` acima.

## Trocar roupa ou objeto (`change`) — testado, ótimo

`roupa.sh`:

```bash
python /root/sheepringan/objeto.py --modo change \
  --video /root/trabalho/parte_a.mp4 --foto /root/trabalho/ref_roupa.png --rotulo roupa \
  --alvo top --sam hoodie \
  --para "a fitted bright red denim jacket worn open over a plain black t-shirt" \
  --desc "A fitted bright red denim jacket with contrast stitching, a pointed collar, chest pockets and metal buttons, worn open over a plain black crew-neck t-shirt." \
  --margem 20 --clip 6.603
```

Por que `--alvo top` e `--sam hoodie`: o `--sam` acha o moletom **no vídeo**; o `--alvo` diz ao programa o que copiar **da foto** (a jaqueta nova está na foto como "top"). Se pusesse `--alvo hoodie`, ele procuraria um moletom na foto da jaqueta.

Rosto, boca e mãos seguem o vídeo real e o áudio é o original. O contorno antigo é mantido (uma regata trocada por camisa de flanela continua sem manga).

## Trocar o cenário (`background`) — testado, ótimo (trecho de 2,3 s)

`cenario.sh`:

```bash
python /root/sheepringan/objeto.py --modo background \
  --video /root/trabalho/parte_b.mp4 --foto /root/trabalho/ref_cenario.png --rotulo cenario \
  --alvo person --sam person \
  --para "a modern dark office with black walls and red neon light" \
  --desc "A modern dark office with matte black walls, a large glowing red neon ring on the wall, a black desk with two monitors showing red and white code, thin red LED lines on the ceiling, moody light with red accents." \
  --margem 10 --clip 2.353
```

A pessoa fica; o resto vira cinza e é refeito, mantendo o movimento da câmera. Testamos com 2,3 s (56 quadros).

## Adicionar um objeto ou personagem (`add`) — testado uma vez, funcionou

Receita que funcionou (01/11/2026): a referência é um quadro do próprio vídeo **sem o personagem**, mais a imagem do personagem, juntos por um gerador de imagens (ver `04-video.md`).

`adicionar.sh`:

```bash
python /root/sheepringan/objeto.py --modo add \
  --video /root/trabalho/parte_c.mp4 --foto /root/trabalho/ref_mesa.png --rotulo mesa \
  --alvo "on the wooden table" \
  --para "a tiny living 3D cyborg sheep character" \
  --desc "<descrição física do personagem, em uma frase>" \
  --margem 2 --clip 3.062 \
  --caixa 0.30,0.41,0.37,0.33 \
  --acao "She stands on the table, looks up at the camera, waves one robotic hand hello and smiles"
```

Resultado do teste: clipe de 73 quadros (3 s), uns 3 minutos de GPU, com sombra de contato e o aceno gerados, e o personagem **atrás** da mão real. A caixa (`--caixa`) é fixa na tela, então a câmera tem que estar parada, e ela precisa ser grande o bastante para o personagem, o gesto e a sombra.

Truque de montagem: entre no clipe gerado quando a mão real já saiu da caixa, com um flash branco curto (`06-resultado.md`).

É um teste só. Trate como "funcionou uma vez", não como garantido.

## Remover (`remove`) — NÃO testado

O comando existe e monta o fluxo certo, mas nenhum teste foi feito na GPU. Não prometa resultado.

```bash
python /root/sheepringan/objeto.py --modo remove \
  --video /root/trabalho/parte_a.mp4 --rotulo limpo \
  --alvo backpack --sam backpack --para "a plain wall" --margem 20 --clip 2.353
```

Sem `--foto`. O `--para` só é preciso quando não é óbvio o que aparece no lugar.

Ideia que pode bastar para um **objeto pequeno que aparece por menos de 1 segundo** e não custa GPU: pintar quadro a quadro no próprio computador com OpenCV (`cv2.inpaint`), sobre uma máscara do objeto feita por cor. Num teste com um personagem pequeno numa tela, a máscara foi feita por cor, a área ao redor foi preenchida com `cv2.inpaint` e a mão real, que cobria parte do objeto, entrou na máscara como área "desconhecida" e ficou intacta. É específico de cada vídeo; use como ideia, não como receita pronta.

## Dois efeitos seguidos (roupa e depois cenário)

Rode o segundo **em cima do resultado do primeiro**, para os dois efeitos ficarem juntos:

1. Rode a roupa e baixe o resultado.
2. Corte os últimos 56 quadros desse resultado (se ele tem 158 quadros, comece em (158 − 56) ÷ 24 = 4,25 s): `python "SCRIPTS/preparar_video.py" roupa_pronta.mp4 --inicio 4.25 --quadros 56 -o parte_b.mp4`.
3. Rode o cenário nesse trecho.
4. Na montagem, o segundo clipe começa, no tempo do original, em `início da roupa + duração da roupa − duração do cenário`.

Exemplo: roupa começa em 6,25 s e dura 6,583 s; cenário dura 2,333 s; então o cenário começa em 6,25 + 6,583 − 2,333 = 10,5 s do original (`--parte cenario.mp4@10.5`).

## Trocar a pessoa — dois jeitos

Quem entra é a pessoa da foto; quem sai é a pessoa **maior** do quadro. As outras ficam como estão. Em todos: só com o sim da pessoa da foto.

### Simples: `trocar_pessoa.py` (perfil `basico`) — testado (1 vídeo com pessoa e 3 com um mascote)

```bash
python /root/sheepringan/trocar_pessoa.py \
  --video /root/trabalho/fonte.mp4 --foto /root/trabalho/pessoa.png --rotulo troca \
  --papel "the speaker"
```

`--papel` nomeia quem sai **pelo papel, nunca pela roupa** (palavra de roupa vaza para o resultado). `--sam` muda o que é trocado (`person` é o padrão; pode ser um animal, como `cat`). `--clip 6` é o padrão. Resultado em `h3_oneclick_swap`.

O que medimos: roupa, tatuagem e movimento saem bem, mas o rosto sai parecido, não idêntico (o resultado ficou fiel à foto, mas a foto era de IA). A pele sai mais nítida e mais pálida que a do original.

### Relay: `relay.py` (perfil `relay`) — testado

Usa o workflow do projeto h3-relay com a LoRA de troca de personagem. Foi o fluxo dos testes de semelhança de rosto abaixo, com uma folha de fotos reais. Os dois jeitos não foram comparados lado a lado, então não dá para dizer qual é melhor.

```bash
python /root/sheepringan/relay.py \
  --video /root/trabalho/fonte.mp4 --ref /root/trabalho/folha.png --rotulo troca2 \
  --prompt "Replace the selected person in <Video 1> with the character in <Picture 1>. Male, [traços], the exact same man shown in the face photos of <Picture 1>, wearing [roupa] shown in the lower part of <Picture 1>. Keep his exact face and identity. Follow the source performance's pose, gaze, expression, eyebrows, mouth movement and gestures. Preserve the scene. Do not show the reference sheet."
```

Resultado em `/root/ComfyUI/output/relay/`. Semelhança do rosto medida com SFace (acima de 0,363 conta como a mesma pessoa): **0,92 quando a pessoa entra no próprio vídeo e 0,68 quando entra no vídeo de outro ator**.

Cuidados: vídeos de 12 s estouraram a memória da placa duas vezes, mesmo com `--mem 13` e o ComfyUI reiniciado com `--reserve-vram 3`. Fique em até uns 6 s (os testes bons tinham 5,9 s).

### Personagem que não é humano — funciona em parte

O boneco cinza que guia o movimento tem forma humana. Em três testes com um mascote (uma ovelha), o modelo vestiu a jaqueta e as mãos, mas a cabeça saiu humana, com a lã no lugar do cabelo. Com o relay e a LoRA o resultado também foi só em parte. Não mostre esses resultados como "o personagem" sem avisar.

## O que não foi testado nem tem script aqui

Várias pessoas ao mesmo tempo, "From picture" (o FLUX monta o primeiro quadro), relight (mudar a luz) e corrigir rosto existem no Openjutsu (na interface web dele), mas **não foram testados** e **não têm script nesta skill**. O corrigir rosto usa o InsightFace `buffalo_l`, que só vale para pesquisa, sem uso comercial (ver `THIRD-PARTY.md`).
