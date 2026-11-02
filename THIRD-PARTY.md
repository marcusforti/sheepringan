# Créditos e licenças de terceiros

O Sheepringan é só a "cola": ele ensina e automatiza o uso de projetos e modelos de outras pessoas. **Nada deles é copiado para este repositório**, com uma exceção: `objeto.py` e `trocar_pessoa.py` reescrevem em Python, para a API do ComfyUI, a lógica de `lib/object.ts` e `lib/simple.ts` do Openjutsu. Por isso a licença do Openjutsu (MIT) está reproduzida abaixo, como ela exige.

Tudo o mais é baixado, na máquina que você aluga, direto das fontes originais, e vale a licença de cada fonte. Licenças conferidas em 01/11/2026.

## Openjutsu (o motor): MIT, D3voz

Projeto: https://github.com/D3voz/openjutsu (versão usada: `7fe118b`, de 30/10/2026). Troca de personagem e de objetos em vídeo, com MiniMax H3, SAM 3.1 e Qwen3-VL, em cima do ComfyUI. Todo o crédito pelo fluxo de trabalho é dele.

```
MIT License

Copyright (c) 2026 D3voz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

O README do próprio Openjutsu avisa: "Model licences are separate" (as licenças dos modelos são separadas), e o recurso de corrigir rosto depende de peças com licença restrita (ver mais abaixo).

## Programas baixados na máquina alugada (nenhum é redistribuído aqui)

| Projeto | Licença | Para quê |
|---|---|---|
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | GPL-3.0 | O programa que roda os fluxos |
| [comfyui-h3-oneclick-swap](https://github.com/D3voz/comfyui-h3-oneclick-swap) | MIT | Os nós do Openjutsu (planos de troca, máscaras, cortes) |
| [ComfyUI-Fantastic-MiniMaxH3-PromptBuilder](https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder) | MIT | Edição de vídeo com máscara |
| [ComfyUI-MiniMaxH3-Context-Loop](https://github.com/ethanfel/ComfyUI-MiniMaxH3-Context-Loop) | GPL-3.0 | Encadeamento de clipes e montagem final |
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | GPL-3.0 | Máscaras |
| [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | GPL-3.0 | Leitura de vídeo |
| [h3-relay](https://github.com/akatz-ai/h3-relay) (só no perfil `relay`) | GPL-3.0 | Workflow de troca de personagem. O `relay.py` lê o arquivo `H3-Character-Swap.api.json` que vem dentro dele; ele não é copiado para cá |

## Modelos baixados na máquina alugada (nenhum é redistribuído aqui)

| Modelo | Licença | Observação |
|---|---|---|
| MiniMax H3 (`Comfy-Org/MiniMax-H3`, `Abiray/MiniMax-H3-GGUF`) | **MiniMax H3 Community License** | Ver a seção abaixo. É a que mais restringe |
| LoRA de troca de personagem (`akatz-ai/MiniMax-H3-Character-Swap-LoRA`) | MiniMax H3 Community License | Mesma licença do modelo |
| SAM 3.1 (`Comfy-Org/sam3.1`) | SAM License (da Meta) | Licença própria. Leia em https://huggingface.co/Comfy-Org/sam3.1 |
| Qwen3-VL 8B (`pxyllvr/qwen3vl_8b_int8_convrot`) e o codificador de texto Qwen3-VL 32B | Apache-2.0 | |
| LoRA DMAD (`Kijai/MiniMax-H3-experimental`) e LoRA Turbo (`lightx2v/Minimax-h3-Turbo`) | não declarada no cartão do modelo | Confira com os autores antes de uso comercial |

### A licença do MiniMax H3: o que ela diz (lida em 01/11/2026)

Texto completo: https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE. Pontos que mudam o que você pode fazer:

- **Território.** A licença só vale fora da União Europeia, do Reino Unido, da República da Coreia e dos Estados Unidos. Usar o modelo ou **o resultado** nesses lugares "não é autorizado" (seção V, item 4; política de uso, item 1). Quem estiver lá precisa pedir licença à MiniMax. Por isso o `vast.py ofertas` nunca mostra máquinas nesses países.
- **Aviso de IA.** A política de uso proíbe publicar conteúdo gerado sem "avisar de forma clara e visível" que foi gerado por máquina (item 12).
- **Se passar por alguém.** É proibido imitar uma pessoa sem o consentimento dela (item 13). Também são proibidos: informação falsa para prejudicar ou influenciar eleições, engajamento falso, difamação e assédio, uso que prejudique menores, e prática profissional sem autorização.
- **Uso comercial.** Permitido. Acima de US$ 20 milhões de receita anual com produtos e serviços que usem o modelo, é preciso autorização escrita da MiniMax. Produto ou serviço comercial que use o modelo deve mostrar "MiniMax H3" na interface (seção IV).
- **Incentivado** (não obrigatório): mostrar "Powered by MiniMax H3" e marcar os arquivos gerados como feitos por IA.

Isto é um resumo de leitura, não aconselhamento jurídico. Em caso de dúvida, leia o texto original.

### Corrigir rosto (não usado por esta skill)

O recurso "Fix faces" do Openjutsu usa o InsightFace `buffalo_l`, licenciado **só para pesquisa, sem uso comercial**, e pesos YOLO do Bingsu/adetailer sob **AGPL-3.0**. Esta skill não instala nem usa essas peças. Quem for usar a interface web do Openjutsu para isso deve checar a licença antes de qualquer entrega paga.

## No seu computador

| Programa | Licença | Para quê |
|---|---|---|
| [vastai](https://github.com/vast-ai/vast-cli) (a ferramenta da Vast) | MIT | Alugar e apagar máquinas |
| [FFmpeg](https://ffmpeg.org/) | LGPL/GPL (conforme a compilação) | Preparar e montar o vídeo. É chamado como programa externo |
| OpenSSH | BSD | Falar com a máquina alugada |

## Sem vínculo

O Sheepringan é um projeto independente. Não tem ligação com o Openjutsu, a D3voz, a MiniMax, a Meta, a Vast.ai, o ComfyUI ou os autores dos outros projetos acima, e eles não o endossam. Os nomes são deles.
