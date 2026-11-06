# Data licensing and attribution

The audio and derived spectrograms in this repository are adaptations of the following sources, both distributed under Creative Commons Attribution 4.0 International (CC BY 4.0):

https://creativecommons.org/licenses/by/4.0/

## CocoChorales — flute and clarinet

- Creators: Yusong Wu, Josh Gardner, Ethan Manilow, Ian Simon, Curtis Hawthorne, Jesse Engel.
- Work: The CocoChorales Dataset / The Chamber Ensemble Generator: Limitless High-Quality MIR Data via Generative Modeling (2022).
- Source: https://magenta.tensorflow.org/datasets/cocochorales
- Dataset documentation: https://github.com/lukewys/chamber-ensemble-generator
- Original track identifiers and selected intervals: `source_tracks.json`.

## Hood Fan

- Creator: acertingart (Freesound).
- Work: Hood Fan, sound ID 266180.
- Source: https://freesound.org/people/acertingart/sounds/266180/
- License: CC BY 4.0, as stated on the source page when checked on 2026-11-06.

## Modifications

Stereo hood-fan recording averaged to mono; source audio resampled to 10 kHz; paired instrument tracks concatenated and trimmed to the fan duration; full-recording RMS balancing and a common peak gain applied; two-source and three-source waveform mixtures created; overlapping 15-second WAV segments, STFT magnitude arrays, one-sided energy averages and images generated. These are derived evaluation/training examples, not original unmodified recordings. No endorsement by the source creators is implied.

Retain these credits and license information when sharing the audio and derived data, and indicate your additional changes. This file does not assert a new software license for the Python code.
