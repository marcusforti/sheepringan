#!/usr/bin/env bash
# Instala a skill sheepringan no Mac ou no Linux, sem sudo e sem Git.
# curl -fsSL https://raw.githubusercontent.com/marcusforti/sheepringan/main/instalar.sh | bash
set -euo pipefail
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
repo="${SHEEPRINGAN_ORIGEM:-}"
if [ -z "$repo" ]; then
  curl -fsSL https://codeload.github.com/marcusforti/sheepringan/tar.gz/refs/heads/main | tar -xz -C "$tmp"
  repo="$tmp/sheepringan-main"
fi
origem="$repo/skill/sheepringan"
[ -f "$origem/SKILL.md" ] || { echo "Nao achei a skill no pacote baixado." >&2; exit 1; }
alvos=("$HOME/.claude/skills" "$HOME/.agents/skills")
for alvo in "${alvos[@]}"; do
  mkdir -p "$alvo"
  rm -rf "$alvo/sheepringan.novo" "$alvo/sheepringan.velho"
  # Monta a pasta nova ao lado e troca no fim: se algo falhar no meio, a versao antiga continua inteira.
  cp -R "$origem" "$alvo/sheepringan.novo"
  find "$alvo/sheepringan.novo" -type d -name '__pycache__' -prune -exec rm -rf {} +
  if [ -e "$alvo/sheepringan" ]; then mv "$alvo/sheepringan" "$alvo/sheepringan.velho"; fi
  mv "$alvo/sheepringan.novo" "$alvo/sheepringan"
  rm -rf "$alvo/sheepringan.velho"
done
echo
echo "sheepringan instalada."
echo "Abra o Claude Code (se ja estava aberto, feche e abra de novo) e escreva: /sheepringan"
echo
echo "O que o seu computador precisa ter (a skill confere e ajuda a instalar):"
for par in "python3|Python 3.9 ou mais novo" "ffmpeg|ffmpeg (Mac: brew install ffmpeg)" "ssh|cliente SSH"; do
  prog="${par%%|*}"; texto="${par#*|}"
  if command -v "$prog" >/dev/null 2>&1; then echo "  ok     $prog"; else echo "  FALTA  $texto"; fi
done
