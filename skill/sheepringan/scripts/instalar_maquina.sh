#!/bin/bash
# Roda DENTRO da maquina alugada (Linux, imagem vastai/pytorch).
# Instala o ComfyUI, o Openjutsu, os nos (plugins) e os modelos, e deixa o ComfyUI ligado.
#
# uso: bash instalar_maquina.sh [--perfil basico|relay] [--ultimas] [--simular] [--conferir] [--so-comfy]
#   --perfil basico   (padrao) modos roupa/objeto, cenario, adicionar, remover e trocar pessoa simples. ~52 GB
#   --perfil relay    o basico + troca de pessoa pelo workflow relay (h3-relay + LoRA). ~75 GB
#   --ultimas         usa a versao mais nova de cada projeto, em vez das versoes testadas em 01/11/2026
#   --simular         so mostra o que faria, sem instalar nada
#   --conferir        confere o que ja esta instalado e se o ComfyUI responde
#   --so-comfy        so (re)liga o ComfyUI
#
# Termina com a linha INSTALACAO_FIM. Se falhar, a ultima linha e INSTALACAO_FALHOU: motivo.

PERFIL=basico
ULTIMAS=0
SIMULAR=0
CONFERIR=0
SO_COMFY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --perfil) PERFIL="${2:-}"; shift 2 ;;
    --perfil=*) PERFIL="${1#*=}"; shift ;;
    --ultimas) ULTIMAS=1; shift ;;
    --simular) SIMULAR=1; shift ;;
    --conferir) CONFERIR=1; shift ;;
    --so-comfy) SO_COMFY=1; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Opcao desconhecida: $1"; exit 2 ;;
  esac
done
case "$PERFIL" in basico|relay) ;; *) echo "Perfil invalido: $PERFIL (use basico ou relay)"; exit 2 ;; esac

# Versoes testadas em 01/11/2026 (RTX 4090, imagem vastai/pytorch:latest, Python 3.10).
COMFYUI_URL=https://github.com/comfyanonymous/ComfyUI.git
COMFYUI_SHA=17ff1dcce963bd9f23095ec9b28febbfc4db8388
OPENJUTSU_URL=https://github.com/D3voz/openjutsu.git
OPENJUTSU_SHA=7fe118bb5a61fcfac0148e1bfea3dd29884dbf26
TORCH_VERSAO=2.11.0+cu128
TORCH_PIP="torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0"
TORCH_INDEX=https://download.pytorch.org/whl/cu128

# nome da pasta | repositorio | commit testado
NOS=(
  "ComfyUI-MiniMaxH3-Context-Loop|https://github.com/ethanfel/ComfyUI-MiniMaxH3-Context-Loop.git|43afeffcc570beb5f7382593e79e4b211c7e02f6"
  "ComfyUI-Fantastic-MiniMaxH3-PromptBuilder|https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder.git|22e719fe89336c628383363182a4da3cb58d4f9b"
  "ComfyUI-KJNodes|https://github.com/kijai/ComfyUI-KJNodes.git|ab72eda7ffad6280422d71ab7d54d3fb87c0ba18"
  "ComfyUI-VideoHelperSuite|https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git|4d907bee61e92c2e65af3bd6383a4e4d356126d1"
  "comfyui-h3-oneclick-swap|https://github.com/D3voz/comfyui-h3-oneclick-swap.git|e44a56e92920000e675d14be484aea0d7498d63e"
)
NOS_RELAY=(
  "h3-relay|https://github.com/akatz-ai/h3-relay.git|e2a7665b6eb8ea37a88c0de2c9c6b69a8f7c9220"
)

# pasta dentro de models | nome do arquivo | endereco
H=https://huggingface.co
MODELOS=(
  "diffusion_models|minimax_h3_ref2va_pruned_int8_convrot.safetensors|$H/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"
  "text_encoders|qwen3vl_32b_minimax_h3_int4_convrot.safetensors|$H/Abiray/MiniMax-H3-GGUF/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_int4_convrot.safetensors"
  "text_encoders|qwen3vl_8b_int8_convrot.safetensors|$H/pxyllvr/qwen3vl_8b_int8_convrot/resolve/main/qwen3vl_8b_int8_convrot.safetensors"
  "loras|minimax_h3_DMAD_4step_full_lora_avg_rank_39_bf16.safetensors|$H/Kijai/MiniMax-H3-experimental/resolve/main/loras/minimax_h3_DMAD_4step_full_lora_avg_rank_39_bf16.safetensors"
  "vae|minimax_h3_video_vae_int8_convrot.safetensors|$H/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot.safetensors"
  "vae|minimax_h3_audio_vae_fp32.safetensors|$H/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors"
  "checkpoints|sam3.1_multiplex_fp16.safetensors|$H/Comfy-Org/sam3.1/resolve/main/checkpoints/sam3.1_multiplex_fp16.safetensors"
)
MODELOS_RELAY=(
  "text_encoders|qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors|$H/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
  "vae|minimax_h3_video_vae_fp16.safetensors|$H/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors"
  "loras|minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors|$H/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
  "loras/h3-v2-challenge-eval-20261013|v2-1000.safetensors|$H/akatz-ai/MiniMax-H3-Character-Swap-LoRA/resolve/main/h3_character_swap_v1.5.safetensors"
)

RAIZ=/root
COMFY=$RAIZ/ComfyUI
M=$COMFY/models
ATIVAR='[ -f /venv/main/bin/activate ] && source /venv/main/bin/activate;'
export DEBIAN_FRONTEND=noninteractive PIP_BREAK_SYSTEM_PACKAGES=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

passo=0
TOTAL=7
[ "$PERFIL" = relay ] && TOTAL=8
etapa() { passo=$((passo + 1)); echo "[$passo/$TOTAL] $*"; }
falha() { echo "INSTALACAO_FALHOU: $*"; exit 1; }
run() {
  if [ "$SIMULAR" = 1 ]; then echo "+ $*"; return 0; fi
  "$@"
}

if [ "$SIMULAR" != 1 ] && [ -f /venv/main/bin/activate ]; then
  # shellcheck disable=SC1091
  source /venv/main/bin/activate
fi

lista_nos() { printf '%s\n' "${NOS[@]}"; [ "$PERFIL" = relay ] && printf '%s\n' "${NOS_RELAY[@]}"; return 0; }
lista_modelos() { printf '%s\n' "${MODELOS[@]}"; [ "$PERFIL" = relay ] && printf '%s\n' "${MODELOS_RELAY[@]}"; return 0; }

tamanho_remoto() {
  curl -sIL -A "Mozilla/5.0" --max-time 40 "$1" | tr -d '\r' | awk 'tolower($1)=="content-length:" {v=$2} END {print v}'
}

clonar() { # url pasta commit
  local url="$1" dir="$2" sha="$3"
  if [ "$SIMULAR" = 1 ]; then echo "  + baixar $url @ ${sha:0:10} -> $dir"; return 0; fi
  if [ -d "$dir/.git" ] && git -C "$dir" rev-parse HEAD >/dev/null 2>&1; then
    echo "  ja existe: $(basename "$dir")"
    return 0
  fi
  rm -rf "$dir"
  if [ "$ULTIMAS" != 1 ]; then
    mkdir -p "$dir" && git -C "$dir" init -q && git -C "$dir" remote add origin "$url" \
      && git -C "$dir" fetch -q --depth 1 origin "$sha" && git -C "$dir" checkout -q FETCH_HEAD && return 0
    echo "  AVISO: nao consegui a versao testada de $(basename "$dir"); usando a mais nova."
    rm -rf "$dir"
  fi
  git clone -q --depth 1 "$url" "$dir"
}

baixa_um() { # pasta nome url
  local dir="$M/$1" nome="$2" url="$3" esperado atual tentativa rc
  mkdir -p "$dir"
  esperado=$(tamanho_remoto "$url")
  for tentativa in 1 2 3; do
    atual=$(stat -c %s "$dir/$nome" 2>/dev/null || echo 0)
    if [ -n "$esperado" ] && [ "$atual" = "$esperado" ]; then
      echo "BAIXOU $nome ($((atual / 1048576)) MB)"
      return 0
    fi
    aria2c -q -c -x 16 -s 16 -k 20M --file-allocation=none --max-tries=10 --retry-wait=5       --allow-overwrite=true --auto-file-renaming=false -d "$dir" -o "$nome" "$url"
    rc=$?
    atual=$(stat -c %s "$dir/$nome" 2>/dev/null || echo 0)
    if [ -n "$esperado" ]; then
      if [ "$atual" = "$esperado" ]; then echo "BAIXOU $nome ($((atual / 1048576)) MB)"; return 0; fi
    elif [ "$rc" = 0 ] && [ "$atual" -gt 1000000 ]; then
      echo "BAIXOU $nome ($((atual / 1048576)) MB, tamanho esperado nao confirmado)"
      return 0
    fi
  done
  echo "FALHOU_DOWNLOAD $nome (tem ${atual:-0} bytes, esperava ${esperado:-?})"
  return 1
}

comfy_no_ar() { curl -s -m 5 http://127.0.0.1:8188/system_stats >/dev/null 2>&1; }

iniciar_comfy() {
  if [ "$SIMULAR" = 1 ]; then
    echo "+ tmux new-session -d -s comfy (ComfyUI com PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True e --reserve-vram 3, so em 127.0.0.1:8188)"
    return 0
  fi
  tmux kill-session -t comfy 2>/dev/null
  sleep 2
  tmux new-session -d -s comfy "$ATIVAR cd $COMFY && PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python main.py --listen 127.0.0.1 --port 8188 --reserve-vram 3 > $RAIZ/comfy.log 2>&1"
  local i
  for i in $(seq 1 90); do
    comfy_no_ar && return 0
    sleep 4
  done
  return 1
}

checar_nos() {
  python - <<'PY'
import json, sys, urllib.request
precisa = ["H3ObjectSwapPlan", "H3OneClickSwapPlan", "MiniMaxH3ChainAssemble", "MiniMaxH3FantasticVideoEditLatent", "VHS_LoadVideo", "GrowMaskWithBlur", "SAM3_VideoTrack"]
faltam = []
for nome in precisa:
    try:
        d = json.load(urllib.request.urlopen("http://127.0.0.1:8188/object_info/" + nome, timeout=20))
    except Exception:
        d = {}
    if nome not in d:
        faltam.append(nome)
print("NOS_FALTANDO " + ",".join(faltam) if faltam else "NOS_OK")
sys.exit(1 if faltam else 0)
PY
}

# Para os testes: carrega so as funcoes, sem instalar nada.
if [ "${SHEEPRINGAN_SO_FUNCOES:-0}" = 1 ]; then return 0 2>/dev/null || exit 0; fi

if [ "$CONFERIR" = 1 ]; then
  rc=0
  echo "Perfil: $PERFIL"
  while IFS='|' read -r pasta nome url; do
    [ -z "$pasta" ] && continue
    esperado=$(tamanho_remoto "$url")
    atual=$(stat -c %s "$M/$pasta/$nome" 2>/dev/null || echo 0)
    if [ "$atual" = "0" ]; then echo "FALTA  $pasta/$nome"; rc=1
    elif [ -n "$esperado" ] && [ "$atual" != "$esperado" ]; then echo "INCOMPLETO  $pasta/$nome ($atual de $esperado bytes)"; rc=1
    else echo "ok     $pasta/$nome"; fi
  done < <(lista_modelos)
  while IFS='|' read -r nome url sha; do
    [ -z "$nome" ] && continue
    if [ -d "$COMFY/custom_nodes/$nome/.git" ]; then echo "ok     no $nome"; else echo "FALTA  no $nome"; rc=1; fi
  done < <(lista_nos)
  [ -d "$RAIZ/openjutsu/workflows" ] && echo "ok     openjutsu" || { echo "FALTA  openjutsu"; rc=1; }
  if comfy_no_ar; then echo "ok     ComfyUI respondendo"; checar_nos || rc=1; else echo "FALTA  ComfyUI desligado (rode com --so-comfy)"; rc=1; fi
  if [ $rc = 0 ]; then echo "CONFERIDO_OK"; else echo "CONFERIDO_COM_PROBLEMAS"; fi
  exit $rc
fi

if [ "$SO_COMFY" = 1 ]; then
  iniciar_comfy || falha "o ComfyUI nao respondeu em 6 minutos (veja $RAIZ/comfy.log)"
  checar_nos || falha "faltam nos no ComfyUI (veja $RAIZ/comfy.log)"
  echo "COMFY_NO_AR"
  exit 0
fi

echo "Perfil: $PERFIL | versoes: $([ "$ULTIMAS" = 1 ] && echo 'mais novas' || echo 'testadas em 01/11/2026')"

if [ "$SIMULAR" != 1 ]; then
  command -v nvidia-smi >/dev/null 2>&1 || falha "nao achei a placa de video (nvidia-smi). Esta maquina nao serve."
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
  livre=$(df -BG --output=avail "$RAIZ" | tail -1 | tr -dc '0-9')
  necessario=70; [ "$PERFIL" = relay ] && necessario=90
  [ "${livre:-0}" -ge "$necessario" ] || falha "pouco disco livre (${livre:-0} GB; preciso de $necessario GB)"
  mem=$(free -g | awk '/^Mem:/ {print $2}')
  [ "${mem:-0}" -ge 48 ] || echo "AVISO: so ${mem:-?} GB de memoria RAM. O autor do Openjutsu testou com 64 GB."
fi

etapa "Programas do sistema (git, ffmpeg, aria2, tmux)"
run apt-get update -qq || falha "apt-get update"
run apt-get install -y -qq git ffmpeg aria2 tmux curl libgl1 libglib2.0-0 build-essential || falha "apt-get install"

etapa "ComfyUI"
clonar "$COMFYUI_URL" "$COMFY" "$COMFYUI_SHA" || falha "nao consegui baixar o ComfyUI"
run pip install -q -r "$COMFY/requirements.txt" || falha "pip install do ComfyUI"

etapa "Nos (plugins) do ComfyUI"
while IFS='|' read -r nome url sha; do
  [ -z "$nome" ] && continue
  echo "  $nome"
  clonar "$url" "$COMFY/custom_nodes/$nome" "$sha" || falha "nao consegui baixar o no $nome"
  if [ -f "$COMFY/custom_nodes/$nome/requirements.txt" ]; then
    run pip install -q -r "$COMFY/custom_nodes/$nome/requirements.txt" || falha "pip install do no $nome"
  fi
done < <(lista_nos)

etapa "Openjutsu (so os arquivos de workflow; a interface web nao e usada)"
clonar "$OPENJUTSU_URL" "$RAIZ/openjutsu" "$OPENJUTSU_SHA" || falha "nao consegui baixar o Openjutsu"

etapa "PyTorch com CUDA 12.8 (versao testada: $TORCH_VERSAO)"
if [ "$SIMULAR" = 1 ]; then
  echo "+ se o torch instalado nao for $TORCH_VERSAO: pip install $TORCH_PIP --index-url $TORCH_INDEX"
else
  atual=$(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo nenhum)
  echo "  torch instalado: $atual"
  if [ "$atual" != "$TORCH_VERSAO" ]; then
    # shellcheck disable=SC2086
    pip install -q $TORCH_PIP --index-url "$TORCH_INDEX" \
      || pip install -q -U torch torchvision torchaudio --index-url "$TORCH_INDEX" \
      || falha "nao consegui instalar o PyTorch cu128"
  fi
  python -c 'import torch; print("  torch", torch.__version__, "cuda ok" if torch.cuda.is_available() else "SEM CUDA")'
  python -c 'import sys, torch; sys.exit(0 if torch.cuda.is_available() else 1)' || falha "o PyTorch nao enxerga a placa de video"
fi

etapa "Modelos (a parte demorada e a que mais gasta download)"
FALHAS=0
pids=()
while IFS='|' read -r pasta nome url; do
  [ -z "$pasta" ] && continue
  if [ "$SIMULAR" = 1 ]; then echo "+ baixar $url -> models/$pasta/$nome"; continue; fi
  baixa_um "$pasta" "$nome" "$url" &
  pids+=($!)
done < <(lista_modelos)
for p in "${pids[@]:-}"; do
  [ -n "$p" ] && { wait "$p" || FALHAS=$((FALHAS + 1)); }
done
[ "$FALHAS" = 0 ] || falha "$FALHAS modelo(s) nao baixaram direito. Rode o instalador de novo: ele continua de onde parou."

if [ "$PERFIL" = relay ]; then
  etapa "Conferindo o no do relay"
  [ -f "$COMFY/custom_nodes/h3-relay/example_workflows/toolkit/H3-Character-Swap.api.json" ] || [ "$SIMULAR" = 1 ] \
    || falha "nao achei o workflow H3-Character-Swap.api.json dentro do h3-relay"
fi

etapa "Ligando o ComfyUI e conferindo"
iniciar_comfy || falha "o ComfyUI nao respondeu em 6 minutos (veja $RAIZ/comfy.log)"
if [ "$SIMULAR" != 1 ]; then
  checar_nos || falha "faltam nos no ComfyUI (veja $RAIZ/comfy.log)"
  mkdir -p "$RAIZ/trabalho"
fi
echo "Tempo: $((SECONDS / 60)) min"
echo "INSTALACAO_FIM"
