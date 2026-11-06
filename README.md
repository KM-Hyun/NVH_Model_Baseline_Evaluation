# NVH_Model_Baseline_Evaluation

## 제공 음원

`full_audio/`의 약 1시간짜리 WAV 5개를 제공합니다. 짧게 자른 샘플이나 개별 스펙트로그램은 업로드하지 않습니다.

| 파일 | 내용 |
|---|---|
| `full_audio/flute.wav` | 플루트 개별 음원 |
| `full_audio/clarinet.wav` | 클라리넷 개별 음원 |
| `full_audio/hood_fan.wav` | 후드 팬 개별 음원 |
| `full_audio/mixture_2.wav` | 플루트 + 클라리넷 |
| `full_audio/mixture_3.wav` | 플루트 + 클라리넷 + 후드 팬 |

모두 3,601.704초(약60분2초), 10kHz, 모노, WAV FLOAT32입니다. 전체 WAV 용량은 약687MiB입니다. 같은 시간축에서 두 혼합음과 정답 파형을 비교할 수 있습니다.

이 파일들은 **개별 원본 곡 파일이 아니라**, 평가용으로 길이·샘플링 주파수·크기를 맞춘 전체 길이 파형입니다. 악기는 CocoChorales의 같은 곡 플루트/클라리넷 파트를 순서대로 이어 붙였고, 후드 팬 길이에 맞춰 마지막 곡을 잘랐습니다. 반복 확장하지 않았습니다. 팬 원본은 stereo 평균으로 모노 변환했습니다. 세 소스의 전체 RMS를 동일하게 맞춘 다음, 모든 소스와 두 혼합음에 같은 공통 게인을 적용했습니다. 소스별로 따로 최대값 정규화하지 않았습니다.

`mixture_2 = flute + clarinet`, `mixture_3 = flute + clarinet + hood_fan` (FLOAT32 반올림 오차 허용). 단, STFT magnitude/power는 위상 영향으로 소스별 단순 합이 아닙니다. 음압(Pa)으로 교정된 자료가 아닙니다.

## 다운로드

Git과 Git LFS를 설치한 뒤:

```bash
git lfs install
git clone https://github.com/KM-Hyun/NVH_Model_Baseline_Evaluation.git
cd NVH_Model_Baseline_Evaluation
git lfs pull
```

대용량 WAV는 Git LFS로 저장됩니다. 일반 ZIP 다운로드에는 실제 WAV 대신 포인터가 포함될 수 있습니다. 개별 WAV는 GitHub 파일 페이지의 다운로드 기능으로도 받을 수 있습니다.

## 15초 학습용 WAV 만들기

Python 3.10 이상에서 실행합니다. **스펙트로그램·FFT·이미지는 생성하지 않습니다.** 전체 길이의 소스 WAV를 자르고, 소스 파형을 더해 혼합 WAV를 만듭니다.

```bash
python -m pip install -r requirements.txt
python make_audio_samples.py --output audio_samples
```

기본값은 **15초 / overlap75% / hop3.75초**이며, Source_2와 Source_3를 각각957개 생성합니다. 마지막15초 미만 구간은 제외합니다.

먼저 3개만 확인하려면:

```bash
python make_audio_samples.py --limit 3 --output audio_samples_preview
```

2소스 또는 3소스만 생성하려면:

```bash
python make_audio_samples.py --task 2 --output audio_samples_2
python make_audio_samples.py --task 3 --output audio_samples_3
```

출력 구조:

```text
audio_samples/
  Source_2/sample_0000/
    flute.wav
    clarinet.wav
    mixture.wav          # flute + clarinet
  Source_3/sample_0000/
    flute.wav
    clarinet.wav
    hood_fan.wav
    mixture.wav          # flute + clarinet + hood_fan
  samples.csv
  settings.json
  Source_2_train.txt
  Source_2_validation.txt
  Source_2_test.txt
  Source_3_train.txt
  Source_3_validation.txt
  Source_3_test.txt
```

모든 출력은 **실제 WAV 파일**이며 심볼릭 링크를 사용하지 않습니다. 두 실험의 플루트·클라리넷 파일은 같은 내용을 각각 저장합니다. 기본값으로 전체 생성 시 약3.75GiB의 여유 공간이 필요합니다. GitHub에 이 생성 결과를 다시 올릴 필요는 없습니다.

- sample_0000: 0~15초, sample_0001: 3.75~18.75초.
- 10kHz 모노 FLOAT32, 기존 full_audio의 크기 유지. 구간별 추가 정규화·볼륨 조절·리샘플링 없음.
- 두 혼합음은 개별 소스의 같은 샘플 위치를 더해 생성. 제공된 full_audio/mixture_2.wav 및 mixture_3.wav와 FLOAT32 반올림 수준에서 일치합니다.
- 기본 분할: 과제별 학습766/검증92/평가91/경계제외8. 생성은957개 전부 하며, 경계8개는 학습·평가 목록에 넣지 않습니다.
- 원본 악기곡 경계에 맞춰 시간순으로 분할해 같은 곡이나 겹치는 파형이 서로 다른 분할에 들어가지 않게 합니다. 제공한 source_tracks.json을 사용합니다.
- 곡 연결부는 samples.csv의 track_join으로 표시합니다. crossfade/무음 제거는 적용하지 않습니다.
- 출력 폴더가 비어 있지 않으면 중단합니다. 재실행 시 새로운 --output 경로를 선택하세요.

원하는 길이와 중첩률을 지정할 수도 있습니다:

```bash
python make_audio_samples.py --sample-seconds 15 --overlap 0.75 --output audio_samples_custom
```

config.json과 기존 samples.csv는 과거 STFT 실험의 설정·구간 참고 자료입니다. **이번 실행 코드는 WAV만 생성**하며, 스펙트럼 배열이나 스펙트로그램 그림은 만들지 않습니다.

## 출처

- CocoChorales (MIDI-DDSP 합성음): https://magenta.tensorflow.org/datasets/cocochorales
- Hood Fan by acertingart (실제 녹음): https://freesound.org/people/acertingart/sounds/266180/

CC BY4.0 출처 및 수정 내역은 `DATA_LICENSE.md`를 확인하세요.
