# Problemas conhecidos

Cada linha: o que aparece, a causa e o que fazer. Os erros em inglês vêm do próprio Openjutsu, do ComfyUI ou da Vast.

## No computador da pessoa

| O que aparece | Causa | O que fazer |
|---|---|---|
| `'charmap' codec can't encode characters` ao usar `vastai` no Windows | A ferramenta imprime letras que o terminal do Windows não conhece | Os scripts da skill já resolvem. À mão, rode antes `set PYTHONUTF8=1` (cmd) ou `$env:PYTHONUTF8=1` (PowerShell) |
| `vastai` não é reconhecido depois de `pip install vastai` | O terminal não enxergou a pasta nova | Feche e abra o terminal. Se continuar, ache a pasta Scripts do Python (`python -m pip show -f vastai`) e ponha no PATH |
| `show invoices` aparece como obsoleto, e `show invoices-v1 --start-date 2026-11-01` quebra com `TypeError` | A versão 1.8 da ferramenta só aceita bem datas como número quando falta a data final | Use `python "SCRIPTS/vast.py" gastos`: ele já manda as duas datas como número |
| `Nao achei o programa 'ssh'` (ou `scp`) | O Windows 10/11 vem com o cliente OpenSSH desligado | Configurações > Aplicativos > Recursos opcionais > Cliente OpenSSH |
| `Bad configuration option: StrictHostKeyChecking=accept-new` | OpenSSH velho (antes da 7.6) | Atualize o Windows ou o OpenSSH |
| `Permission denied (publickey)` logo depois de alugar | A chave SSH não estava na conta quando a máquina nasceu | `python "SCRIPTS/vast.py" conta --registrar-chave` e depois `vastai attach ssh ID "CONTEUDO_DA_CHAVE_PUBLICA"` |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | A Vast reaproveita endereços de máquinas antigas | Os scripts usam um arquivo próprio de hosts e o limpam a cada aluguel. À mão: `ssh-keygen -R "[IP]:PORTA"` |
| `ffmpeg`/`ffprobe` não encontrado | Falta instalar | Windows: `winget install Gyan.FFmpeg`. Mac: `brew install ffmpeg` |

## Na hora de alugar e instalar

| O que aparece | Causa | O que fazer |
|---|---|---|
| `Essa oferta nao esta mais disponivel` ou `O preco subiu` | Alguém alugou antes, ou o preço mudou | Rode `ofertas` de novo e peça o sim outra vez |
| A máquina não fica `running` em 15 minutos | A máquina está lenta para baixar a imagem, ou com defeito | `status`. Se não for ligar, apague e escolha outra oferta |
| `INSTALACAO_FALHOU: ... modelo(s) nao baixaram direito` | Queda de rede ou limite do site de modelos | Rode o instalador de novo: ele continua de onde parou |
| `INSTALACAO_FALHOU: o PyTorch nao enxerga a placa de video` | Driver antigo na máquina | Apague e escolha outra oferta (o filtro já pede CUDA 12.8 ou mais, mas pode haver exceções) |
| `INSTALACAO_FALHOU: pouco disco livre` | A máquina foi alugada com disco menor | Apague e alugue de novo com `--disco 140` (padrão) |
| `AVISO: so ... GB de memoria RAM` | Máquina com pouca RAM | O autor do Openjutsu testou com 64 GB. Pode dar erro de memória em trechos longos |
| Aviso `You need pytorch with cu130 or higher to use optimized CUDA operations` no log do ComfyUI | O ComfyUI prefere o CUDA 13 | É só um aviso: os testes de 01/11 rodaram assim, com o CUDA 12.8 |

## Na hora de rodar

| O que aparece | Causa | O que fazer |
|---|---|---|
| `ERRO_COMFY_FORA` | O ComfyUI está desligado | `remoto.py rodar "bash /root/sheepringan/instalar_maquina.sh --so-comfy" --tempo 600`. O log está em `/root/comfy.log` |
| `ERRO_PROMPT ... Value not in list` ou arquivo de modelo faltando | A instalação não terminou | `instalar_maquina.sh --conferir` e rode o instalador de novo |
| `sem no com o titulo: ...` | O Openjutsu mudou os nomes dos nós (versão mais nova que a testada) | Reinstale com as versões testadas (sem `--ultimas`) |
| `ERRO_EXEC` com `out of memory` | Trecho comprido demais para a placa | Encurte o trecho. No relay, 12 s estouraram duas vezes |
| `H3 Source Timeline audio window 0:158 exceeds 0:157` | O áudio era menor que o vídeo | Use o `preparar_video.py`. O clipe já foi gerado: `resultado.py ROTULO --run edit_xxxx` (`06-resultado.md`) |
| `VHS failed to extract audio ... Error opening output file -` | O vídeo não tem trilha de áudio | Use o `preparar_video.py` (põe um silêncio) |
| O programa fica esperando e nada acontece | Trabalho longo | `remoto.py log NOME`. Um trecho de 6,6 s leva uns 7 minutos |
| `STATUS success` mas não acho o arquivo | A montagem final falhou | `resultado.py ROTULO --run edit_xxxx` com o nome da linha `RUN` |

## No resultado

| O que se vê | Causa | O que fazer |
|---|---|---|
| Legenda embaralhada | Legenda queimada na imagem cai na área que o modelo refaz | Tire a legenda do vídeo de origem e ponha depois |
| A pessoa original aparece no espelho ou na janela | Reflexo: o modelo copia o look dela de volta | Grave sem reflexo |
| O rosto trocado é parecido, mas não idêntico | A foto de referência é feita por IA (parece 0,53 com o rosto real) | Use 2 a 3 quadros reais do rosto |
| Rosto sem expressão | O guia cinza de movimento vai sem rosto no fluxo simples | Hipótese ainda não testada: ligar o rosto no guia. Prefira roupa, cenário ou adicionar, que mantêm o rosto real |
| Pele dura e pálida | O modelo deixa a pele mais nítida e menos saturada (nitidez 51 contra 29 no original) | Na montagem, ajuste a cor; o "Fix colours" do Openjutsu existe, mas não foi testado |
| O personagem não humano vira uma pessoa | O guia de movimento tem forma humana | Ver `05-modos.md` |
| Roupa laranja em vez de vermelha | A foto de referência saiu com a cor errada | Refaça a foto pedindo a cor ("vermelho, não laranja") |

## Dinheiro

| O que aparece | Causa | O que fazer |
|---|---|---|
| A conta veio muito maior que a estimativa | Quase sempre o preço do download (`gastos` mostra a coluna `download`), ou a máquina ficou ligada | Compare com `ofertas` na próxima. Apague sempre no fim |
| A máquina aparece como `exited` | A Vast parou (crédito acabou, ou foi parada à mão) | Parada ainda cobra o disco. Baixe o que puder e apague |
| A máquina sumiu | Possível causa: crédito zerado por muito tempo | O que estava nela se perdeu. Alugue outra e instale de novo |
