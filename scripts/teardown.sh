#!/usr/bin/env bash
# Delete every Azure resource this project created. Run ONLY after taking the Service Consumption
# (Azure Monitor metrics) screenshots, because deleting a resource deletes its metrics too.
#
# Usage: scripts/teardown.sh --yes
#
# The lab resource groups themselves are owned by Udacity and cannot be deleted by the lab user,
# so this removes the individual resources inside them.
set -euo pipefail

if [[ "${1:-}" != "--yes" ]]; then
  echo "This permanently deletes the kiosk's Azure resources. Re-run with --yes to proceed." >&2
  exit 1
fi

# GenAI lab subscription: storage + Document Intelligence (+ unused AI Services probe)
GENAI_SUB="65351cc3-a727-4694-8be3-844c6932508f"
GENAI_RG="Regroup_1aqrpsihqh"
# Computer-vision lab subscription: Face, Custom Vision, Video Indexer
CV_SUB="4c2045fc-9062-469b-a04d-fce56e0512a0"
CV_RG="aind-305856"

delete_cog() { # subscription resource-group name
  echo "deleting Cognitive Services account $3"
  az cognitiveservices account delete --subscription "$1" -g "$2" -n "$3" || echo "  (skipped: $3)"
  az cognitiveservices account purge --subscription "$1" -g "$2" -n "$3" \
     -l "$(az cognitiveservices account list-deleted --subscription "$1" --query "[?name=='$3'].location | [0]" -o tsv 2>/dev/null || true)" 2>/dev/null || true
}

delete_storage() { # subscription resource-group name
  echo "deleting storage account $3"
  az storage account delete --subscription "$1" -g "$2" -n "$3" --yes || echo "  (skipped: $3)"
}

delete_cog "$GENAI_SUB" "$GENAI_RG" kiosk-formrecognizer-1aq
delete_cog "$GENAI_SUB" "$GENAI_RG" kiosk-ais-1aq
delete_storage "$GENAI_SUB" "$GENAI_RG" kioskst1aqrpsihqh

delete_cog "$CV_SUB" "$CV_RG" kiosk-face-305856
delete_cog "$CV_SUB" "$CV_RG" kiosk-training-305856
delete_cog "$CV_SUB" "$CV_RG" kiosk-prediction-305856
echo "deleting Video Indexer account kiosk-vi-305856"
az resource delete --subscription "$CV_SUB" -g "$CV_RG" -n kiosk-vi-305856 \
  --resource-type Microsoft.VideoIndexer/accounts || echo "  (skipped: kiosk-vi-305856)"
delete_storage "$CV_SUB" "$CV_RG" kioskvi305856

echo "done. Remaining resources:"
az resource list --subscription "$GENAI_SUB" -g "$GENAI_RG" -o table || true
az resource list --subscription "$CV_SUB" -g "$CV_RG" -o table || true
