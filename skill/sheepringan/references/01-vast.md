# 1. Conta, crédito e chaves

Faça uma etapa por vez. Antes de começar, conte em poucas linhas o que vai acontecer:

> Para esse vídeo precisamos de uma placa de vídeo forte, e o seu computador não tem. Vamos alugar uma, por hora, numa loja chamada Vast.ai. Cada hora custa uns 40 a 50 centavos de dólar. Hoje vamos só deixar a sua conta pronta; nada será alugado sem você dizer sim.

## 0. O que o computador precisa ter

| O quê | Como conferir | Como instalar |
|---|---|---|
| Python 3.9 ou mais novo | `python --version` (Mac e Linux: `python3 --version`) | python.org |
| Ferramenta da Vast | `vastai --version` | `pip install vastai` (depois feche e abra o terminal) |
| ffmpeg | `ffmpeg -version` | Windows: `winget install Gyan.FFmpeg`. Mac: `brew install ffmpeg`. Linux: `sudo apt install ffmpeg` |
| SSH e SCP | `ssh -V` | Já vêm no Mac e no Linux. No Windows 10 e 11: Configurações > Aplicativos > Recursos opcionais > Cliente OpenSSH |

No Windows, o `vast.py` já liga o modo UTF-8 sozinho. Se você usar o `vastai` direto no terminal e aparecer o erro `'charmap' codec can't encode`, rode antes `set PYTHONUTF8=1` (cmd) ou `$env:PYTHONUTF8=1` (PowerShell).

## 1. Conta na Vast.ai

1. Entrar em https://cloud.vast.ai/ e criar a conta. Confirmar o e-mail.
2. **Crédito:** menu Billing > Add Credit. O mínimo é US$ 5. Aceita cartão, BitPay ou Crypto.com.

Quanto colocar: nas duas sessões reais que medimos, o total foi de US$ 0,44 e US$ 5,32 (juntas, uns US$ 5,75). A maior parte da diferença foi o preço do download dos modelos (ver `02-maquina.md`); o resto foi uma máquina que ficou ligada 3 horas, boa parte esperando. US$ 5 a US$ 10 cobrem a primeira vez com folga.

Avise a pessoa: **se o crédito acabar, a Vast para a máquina** (e, se o saldo continuar negativo, pode apagá-la com tudo que estiver dentro). Por isso os resultados devem ser baixados logo que ficarem prontos.

## 2. Chave da API (a senha que deixa a ferramenta falar com a conta)

1. Abrir https://cloud.vast.ai/manage-keys/ e clicar em **+New**.
2. **A pessoa** copia a chave, abre uma janela normal do terminal (PowerShell no Windows, Terminal no Mac), cola `vastai set api-key COLE_A_CHAVE_AQUI` e aperta Enter. Não use o chat nem o `!` do Claude Code: eles mostram a chave para o agente.

Não peça a chave no chat. Se ela colar aqui sem querer, diga para apagar essa chave na mesma página e criar outra.

## 3. Chave SSH (o jeito seguro de controlar a máquina de longe)

```
python "SCRIPTS/vast.py" conta --criar-chave --registrar-chave
```

Isso cria a chave em `~/.ssh/vast_ed25519` (a parte secreta nunca sai do computador) e cadastra a parte pública na conta da Vast. Se preferir à mão: cole o conteúdo do arquivo `vast_ed25519.pub` em https://cloud.vast.ai/manage-keys/.

## 4. Conferir

```
python "SCRIPTS/vast.py" conta
```

Tem que terminar com `PRONTO`. Ele mostra o crédito, se a chave SSH está na conta e se já existe alguma máquina alugada cobrando. Nunca imprime chave nem e-mail.

Se aparecer `ATENCAO: ja existe(m) ... maquina(s) alugada(s)`, mostre a lista: pode ser uma esquecida (está cobrando agora) ou de outro projeto da pessoa. Não apague sem ela confirmar.
