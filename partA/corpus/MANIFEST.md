# Corpus manifest

- Construction: 20 short, aligned, human-readable general-domain sentences authored for this audit and translated into seven languages. This is a small controlled probe set, not a published benchmark and not independently native-speaker validated.
- Languages: English (`eng`), Hindi (`hin`), Kannada (`kan`), Tamil (`tam`), Telugu (`tel`), Bengali (`ben`), Marathi (`mar`).
- Domains: daily life, transport, household actions, basic computing, safety, and communication.
- Size: 20 parallel sentence IDs × 7 languages = 140 sentence strings; 20 sentences per language.
- Preprocessing: UTF-8, NFC normalization, strip leading/trailing whitespace, preserve case for main audit; no punctuation removal. The starter script lowercases; corrected script preserves text because casing can matter to tokenization.
- Limitations: only 20 short sentences; synthetic translation can sound unnatural; limited domains, sentence lengths, named entities, code-switching, morphology and dialect variation; no native validation. Results are diagnostic only and must not support production routing without a larger native-reviewed corpus.
