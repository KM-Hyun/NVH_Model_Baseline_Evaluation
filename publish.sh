#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v gh >/dev/null || { echo 'GitHub CLI(gh)를 설치하고 gh auth login을 먼저 실행하세요.' >&2; exit 1; }
gh auth status >/dev/null
owner=$(gh api user --jq .login)
repo="$owner/NVH_Model_Baseline_Evaluation"
if ! gh repo view "$repo" >/dev/null 2>&1; then
  gh repo create "$repo" --public --description 'Two- and three-source audio baseline evaluation dataset with STFT and energy-average features'
fi
url="https://github.com/$repo.git"
if git remote get-url origin >/dev/null 2>&1; then
  existing=$(git remote get-url origin)
  if [[ "$existing" != "$url" ]]; then echo "기존 origin($existing)이 대상($url)과 다릅니다. 자동 변경하지 않습니다." >&2; exit 1; fi
else
  git remote add origin "$url"
fi
visibility=$(gh api "repos/$repo" --jq 'if .private then "PRIVATE" else "PUBLIC" end')
if [[ "$visibility" != PUBLIC ]]; then echo '대상이 공개 저장소가 아닙니다. 설정을 확인하세요.' >&2; exit 1; fi
gh auth setup-git
GIT_LFS_FORCE_PROGRESS=1 GIT_LFS_PROGRESS="$PWD/upload_progress.log" git lfs push --all origin main
git push -u origin main
printf 'Uploaded: https://github.com/%s\n' "$repo"
