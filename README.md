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

## 전처리 참고 설정

`config.json`은 기존 15초 샘플의 설정 기록입니다. WAV 5개만으로 원하는 전처리를 직접 수행할 수 있습니다.

- Sample window 15초 / overlap75% / hop3.75초: 957구간.
- FFT window0.5초 / periodic Hann / overlap60% / hop0.2초.
- nFFT5000, sampling10kHz → 주파수빈 간격2Hz, 0~5kHz.
- 평균 전 STFT: 2501주파수 ×73시간 프레임.
- Energy Average: 시간에 따른 단측 파워 평균(2501개). 내부주파수 파워2배, DC/Nyquist 제외.
- 기존 분할·연결부 정보: `samples.csv`, `source_tracks.json`. 같은 원본곡 및 중첩 파형이 서로 다른 분할에 들어가지 않도록 주의하세요.

현재 파일 목록에는 개별 원본321파일 압축본을 포함하지 않습니다. 이전 버전에는 해당 압축본이 있었으며 최신 버전에서 전체 길이 WAV로 대체했습니다.

## 출처

- CocoChorales (MIDI-DDSP 합성음): https://magenta.tensorflow.org/datasets/cocochorales
- Hood Fan by acertingart (실제 녹음): https://freesound.org/people/acertingart/sounds/266180/

CC BY4.0 출처 및 수정 내역은 `DATA_LICENSE.md`를 확인하세요.
