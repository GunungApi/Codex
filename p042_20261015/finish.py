"""Finish HEION-P042 without re-encoding the high-quality shots or narration."""
from pathlib import Path
import json, hashlib, subprocess, zipfile, shutil, math, wave
import numpy as np
from PIL import Image,ImageDraw
import av
ROOT=Path('p042');OUT=Path('deliverables');OUT.mkdir(exist_ok=True)
P=json.loads((ROOT/'timeline.json').read_text());STEM='heionreki_p042_v1'
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=ROOT/'clips/concat.txt';manifest.write_text(''.join(f"file 'shot_{s['id']:02d}.mp4'\n" for s in P['shots']))
master=ROOT/'audio/master.m4a';high=OUT/f'{STEM}_high.mp4';light=OUT/f'{STEM}_light.mp4'
run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(manifest),'-i',str(master),'-map','0:v:0','-map','1:a:0','-c','copy','-video_track_timescale','24000','-movflags','+faststart',str(high)])
run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','slow','-crf','23','-c:a','copy','-movflags','+faststart',str(light)])
def check(path):
    inp=av.open(str(path));v=inp.streams.video[0];dims=(v.width,v.height);count=0;prev=None;dups=[];black=[];pts=[];hs=set();brightness=[]
    for f in inp.decode(video=0):
        rgb=f.to_ndarray(format='rgb24');h=hashlib.sha256(rgb.tobytes()).hexdigest();hs.add(h)
        if prev==h:dups.append(count)
        prev=h;pts.append(float(f.pts*f.time_base));small=rgb[::16,::16];brightness.append(float(small.mean()))
        if small.mean()<2 and (small.max(-1)<5).mean()>.99:black.append(count)
        count+=1
    inp.close();assert count==P['frames'],(path,count,P['frames']);terr=max(abs(t-i/24) for i,t in enumerate(pts));assert terr<1e-4,terr
    a=av.open(str(path));samples=0;af=0;peak=0.
    for frame in a.decode(audio=0):samples+=frame.samples;af+=1;peak=max(peak,float(np.max(np.abs(frame.to_ndarray()))))
    a.close();assert af>0
    data=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=10:print_format=json','-f','null','-']).stderr;m=json.loads(data[data.rfind('{'):])
    aac=ROOT/'validation'/f'{path.stem}.aac';run(['ffmpeg','-y','-v','error','-i',str(path),'-vn','-c:a','copy','-f','adts',str(aac)])
    r=dict(file=path.name,width=dims[0],height=dims[1],frames=count,duration=count/24,fps=24,bytes=path.stat().st_size,sha256=sha(path),decode_all=True,unique_images=len(hs),consecutive_identical_frames=dups,black_candidates=black,max_timestamp_error=terr,audio_frames=af,audio_samples=samples,audio_sha256=sha(aac),lufs=float(m['input_i']),true_peak_dbtp=float(m['input_tp']),mean_frame_brightness_range=[min(brightness),max(brightness)])
    assert abs(r['lufs']+16)<.6 and r['true_peak_dbtp']<=-1.5,r;assert not black
    print('VERIFIED',json.dumps(r),flush=True);return r
reports=[check(high),check(light)];assert reports[0]['audio_sha256']==reports[1]['audio_sha256']
rawaac=ROOT/'validation/master.aac';run(['ffmpeg','-y','-v','error','-i',str(master),'-c:a','copy','-f','adts',str(rawaac)]);assert sha(rawaac)==reports[0]['audio_sha256']
start=P['shots'][5]['start'];dur=P['shots'][7]['end']-start
run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(high),'-t',str(dur),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','slow','-crf','20','-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT/f'{STEM}_water_preview.mp4')])
folder=ROOT/'validation/final_samples';folder.mkdir(parents=True,exist_ok=True)
def sheet_at(times,name,cols=4):
    ims=[]
    for i,t in enumerate(times):
        path=folder/f'{name}_{i:02d}.png';run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(high),'-frames:v','1',str(path)])
        im=Image.open(path).convert('RGB').resize((270,480));d=ImageDraw.Draw(im);d.rectangle((0,0,180,26),fill='black');d.text((5,4),f'{t:.2f}s',fill='white');ims.append(im)
    sheet=Image.new('RGB',(270*cols,480*math.ceil(len(ims)/cols)))
    for i,im in enumerate(ims):sheet.paste(im,((i%cols)*270,(i//cols)*480))
    sheet.save(folder/f'{name}.jpg',quality=95)
sheet_at([(s['start']+s['end'])/2 for s in P['shots']],'shot_sheet')
sheet_at([(c['start']+c['end'])/2 for c in P['captions']],'caption_sheet')
sheet_at(np.linspace(P['shots'][5]['start']+.2,P['shots'][7]['end']-.2,12),'water_sequence')
(ROOT/'validation/final_validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
summary=dict(status='rendered_and_machine_verified',episode='P042',duration=P['duration'],frames=P['frames'],shots=len(P['shots']),captions=len(P['captions']),original_audio_segments=len(P['narration']),outputs=reports,actual_audio_listening=False,final_visual_review_by_assistant=False,phone_preview=False,local_container_unavailable=True,preview_seconds=dur)
(ROOT/'validation/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));Path('status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
script='\n\n'.join(f"### 語り{s['id']:02d}｜{s['start']:.3f}〜{s['end']:.3f}秒\n{s['text']}" for s in P['narration'])
doc=f'''# 平穏暦全史・前史042\n## 惑星があることと、住めること\n
第1版・音声、日英字幕、音楽、効果音付き。{P['duration']:.3f}秒、1080×1920・24fps・{P['frames']}コマ。制作日：2026年10月15日。第2巻P042の計画を継承。

## 問い
惑星を見つけたことから、地表に液体の水が存在できる環境をどう調べるか。大きさ、受光量、大気、温度・気圧、生命の証拠を別々の段階として見せる。

## 台本と実音声時間
{script}

## 今回の映像と計算
二つの惑星は同じ半径、同じメッシュ、同じ大陸識別の関数を使う比較模型。観測されたケプラー444の地表を再現してはいない。前回の古い惑星という文脈から、一般的な環境の問いへ進む。

光の比較は、一定光度の等方的な点光源と同じ受光面積を用いる。距離をrから2rへ変えると、受け取る単位面積あたりの放射は1/4になる。アニメーションの光の筋は方向を読むための記号であり、実際の光速、光子数、地表温度を求めた表示ではない。星の出力と惑星の半径を同時には変えない。

大気は入射光の一部を反射し、地表からの熱放射を吸収して再放射する代表的な働きを分けて示す。吸収点から外向き・内向きに新しい波線を出す。全波長や全大気が同じ振る舞いをするとは一般化しない。波線の色と速度は模式表示。気候の全球連成計算ではなく、温度数値は表示しない。

氷、液体の水、水蒸気は同じ谷・山・岸の地形に対する別条件の景観。氷から蒸気まで一つの実在惑星がこの秒数で変化した記録ではない。温度と気圧は独立の条件で、気圧も温度も定量的に推定していない。水蒸気は透明であるため、気体の場面の光る点は分子を読むための目印と表示する。白い霧を水蒸気そのものとは呼ばない。山、海底、岸の高さは同じ三角形地形を使い、水面だけ動的な法線と変位を持つ。植物、生物、都市は追加していない。

ハビタブルゾーンの帯は、大気などの条件のもとで地表に液体の水がありうる距離を示す模式模型。実在恒星の境界距離を数値計算した帯ではない。生命の検出印や、人が呼吸できる保証を付けない。地表の液体の水を手掛かりにする回であり、宇宙の全生命の必要条件や地下海の不存在へ広げない。

## 立体表現
主役、地形、水面、星、気体の目印は三次元メッシュ。高画質版は1080×1920へ直接描画し、4サンプルの輪郭処理と地形の2048×2048影を使う。地表の空は三次元ノイズを視線に沿って16段積算する雲。全景の惑星雲は薄い球面層で、近景の体積雲とは区別する。前作の静止画の拡大や、低解像度映像の拡大を本編立体撮影の代わりにしない。

## 声・字幕・音
原音6区間はVOICEVOX・四国めたん（ノーマル）。前作と同じ話速1.01・音高-0.015・抑揚1.08、48kHz・16bit PCM。受領後に発話速度は変えない。水の状態を観察するため、語り04の二か所へ合計1.7秒の無音だけを追加。原音は保存し、無音を除くと元の全サンプルと一致することを検査した。

字幕は合成音素の実長を93.75Hzの合成フレームへ丸め、原WAVのサンプル数と照合して作成。独立の音声認識結果も原音と保管。台本を字幕の正本とする。『液体』『気圧』『水蒸気』『二倍』『四分の一』などを原音の音素列で確認する。耳でのアクセントや聴き心地の確認は未実施。

日英SRTと装飾ASSは同一のtimeline.jsonから生成。通常64、白・水色、1〜2行。140/120msの透明度変化、180ms・16pxの登場移動、98〜100%の控えめな拡大。書体ファイルは配布しない。

音楽・効果音は前史の主題と同系統のオリジナル計算生成。第三者の録音や楽曲は採用していない。発話の波形から作った包絡で音楽を下げる。原音、編集音声、音楽、効果音、混音原本、完成AACを分けて保管。高画質版と軽量版には同一のAACを再圧縮せず入れる。

## 出典と確認範囲
確認日：2026年10月15日。画像・図の転載はしていない。

R01：NASA『Habitable Zone』。大きさだけでなく恒星光と大気、地表の液体の水を考える概念を参照。\nhttps://science.nasa.gov/exoplanets/habitable-zone/

R02：NASA『Beginnings: Life on Our World and Others』。適切な大気のもとで液体の水を考えること、金星と火星の条件の違いを本文で確認。氷の下の海は今回の地表環境の比較とは別。\nhttps://science.nasa.gov/universe/search-for-life/beginnings-life-on-our-world-and-others/

R03：NASA Earth Observatory『Climate and Earth's Energy Budget』（2009）。反射、地表の放射、大気の吸収・再放射を確認。地球の平均的な収支の数値を無名惑星へ転載していない。\nhttps://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/

R04：国立天文台『A Day at the Beach for Life on Other Worlds』（2022）。液体の水がありうる帯にあっても、水や生命の実在を自動的に確定しないという区別を確認。\nhttps://www.nao.ac.jp/en/news/science/2022/20220930-dos.html

R05：ESA『Greenhouse effect, clouds and winds』。大気・雲による入射光の反射と、熱放射への働きが並存する例を参照。金星の数値を本模型へ移していない。\nhttps://www.esa.int/Science_Exploration/Space_Science/Venus_Express/Greenhouse_effect_clouds_and_winds

E01：本制作の比較模型。距離2倍に対する1/4は逆二乗則の算術。地形、水面、分子の目印、放射経路、帯の幅は説明用の制作設計。

音声：VOICEVOX:四国めたん。再利用者にも利用条件の遵守を求める。\nhttps://voicevox.hiroshiba.jp/term/\nhttps://zunko.jp/con_ongen_kiyaku.html

## 復旧と確認範囲
手元のコンテナ起動、最小コマンド、別セッション、二つのPython入口はClientErrorで失敗。許可されたGitHub Actionsで原音生成・ネイティブ描画・混音・全編検査を実行し、ショットごとに成果物を保存した。既存作品は変更していない。描画記録と完成映像を区別し、機械検査の結果はvalidation/final_validation.jsonに保存。

完成した映像を私が再生して目で見た最終点検、耳による全編試聴、投稿端末での見え方は未実施。画像は完成MP4から抽出済みで、ユーザーが比較できる。公開、投稿、再生リスト変更は行っていない。

## 実測結果
{json.dumps(reports,ensure_ascii=False,indent=2)}
'''
(ROOT/f'{STEM}_script_sources.md').write_text(doc,encoding='utf-8')
(ROOT/'README_制作メモ.md').write_text('HEION-P042 第1版\n\n台本・時刻の正本：timeline.json。原音：audio/raw。制作コード：code。\n再描画：このフォルダーをp042という名前で作業ディレクトリへ置き、コードのある環境で python p042/code/render.py shot 0（場面番号0〜11）。Python 3.11、numpy、scipy、Pillow、moderngl 5.12、glcontext 3.0、PyAV、FFmpeg、Noto Sans CJK JPとEGLが必要。書体は別途導入。\nネイティブ解像度の原ショットと音声を保存しているため、部分修正でも不要な再圧縮を避けられる。\n生成用エンジンのプログラムや音源モデル、書体本体はこのZIPに配布していない。\n',encoding='utf-8')
for path in (ROOT/'captions').glob('*'):shutil.copy2(path,OUT/path.name)
shutil.copy2(ROOT/f'{STEM}_script_sources.md',OUT/f'{STEM}_script_sources.md')
# Include a file-by-file manifest. Never include font binaries, engine models, or credentials.
files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.ttf','.otf','.ttc','.aac']]
inventory=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
(ROOT/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2));files.append(ROOT/'inventory.json')
package=OUT/f'{STEM}_production.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
    for p in files:z.write(p,Path('HEION-P042-v1')/p.relative_to(ROOT))
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
    for item in inventory:assert hashlib.sha256(z.read('HEION-P042-v1/'+item['path'])).hexdigest()==item['sha256']
summary['package']=dict(bytes=package.stat().st_size,files=len(files),sha256=sha(package),crc_and_manifest_pass=True)
(ROOT/'validation/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));Path('status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('FINAL_READY',json.dumps(summary,ensure_ascii=False),flush=True)
