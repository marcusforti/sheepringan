# 2. Escolher e alugar a máquina

Aqui se gasta dinheiro. Duas travas: o custo vem na mão antes, e o `--confirmo` só entra depois do sim da pessoa.

## O que importa na escolha

| Filtro | Por quê | O `ofertas` já faz |
|---|---|---|
| Placa RTX 4090 | É a única placa em que testamos. O autor do Openjutsu testou numa RTX 4060 Ti de 16 GB, mais lenta | sim (`--ampliar` aceita outras RTX 40 e 50, sem teste) |
| 16 GB ou mais de memória de vídeo | O modelo precisa | sim |
| RAM de 64 GB ou mais | Os modelos passam pela memória do computador; o autor do Openjutsu testou com 64 GB | sim (`--ram`) |
| Disco de 140 GB | Modelos (uns 47 GB) mais programas e vídeos | sim (`--disco`) |
| Confiável e verificada | Máquina ruim cai no meio do trabalho | sim |
| **Preço do download** (`inet_down_cost`) | Ver abaixo: é o que mais surpreende | sim, entra na conta |
| **Fora de UE, Reino Unido, Coreia do Sul e EUA** | A licença do modelo só vale fora desses lugares | sim, sempre |

### O preço do download decide a conta

A hora da GPU custa quase o mesmo em todo lugar, mas o download dos modelos (uns 52 GB só para instalar) é cobrado **por GB**, e esse preço varia mais de dez vezes de uma máquina para outra. Dois casos reais, de 01/11/2026:

| Máquina | Download | Preço por GB | Custo do download |
|---|---|---|---|
| 1 | 52,4 GB | US$ 0,003 | **US$ 0,14** |
| 2 | 95 GB | US$ 0,039 | **US$ 3,71** |

A segunda baixou menos de duas vezes mais dados (95 GB contra 52 GB), mas o download custou mais de 26 vezes mais, só por causa do preço por GB. No total, as duas sessões custaram US$ 0,44 e US$ 5,32; a segunda também ficou ligada 3 horas, boa parte esperando. Por isso o `ofertas` ordena pelo **custo total estimado**, e não pelo preço da hora.

Também vale lembrar: apagar a máquina e alugar outra **repete o download**. Escolha bem na primeira vez.

## Procurar

```
python "SCRIPTS/vast.py" ofertas
```

Opções que importam:

| Opção | Para quê |
|---|---|
| `--horas 3` | Quantas horas de uso você prevê (padrão 2: instalar, uns 3 trechos e a espera) |
| `--perfil relay` | Se vai usar a troca de pessoa pelo `relay` (baixa uns 23 GB a mais) |
| `--tipo interruptivel` | Preço menor, mas a Vast pode pausar a máquina quando alguém pagar mais |
| `--ampliar` | Aceita RTX 40 e 50 que não a 4090. Não testamos |
| `--json` | Resultado em dados, para você ler |

O `ofertas` mostra as 6 de menor custo estimado. **Custo estimado = horas × preço da hora + GB × preço do download.** Preço muda toda hora: é uma estimativa. Também diz quantos minutos a instalação leva naquela velocidade e quanto custaria por dia se a máquina fosse esquecida ligada.

### Fixa ou interruptível

| | Fixa (padrão) | Interruptível |
|---|---|---|
| Preço | cheio | bem menor (nas ofertas que vimos em 01/11/2026, de 8% a 56% menos) |
| Risco | nenhum | a Vast pode pausar a máquina a qualquer momento se alguém pagar mais; para voltar, pode ficar na fila |
| Quando usar | **a primeira vez e qualquer trabalho com prazo** | quem já sabe o que faz e aceita esperar |

## Pedir o sim

Mostre os números à pessoa com estas palavras (troque os valores):

> Achei uma máquina com placa RTX 4090 no país X. Ela custa US$ A por hora. Baixar os programas e modelos (uns 52 GB) custa cerca de US$ B, uma vez só. Para uma sessão de umas 2 horas, o total estimado é de US$ C. O seu crédito na Vast é de US$ D. Enquanto a máquina existir ela cobra, mesmo parada; eu vou apagar no fim e conferir. Posso alugar? Responda "sim".

Só continue com um "sim" claro. Se a pessoa hesitar, ofereça outra oferta mais barata ou menos tempo, ou pare.

## Alugar

```
python "SCRIPTS/vast.py" alugar OFERTA --confirmo
```

- O `alugar` só aceita ofertas da **última** busca `ofertas`. Antes de gastar, ele repete a busca com os mesmos filtros (inclusive o de país) e recusa se a oferta sumiu ou se o preço subiu mais de 10%. Nesse caso, rode `ofertas` de novo e peça o sim outra vez.
- No interruptível, ele sugere um lance 10% acima do mínimo; dá para escolher com `--lance`.
- Ele espera a máquina ligar (alguns minutos) e grava o endereço em `~/.sheepringan/maquina.json`. Depois:

```
python "SCRIPTS/remoto.py" testar
```

Tem que aparecer `MAQUINA_OK` e o nome da placa. Se der erro logo depois de alugar, espere um minuto e tente de novo: o SSH da máquina demora um pouco.

- Se a máquina não ficar `running` em 15 minutos, rode `status`. Se não for ligar, apague: `python "SCRIPTS/vast.py" destruir ID --confirmo`.
- Se der `Permission denied (publickey)` mesmo com a chave cadastrada, a chave pode ter sido cadastrada depois do aluguel: `vastai attach ssh ID "$(cat ~/.ssh/vast_ed25519.pub)"`.

A partir daqui a conta está correndo. Diga isso à pessoa, e que o próximo passo (instalar) é o que mais demora.
