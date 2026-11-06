# NVH_Model_Baseline_Evaluation

플루트·클라리넷·후드 팬을 이용한 2소스/3소스 분리 실험 자료입니다. **선택한 원본 음원과 재생성 코드만 배포**합니다. 약 7.2GiB의 전처리 결과는 저장소에 포함하지 않습니다.

## 포함 자료

- `source_audio.tar.gz`: 원본 후드 팬 MP3 1개와 CocoChorales 원본 악기 WAV 320개(160곡 × 2악기), 총 321파일. 반복·정규화·리샘플링 전 원본 파일입니다. CocoChorales 전체 48,000곡이 아니라 이 평가 데이터에 사용한 곡만 포함합니다.
- `source_manifest.json`: 원본 파일별 SHA256·크기, 압축파일 SHA256.
- `prepare.py`, `분할검증.py`, `rebuild.py`: 추출·전처리·검증 코드.
- `config.json`, `source_tracks.json`, `samples.csv`: 기존 생성 결과의 기준 설정과 구간 정보.
- `preview_sample_0000.png`: 결과 그림 예시 1개.
- `DATA_LICENSE.md`: 출처·CC BY 4.0·변경 내역.

원본 후드 팬은 스테레오48kHz MP3, 악기는 모노16kHz WAV입니다. 팬 MP3는 손실압축, 악기는 MIDI-DDSP 합성음입니다. 실제 확인한 전처리 후 길이는 3,601.704초입니다.

## 받기

Git과 Git LFS를 설치한 뒤:

```bash
git lfs install
git clone https://github.com/KM-Hyun/NVH_Model_Baseline_Evaluation.git
cd NVH_Model_Baseline_Evaluation
git lfs pull
```

## 원본만 풀기

```bash
python rebuild.py --extract-only
```

원본은 `generated/data/`에 저장됩니다. 외부 파일 다운로드는 필요하지 않습니다.

## 동일 조건으로 전처리

Linux/WSL 환경 권장. Python 3.10 이상. 그림용 글꼴은 Ubuntu에서 `sudo apt install fonts-noto-cjk`로 설치하거나 prepare.py의 FONT 경로를 변경하세요. Windows는 심볼릭 링크 생성 권한/개발자 모드가 필요할 수 있습니다.

```bash
python -m pip install -r requirements.txt
python rebuild.py
```

결과: `generated/data/NVH_Model_Baseline_Evaluation/`. `--output /원하는/폴더`로 위치를 변경할 수 있습니다. 기존 출력이 있으면 재생성 시 해당 생성 파일이 갱신됩니다.

## 전처리 조건

| 항목 | 설정 |
|---|---|
| 2소스 | 플루트 + 클라리넷 |
| 3소스 | 플루트 + 클라리넷 + 후드 팬 |
| 길이 | 후드 팬 기준 약60분2초 |
| 샘플 | 15초, overlap75%, hop3.75초, 957개 |
| 샘플링 | 10kHz 모노, anti-alias 리샘플링 |
| FFT | 주기적 Hann 0.5초, 5000점, overlap60%, hop0.2초 |
| 주파수 빈 | 0~5kHz, 2Hz 간격 |
| STFT magnitude | (2501,73), 선형값 |
| Energy Average | 시간 프레임별 단측 파워 평균, (2501,) |
| RMS spectrum | Energy Average의 제곱근 |
| 혼합 | 전체 길이 RMS 균형 후 모든 소스·혼합음에 공통 게인 |

Energy Average는 시간축이 없는 스펙트럼입니다. 시간 구조가 필요하면 평균 전 STFT를 사용하세요. 파형은 합산 관계를 유지하지만 magnitude/power는 위상 때문에 단순 합산 관계가 성립하지 않습니다. 음압(Pa)으로 교정된 데이터가 아닙니다.

악기곡은 동기화를 유지해 순서대로 연결합니다. 연결부는 crossfade하지 않으며 samples.csv의 track_join으로 표시합니다. 원본곡 경계에서 시간순80/10/10에 가깝게 분할하고, 분할을 가로지르는 중첩 구간은 제외합니다. 학습766/검증92/평가91/경계제외8. 후드 팬은 하나의 녹음이므로 미지팬·미지환경 일반화 평가로 해석하면 안 됩니다. 선택 악기곡은 CocoChorales 원본 train에서 가져왔으며, 이 데이터의 분할은 사용자 정의입니다.

## 검증

```bash
python rebuild.py --verify-only
```

아카이브와 원본321파일의 체크섬을 검증합니다. 전처리 후 분할검증.py는 소스 합산, 배열 크기, 에너지 평균, 분할 간 원본곡·시간 중복을 확인합니다.

## 출처

- CocoChorales: https://magenta.tensorflow.org/datasets/cocochorales
- Hood Fan by acertingart: https://freesound.org/people/acertingart/sounds/266180/

두 원본의 CC BY 4.0 조건과 기여자 표기를 DATA_LICENSE.md에 보관했습니다. 코드 자체에 별도의 소프트웨어 라이선스를 지정한 것은 아닙니다.
