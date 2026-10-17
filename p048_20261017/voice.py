"""P048 narration: pinned P047 voice, retained PCM/query/phonemes and independent ASR.

Only narration is produced. Text is the six-paragraph final script approved by root.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time
import wave

ENGINE_REF = "voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90"
EXPECTED_IMAGE_ID = "sha256:f4bfb5866aec6ea52797f54a52f8cef38b2b05cc157f229e60196e3679b8cb66"
BASE = "http://127.0.0.1:50021"
TEXTS = [
    "星から飛んでくる粒子が、惑星の手前で曲がった。この磁場があれば、空はずっと残るのかな。",
    "磁場は、電気を帯びた粒子の進む向きを変える。星の風に押され、磁場の広がりは昼側で縮み、夜側へ長い尾を引く。",
    "今度は極の上。加熱などで勢いを得た、電気を帯びた大気の粒子が、磁場に沿って外へ出ていく。空から宇宙への出口だ。",
    "紫外線は、磁場を通り抜けて上空へ届く。分子を変えたり、気体を温めたりする働きは続くんだ。",
    "火山から空へ加わる気体もある。入ってくる量と、宇宙へ逃げる量。その出入りが、長い時間の空を変える。",
    "磁場が変えるのは、粒子の通り道。空が残るかは、星の光や、材料の出入りも合わせて考えるんだ。",
]
# Preserve relevant established readings; explicitly disambiguate this episode's terms.
READINGS = [
    ("磁場", "ジバ", 1), ("極", "キョク", 1),
    ("昼側", "ヒルガワ", 0), ("夜側", "ヨルガワ", 0),
    ("惑星", "ワクセイ", 0), ("上空", "ジョウクウ", 0),
    ("紫外線", "シガイセン", 2), ("加熱", "カネツ", 0),
    ("大気", "タイキ", 1), ("星の光", "ホシノヒカリ", 4),
]
QUERY_SETTINGS = {
    "speedScale": 1.01, "pitchScale": -0.015, "intonationScale": 1.08,
    "volumeScale": 1.0, "prePhonemeLength": 0.15, "postPhonemeLength": 0.25,
    "pauseLength": None, "pauseLengthScale": 1.0,
    "outputSamplingRate": 48000, "outputStereo": False,
}
TIMING_SOURCE = "https://github.com/VOICEVOX/voicevox_engine/blob/f2a20b1d4d2613851daffdd1de2217a472d89c48/voicevox_engine/tts_pipeline/tts_engine.py"

def put(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def phoneme_timing(query, samples):
    """Derive decoder-frame boundaries, not empirical forced-alignment timings.

    Engine 0.25.2: upspeak; silence/pause overrides; speed; per-phoneme even rounding
    at 93.75 Hz. Output at 48 kHz is 512 samples per acoustic frame.
    """
    q = copy.deepcopy(query)
    assert q["outputSamplingRate"] == 48000 and not q["outputStereo"]
    stream = [dict(text="", vowel="sil", vowel_length=q["prePhonemeLength"],
                   pitch=0.0, phrase=None, mora=None, kind="pre_silence")]
    for ai, a in enumerate(q["accent_phrases"]):
        for mi, m in enumerate(a["moras"]):
            stream.append(dict(m, phrase=ai, mora=mi, kind="speech"))
        if a.get("is_interrogative") and a["moras"] and a["moras"][-1]["pitch"] > 0:
            last = a["moras"][-1]
            stream.append(dict(text=last["vowel"], vowel=last["vowel"], vowel_length=.15,
                               pitch=last["pitch"], phrase=ai, mora=None, kind="upspeak"))
        if a.get("pause_mora"):
            stream.append(dict(a["pause_mora"], phrase=ai, mora=None, kind="pause"))
    stream.append(dict(text="", vowel="sil", vowel_length=q["postPhonemeLength"],
                       pitch=0.0, phrase=None, mora=None, kind="post_silence"))
    frame = 0
    moras, phonemes = [], []
    for m in stream:
        first = frame
        length = m["vowel_length"]
        if m["vowel"] == "pau":
            if q.get("pauseLength") is not None:
                length = q["pauseLength"]
            length *= q.get("pauseLengthScale", 1.0)
        units = []
        if m.get("consonant"):
            units.append((m["consonant"], m["consonant_length"]))
        units.append((m["vowel"], length))
        for symbol, seconds in units:
            frames = round(seconds / q["speedScale"] * 93.75)
            end = frame + frames
            phonemes.append(dict(phoneme=symbol, start_sample=frame*512,
                                 end_sample=end*512, start=frame/93.75, end=end/93.75,
                                 phrase=m["phrase"], mora=m["mora"], kind=m["kind"]))
            frame = end
        moras.append(dict(text=m["text"], start_sample=first*512, end_sample=frame*512,
                          start=first/93.75, end=frame/93.75, phrase=m["phrase"],
                          mora=m["mora"], kind=m["kind"]))
    assert frame * 512 == samples, (frame*512, samples)
    return dict(method="VOICEVOX 0.25.2 query-to-decoder-frame reconstruction",
                source=TIMING_SOURCE, decoder_frame_rate=93.75,
                output_sample_rate=48000, samples_per_decoder_frame=512,
                reconstructed_samples=frame*512, wave_samples=samples,
                exact_sample_count_match=True, empirical_alignment=False,
                phonemes=phonemes, moras=moras)

def synthesize(root):
    import requests
    root.mkdir(parents=True, exist_ok=True)
    response = None
    for attempt in range(100):
        try:
            response = requests.get(BASE + "/speakers", timeout=5)
            if response.ok:
                break
        except requests.RequestException:
            pass
        time.sleep(2)
    if response is None:
        raise RuntimeError("VOICEVOX did not start")
    response.raise_for_status()
    person = next(s for s in response.json() if s["name"] == "四国めたん")
    sid = next(s["id"] for s in person["styles"] if s["name"] == "ノーマル")
    assert sid == 2, sid
    response = requests.get(BASE + "/version", timeout=10)
    response.raise_for_status()
    version = response.json()
    assert version == "0.25.2", version
    image_id = subprocess.check_output(["docker", "inspect", "--format={{.Image}}", "voicevox"], text=True).strip()
    assert image_id == EXPECTED_IMAGE_ID, (image_id, EXPECTED_IMAGE_ID)
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", ENGINE_REF], text=True))[0]
    assert image["Id"] == EXPECTED_IMAGE_ID
    assert ENGINE_REF in image["RepoDigests"], image["RepoDigests"]
    engine_record = dict(requested_manifest=ENGINE_REF, image_id=image_id,
                         repo_digests=image["RepoDigests"], architecture=image["Architecture"],
                         os=image["Os"], version=version,
                         inherited_from_run=38877728282,
                         inherited_pull_log_job=116896721876)
    put(root / "engine_record.json", engine_record)
    (root / "engine_image_digest.txt").write_text(image_id + "\n")
    for endpoint in ("engine_manifest", "core_versions"):
        response = requests.get(BASE + "/" + endpoint, timeout=20)
        response.raise_for_status()
        put(root / (endpoint + ".json"), response.json())
    put(root / "voice.json", dict(engine="VOICEVOX", engine_version=version,
        speaker="四国めたん", style="ノーマル", selected_style_id=sid,
        credit="VOICEVOX:四国めたん", readings=READINGS, query_settings=QUERY_SETTINGS,
        enable_interrogative_upspeak=True, actual_listening_performed=False))
    put(root / "script.json", [dict(id=i, text=t) for i,t in enumerate(TEXTS,1)])
    for word, kana, accent in READINGS:
        response = requests.post(BASE + "/user_dict_word",
            params=dict(surface=word, pronunciation=kana, accent_type=accent, priority=8), timeout=30)
        response.raise_for_status()
    response = requests.get(BASE + "/user_dict", timeout=30)
    response.raise_for_status()
    put(root / "user_dictionary.json", response.json())
    records = []
    for i, text in enumerate(TEXTS, 1):
        response = requests.post(BASE + "/audio_query", params=dict(text=text, speaker=sid), timeout=90)
        response.raise_for_status()
        q = response.json()
        q.update(QUERY_SETTINGS)
        put(root / f"{i:02d}_query.json", q)
        response = requests.post(BASE + "/synthesis",
            params=dict(speaker=sid, enable_interrogative_upspeak="true"), json=q, timeout=150)
        response.raise_for_status()
        p = root / f"{i:02d}.wav"
        p.write_bytes(response.content)
        with wave.open(str(p), "rb") as w:
            count, rate, channels, width = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
            pcm = w.readframes(count)
            assert rate == 48000 and channels == 1 and width == 2
            assert len(pcm) == count * 2
        timing = phoneme_timing(q, count)
        put(root / f"{i:02d}_phonemes.json", timing)
        record = dict(file=p.name, text=text, duration=count/rate, samples=count,
            sample_rate=rate, channels=channels, sample_width=width,
            sha256=sha(response.content), pcm_sha256=sha(pcm), kana=q.get("kana"),
            query_sha256=sha((root/f"{i:02d}_query.json").read_bytes()),
            speech_start=next(m["start"] for m in timing["moras"] if m["kind"]=="speech"),
            speech_end=max(m["end"] for m in timing["moras"] if m["kind"] in ("speech","upspeak")))
        records.append(record)
        put(root / "retrieval.json", records)
        print("ORIGINAL", i, json.dumps(record, ensure_ascii=False), flush=True)
    put(root / "narration_durations.json", dict(
        segment_seconds=[r["duration"] for r in records],
        segment_samples=[r["samples"] for r in records],
        sum_seconds=sum(r["duration"] for r in records),
        sum_samples=sum(r["samples"] for r in records),
        inserted_gaps=False, speed_or_pitch_processing_after_synthesis=False))
    print("ALL_SPEECH_SYNTHESIZED", sum(r["duration"] for r in records), flush=True)

def transcribe(root):
    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
    results = []
    for p in sorted(root.glob("[0-9][0-9].wav")):
        segments, info = model.transcribe(str(p), language="ja", word_timestamps=True,
                                         beam_size=5, vad_filter=False)
        result = dict(file=p.name, duration=info.duration, model="large-v3-turbo",
            language="ja", compute_type="int8", cpu_threads=4, beam_size=5,
            vad_filter=False, supplied_transcript_prompt=False,
            actual_listening_performed=False,
            segments=[dict(start=s.start,end=s.end,text=s.text,
                           words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability)
                                  for w in s.words]) for s in segments])
        put(root/f"{p.stem}_words.json",result)
        results.append(result)
        print("TRANSCRIPT", p.name, [s["text"] for s in result["segments"]], flush=True)
    packages = {}
    for name in ("requests", "faster-whisper", "ctranslate2", "huggingface-hub", "numpy"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    cache = Path(os.environ.get("HF_HOME", str(Path.home()/".cache/huggingface"))) / "hub"
    snapshots = sorted(str(p.relative_to(cache)) for p in cache.glob("models--*whisper*/snapshots/*") if p.is_dir())
    put(root/"asr_conditions.json", dict(model="large-v3-turbo", device="cpu", compute_type="int8",
        cpu_threads=4, language="ja", beam_size=5, vad_filter=False, word_timestamps=True,
        supplied_transcript_prompt=False, actual_listening_performed=False,
        packages=packages, downloaded_model_snapshots=snapshots))
    print("VOICE_READY",len(results),flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("p048/audio/raw"))
    parser.add_argument("--stage",choices=["all","synth","asr"],default="all")
    args=parser.parse_args()
    if args.stage in ("all","synth"):
        synthesize(args.output)
    if args.stage in ("all","asr"):
        transcribe(args.output)

if __name__ == "__main__":
    main()

