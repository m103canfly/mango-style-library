#!/usr/bin/env bash
# gen_image.sh — mango-style-library 的可移植图像生成适配层
#
# 用法（与 Kimi image_generation 插件 CLI 完全同构）：
#   gen_image.sh generate --description "..." [--ratio 1:1|3:2|2:3|16:9|9:16]
#       [--resolution 1K|2K|4K] [--background opaque|transparent]
#       [--reference-image <URL或本地路径>]... --output <path.png>
#   gen_image.sh image-to-url --image-path <本地图>     # 仅 kimi 后端需要（参考图转公网URL）
#   gen_image.sh ensure-deps                            # 仅 kimi 后端需要（装 agent-gw SDK）
#
# 后端选择（优先级从高到低）：
#   1. 环境变量 GEN_IMAGE_BACKEND = kimi | openai | deepseek
#   2. 自动探测：/app/.agents/plugins/image_generation 存在 → kimi
#      OPENAI_API_KEY 已设 → openai；DEEPSEEK_API_KEY 已设 → deepseek
#
# 后端说明：
#   kimi     — 经 Kimi image_generation 插件（agent-gw）。本会话内全量实战验证。
#   openai   — 经 OpenAI Images API（gpt-image-1，generations/edits 端点）。
#              参考实现：依赖官方文档端点，未在本环境实测，请先用一张小图验证。
#   deepseek — DeepSeek 官方公开 API 目前无图像生成端点；如自建了 OpenAI 兼容
#              图像端点（如 Janus 服务），设 DEEPSEEK_IMAGE_ENDPOINT 即可接入。
set -euo pipefail

CMD="${1:-generate}"; shift || true
DESC=""; RATIO="1:1"; RES="1K"; BG="opaque"; OUT=""; REFS=(); IMG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --description) DESC="$2"; shift 2;;
    --ratio) RATIO="$2"; shift 2;;
    --resolution) RES="$2"; shift 2;;
    --background) BG="$2"; shift 2;;
    --reference-image) REFS+=("$2"); shift 2;;
    --output) OUT="$2"; shift 2;;
    --image-path) IMG="$2"; shift 2;;
    *) echo "未知参数: $1" >&2; exit 2;;
  esac
done

BACKEND="${GEN_IMAGE_BACKEND:-}"
if [ -z "$BACKEND" ]; then
  if [ -d /app/.agents/plugins/image_generation ]; then BACKEND="kimi"
  elif [ -n "${OPENAI_API_KEY:-}" ]; then BACKEND="openai"
  elif [ -n "${DEEPSEEK_API_KEY:-}" ]; then BACKEND="deepseek"
  else echo "无法确定图像后端：设 GEN_IMAGE_BACKEND 或配置相应 API Key" >&2; exit 1; fi
fi

kimi_run() {
  local PLUGIN=/app/.agents/plugins/image_generation
  [ -d "$PLUGIN" ] || { echo "kimi 后端不可用：未找到 $PLUGIN" >&2; exit 1; }
  case "$CMD" in
    ensure-deps) (cd "$PLUGIN" && python3 scripts/image_generation_tool.py ensure-deps);;
    image-to-url) (cd "$PLUGIN" && python3 scripts/image_generation_tool.py image-to-url --image-path "$IMG");;
    generate)
      local args=(generate --description "$DESC" --ratio "$RATIO" --resolution "$RES" --background "$BG" --output "$OUT")
      for r in ${REFS[@]+"${REFS[@]}"}; do
        case "$r" in
          http://*|https://*) args+=(--reference-image "$r");;
          *) echo "kimi 后端参考图必须是公网 URL，本地图请先 image-to-url：$r" >&2; exit 1;;
        esac
      done
      (cd "$PLUGIN" && python3 scripts/image_generation_tool.py "${args[@]}");;
  esac
}

map_size() {  # ratio/resolution → OpenAI size
  case "$1" in
    1:1) echo "1024x1024";;
    3:2|16:9) echo "1536x1024";;
    2:3|9:16) echo "1024x1536";;
    *) echo "1024x1024";;
  esac
}

openai_run() {
  [ "$CMD" = "generate" ] || { echo "openai 后端无需 $CMD（参考图直接传本地路径或 URL）" >&2; exit 1; }
  command -v curl >/dev/null || { echo "需要 curl" >&2; exit 1; }
  command -v python3 >/dev/null || { echo "需要 python3" >&2; exit 1; }
  local size; size=$(map_size "$RATIO")
  local api="https://api.openai.com/v1/images"
  local tmp; tmp=$(mktemp -d)
  local resp="$tmp/resp.json"
  if [ ${#REFS[@]} -eq 0 ]; then
    curl -sS -X POST "$api/generations" \
      -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
      -d "$(python3 -c "import json,sys;print(json.dumps({'model':'gpt-image-1','prompt':sys.argv[1],'size':sys.argv[2],'background':sys.argv[3],'quality':'high'}))" "$DESC" "$size" "$BG")" \
      -o "$resp"
  else
    local fargs=(); i=0
    for r in "${REFS[@]}"; do
      i=$((i+1)); f="$tmp/ref$i.png"
      case "$r" in http://*|https://*) curl -sS -L "$r" -o "$f";; *) cp "$r" "$f";; esac
      fargs+=(-F "image[]=@$f")
    done
    curl -sS -X POST "$api/edits" \
      -H "Authorization: Bearer $OPENAI_API_KEY" \
      -F "model=gpt-image-1" -F "prompt=$DESC" -F "size=$size" -F "background=$BG" \
      ${fargs[@]+"${fargs[@]}"} -o "$resp"
  fi
  python3 - "$resp" "$OUT" <<'PY'
import json, sys, base64
d = json.load(open(sys.argv[1]))
if "error" in d: print("OpenAI API 错误:", d["error"].get("message"), file=sys.stderr); sys.exit(1)
b64 = d["data"][0].get("b64_json")
if b64: open(sys.argv[2], "wb").write(base64.b64decode(b64))
else:
    import urllib.request; urllib.request.urlretrieve(d["data"][0]["url"], sys.argv[2])
print("Saved generated image to:", sys.argv[2])
PY
  rm -rf "$tmp"
}

deepseek_run() {
  local ep="${DEEPSEEK_IMAGE_ENDPOINT:-}"
  [ -n "$ep" ] || { echo "DeepSeek 官方公开 API 无图像生成端点。请设 DEEPSEEK_IMAGE_ENDPOINT 指向你的 OpenAI 兼容图像端点（如自建 Janus），或改用 GEN_IMAGE_BACKEND=kimi|openai" >&2; exit 1; }
  [ "$CMD" = "generate" ] || { echo "deepseek 后端仅支持 generate" >&2; exit 1; }
  local size; size=$(map_size "$RATIO")
  local resp; resp=$(mktemp)
  curl -sS -X POST "$ep" \
    -H "Authorization: Bearer ${DEEPSEEK_API_KEY:-none}" -H "Content-Type: application/json" \
    -d "$(python3 -c "import json,sys;print(json.dumps({'prompt':sys.argv[1],'size':sys.argv[2],'response_format':['b64_json']}))" "$DESC" "$size")" \
    -o "$resp"
  python3 - "$resp" "$OUT" <<'PY'
import json, sys, base64, urllib.request
d = json.load(open(sys.argv[1]))
item = d.get("data", [{}])[0]
if item.get("b64_json"): open(sys.argv[2], "wb").write(base64.b64decode(item["b64_json"]))
elif item.get("url"): urllib.request.urlretrieve(item["url"], sys.argv[2])
else: print("端点返回无法解析:", json.dumps(d)[:400], file=sys.stderr); sys.exit(1)
print("Saved generated image to:", sys.argv[2])
PY
}

case "$BACKEND" in
  kimi) kimi_run;;
  openai) openai_run;;
  deepseek) deepseek_run;;
  *) echo "未知 GEN_IMAGE_BACKEND: $BACKEND（可选 kimi|openai|deepseek）" >&2; exit 1;;
esac
