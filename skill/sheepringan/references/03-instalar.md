# 3. Instalar na máquina alugada

A máquina chega vazia. Esta etapa instala o ComfyUI, o Openjutsu, os plugins e baixa os modelos. É a parte que mais demora (10 a 20 minutos) e a que mais gasta download.

Diga à pessoa:

> A máquina está baixando o "cérebro" da IA, uns 50 GB. Leva de 10 a 20 minutos e é a parte que mais custa. Depois disso, cada vídeo leva poucos minutos.

## 1. Mandar os programas para a máquina

```
python "SCRIPTS/remoto.py" subir
```

## 2. Escolher o perfil

| Perfil | Para quê | Baixa | Como pedir |
|---|---|---|---|
| `basico` (padrão) | Roupa ou objeto, cenário, adicionar, remover e trocar pessoa pelo `trocar_pessoa.py` | uns 47 GB de modelos (52 GB no total, medido) | `--perfil basico` |
| `relay` | Tudo do básico mais a troca de pessoa pelo `relay.py`, com a LoRA de troca de personagem | uns 70 GB de modelos (75 GB no total, estimado) | `--perfil relay` |

Na dúvida, `basico`. O `relay` dá para instalar depois, rodando o instalador de novo com `--perfil relay`: ele só baixa o que falta.

## 3. Instalar (em segundo plano)

```
python "SCRIPTS/remoto.py" fundo instalar "bash /root/sheepringan/instalar_maquina.sh --perfil basico"
python "SCRIPTS/remoto.py" espera instalar --max 8
```

O `espera` volta depois de até 8 minutos. Se ainda não acabou, ele diz `ainda esta rodando`: chame de novo. Dá para ver o andamento com `python "SCRIPTS/remoto.py" log instalar`. As linhas `[1/7]`, `[2/7]`... mostram a etapa, e `BAIXOU arquivo` aparece a cada modelo pronto.

Termina com:

- `INSTALACAO_FIM`: deu certo.
- `INSTALACAO_FALHOU: motivo`: leia o motivo. É seguro **rodar o mesmo comando de novo**: o instalador continua de onde parou (não baixa de novo o que já está inteiro).

## 4. O que o instalador faz

1. Programas do sistema (git, ffmpeg, aria2, tmux).
2. ComfyUI (versão testada em 01/11/2026).
3. Cinco plugins do ComfyUI que o Openjutsu usa: MiniMaxH3-Context-Loop, Fantastic-MiniMaxH3-PromptBuilder, KJNodes, VideoHelperSuite e comfyui-h3-oneclick-swap (mais o h3-relay no perfil `relay`).
4. Openjutsu (só os arquivos de workflow; a interface web dele não é usada).
5. PyTorch 2.11.0 com CUDA 12.8, a versão testada. A imagem da Vast costuma vir com uma bem mais velha (a de 01/11 tinha a 2.5.1); o instalador troca pela versão testada.
6. Os modelos, em paralelo, conferindo o tamanho de cada arquivo contra o do site de origem.
7. Liga o ComfyUI (só dentro da máquina, na porta 8188) e confere que os nós do Openjutsu existem.

As versões de cada projeto ficam fixas nas testadas em 01/11/2026. Com `--ultimas` ele usa as mais novas, o que pode quebrar (não testado).

## 5. Conferir

```
python "SCRIPTS/remoto.py" rodar "bash /root/sheepringan/instalar_maquina.sh --conferir"
```

Tem que terminar com `CONFERIDO_OK`. Se o ComfyUI estiver desligado (a máquina reiniciou, por exemplo):

```
python "SCRIPTS/remoto.py" rodar "bash /root/sheepringan/instalar_maquina.sh --so-comfy" --tempo 600
```

## Avisos

- A máquina já está cobrando durante a instalação. Se a pessoa precisar sair, é melhor esperar acabar do que deixar pela metade.
- Se a instalação falhar duas vezes seguidas pelo mesmo motivo, não insista: mostre o motivo à pessoa e veja `problemas.md`. Apagar e alugar outra máquina repete o download.
- Vídeos, fotos e resultados ficam na pasta `/root/trabalho` da máquina. Tudo isso some quando a máquina é apagada.
