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
| `--clip` | Segundos de cada clipe: copie o valor que o `preparar_video.py` imprimiu. Até 158 quadros vira um clipe só; trecho mais longo usa `--clip 6` e o Openjutsu emenda vários clipes |
| `--seed` | Muda para sair outro resultado. Rodar de novo com tudo igual continua do último clipe pronto |
| `--resolucao` | `736p` (padrão). `1080p` é uns 2,5 vezes mais lento e pede muito mais memória (não testado) |
| `--sem-contorno` | Só `change`: não manda o contorno antigo. Troca a silhueta, mas perde o guia das mãos e dos braços |
| `--todos` | Mantém **todas** as ocorrências que o `--sam` achar, em vez de só a maior. Necessário com vários alvos separados por vírgula (`--alvo "t-shirt, arms" --sam "t-shirt, arm"`). Testado em 02/11/2026 |
| `--caixa x,y,largura,altura` | Só `add`: onde o objeto aparece, em fração da tela (0 a 1). Tem que caber o personagem, os gestos e a sombra. Com a câmera em movimento, a caixa tem que cobrir **todo o trajeto** do objeto na tela |
| `--acao` | Só `add`: o que o objeto ou personagem faz, em inglês |

Por padrão o script mantém só a maior ocorrência do que o `--sam` achar (uma coisa por vez). Sem `--todos`, num pedido de camiseta e braços, só ficaria a maior das duas.

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

### Roupa que cobre o tronco e os braços — testado, funcionou

Para trocar a camiseta e as mangas de uma vez, nomeie as duas coisas e ligue o `--todos` (sem ele só a maior ficaria):

```bash
python /root/sheepringan/objeto.py --modo change --todos \
  --video /root/trabalho/parte_a.mp4 --foto /root/trabalho/ref_roupa.png --rotulo roupa2 \
  --alvo "t-shirt, arms" --sam "t-shirt, arm" \
  --para "<a roupa nova, com mangas>" \
  --desc "<a roupa nova, em uma frase, com cor, material e detalhes>" \
  --margem 20 --clip 6.603
```

Testado com 158 quadros: 7 minutos de GPU. **Defeito visto:** a manga do braço mais perto da câmera saiu com a tatuagem aparecendo, porque a referência tinha a tatuagem. **O que estiver errado na referência costuma ir para o vídeo.** Confira a imagem com calma antes de gastar GPU (`04-video.md`).

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

## Adicionar um objeto ou personagem (`add`) — testado 3 vezes, funcionou (com um defeito)

A referência é um quadro do próprio vídeo **sem o personagem ou o objeto**, mais a imagem dele, juntos por um gerador de imagens (ver `04-video.md`). Esse resultado é a `--foto`.

`adicionar.sh` (personagem em cima de uma mesa):

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

A `--caixa` precisa ser grande o bastante para o personagem, o gesto e a sombra. O que se viu em cada teste (01 e 02/11/2026, RTX 4090):

| Teste | Trecho | GPU | Resultado |
|---|---|---|---|
| Personagem em cima da mesa, acenando | 73 quadros (3 s), 1 clipe | uns 3 min | Sombra de contato e aceno gerados; o personagem ficou **atrás** da mão real |
| Objeto **parado** com a **câmera em movimento** (uma moto numa sala) | 260 quadros, `--clip 6`, 3 clipes | 11,5 min | Funcionou com uma caixa grande cobrindo todo o trajeto do objeto na tela (`--caixa 0.0,0.12,1.0,0.62`) e o `--acao` dizendo que ele fica parado no mesmo ponto do chão. **Defeito:** por cerca de 1 s apareceu uma segunda moto pequena ao fundo |
| Personagem que **sai de um lugar e sobe na mão real**, falando | 226 quadros, `--clip 6`, 2 clipes | 8,8 min | A mão real ficou preservada dentro da caixa e a boca mexeu de verdade, em sincronia |

Para o personagem **falar**: ponha a voz dele no áudio do trecho (só a voz do personagem, sem a de quem filma) antes de preparar o vídeo, e peça no `--acao` que a boca acompanhe o áudio, em inglês (por exemplo, "its mouth moves in sync with the audio while it speaks"). Para trocar o áudio do vídeo pela voz do personagem (o vídeo não é recodificado; se a voz for mais curta, o `preparar_video.py` completa com silêncio):

```
ffmpeg -i take.mp4 -i voz.mp3 -map 0:v -map 1:a -c:v copy -c:a aac take_com_voz.mp4
```

No vídeo final, o áudio que vale é o do arquivo `--original` do `montar.py`: se o personagem fala, monte com um original que já leve a voz dele (o `take_com_voz.mp4`).

Para o **defeito do objeto repetido** ao fundo: na montagem, corte o trecho em que ele aparece, ou rode de novo com outro `--seed` (uma sugestão, sem teste).

Truque de montagem: entre no clipe gerado quando a mão real já saiu da caixa, com um flash branco curto (`06-resultado.md`).

São poucos testes. Trate como "funcionou nesses casos", não como garantido. Não foi testado: mais de um objeto na mesma cena e objeto que se move pelo cenário (a caixa é fixa; só o caso do objeto parado com a câmera em movimento foi testado).

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
