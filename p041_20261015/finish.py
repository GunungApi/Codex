"""Mux, inspect every frame, preserve original audio, package editable sources."""
from pathlib import Path
import json,hashlib,subprocess,zipfile,shutil,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import av
ROOT=Path('p041');OUT=Path('deliverables');OUT.mkdir(exist_ok=True)
P=json.loads((ROOT/'timeline.json').read_text());stem='heionreki_p041_v1'
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=ROOT/'clips/concat.txt';manifest.write_text(''.join(f"file 'shot_{s['id']:02d}.mp4'\n" for s in P['shots']))
master=ROOT/'audio/master.m4a';high=OUT/f'{stem}_high.mp4';light=OUT/f'{stem}_light.mp4'
run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(manifest),'-i',str(master),'-map','0:v:0','-map','1:a:0','-c','copy','-video_track_timescale','24000','-movflags','+faststart',str(high)])
run(['ffmpeg','-y','-v','error','-i',str(high),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-preset','slow','-crf','24','-c:a','copy','-movflags','+faststart',str(light)])

def check(path):
    inp=av.open(str(path));v=inp.streams.video[0];count=0;prev=None;dups=0;black=[];pts=[];allhash=set()
    for f in inp.decode(video=0):
        rgb=f.to_ndarray(format='rgb24');h=hashlib.sha256(rgb.tobytes()).hexdigest();allhash.add(h)
        if prev==h:dups+=1
        prev=h;pts.append(float(f.pts*f.time_base));small=rgb[::16,::16]
        if float(small.mean())<2 and float((small.max(-1)<5).mean())>.99:black.append(count)
        count+=1
    inp.close();assert count==P['frames'],(path,count,P['frames'])
    terr=max(abs(t-i/P['fps']) for i,t in enumerate(pts));assert terr<1e-4,terr
    aa=av.open(str(path));audio_frames=0;audio_samples=0
    for f in aa.decode(audio=0):audio_frames+=1;audio_samples+=f.samples
    aa.close();assert audio_frames>0
    r=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=10:print_format=json','-f','null','-']);s=r.stderr;m=json.loads(s[s.rfind('{'):])
    raw=ROOT/'validation'/f'{path.stem}.aac';run(['ffmpeg','-y','-v','error','-i',str(path),'-vn','-c:a','copy','-f','adts',str(raw)])
    result=dict(file=path.name,bytes=path.stat().st_size,sha256=sha(path),width=v.width,height=v.height,frames=count,duration=count/P['fps'],fps=P['fps'],decode_all=True,unique_images=len(allhash),consecutive_identical_frames=dups,black_candidates=black,max_timestamp_error=terr,audio_decoded_frames=audio_frames,audio_decoded_samples=audio_samples,audio_sha256=sha(raw),lufs=float(m['input_i']),true_peak_dbtp=float(m['input_tp']))
    assert abs(result['lufs']+16)<.5 and result['true_peak_dbtp']<=-1.5,result
    assert not black
    return result
reports=[check(high),check(light)];assert reports[0]['audio_sha256']==reports[1]['audio_sha256']
orig_aac=ROOT/'validation/master.aac';run(['ffmpeg','-y','-v','error','-i',str(master),'-c:a','copy','-f','adts',str(orig_aac)]);assert sha(orig_aac)==reports[0]['audio_sha256']
# Short review excerpt spans the age comparison and the 6.6-billion-year interval.
start=P['shots'][2]['start'];dur=P['shots'][3]['end']-start
run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(high),'-t',str(dur),'-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','21','-preset','slow','-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT/f'{stem}_age_preview.mp4')])
# Representative frames extracted from the final encoded MP4, not the source image cache.
folder=ROOT/'validation/final_samples';folder.mkdir(parents=True,exist_ok=True);tiles=[]
for shot in P['shots']:
    t=(shot['start']+shot['end'])/2;p=folder/f'shot_{shot["id"]:02d}.png'
    run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(high),'-frames:v','1',str(p)])
    im=Image.open(p).convert('RGB');im.thumbnail((270,480));tiles.append(im)
sheet=Image.new('RGB',(1080,480*math.ceil(len(tiles)/4)))
for i,im in enumerate(tiles):sheet.paste(im,((i%4)*270,(i//4)*480))
sheet.save(folder/'shot_sheet.jpg',quality=95)
(ROOT/'validation/final_validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
summary=dict(status='rendered_and_machine_verified',episode='P041',duration=P['duration'],frames=P['frames'],shots=len(P['shots']),captions=len(P['captions']),original_audio_segments=len(P['narration']),outputs=reports,actual_human_audio_listening=False,final_frame_visual_review_by_assistant=False,phone_platform_preview=False,local_container_unavailable=True)
(ROOT/'validation/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));Path('status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
script='\n\n'.join(f"### 語り{s['id']:02d}｜{s['start']:.3f}〜{s['end']:.3f}秒\n{s['text']}" for s in P['narration'])
sources='''## 出典と使った範囲
確認日：2026年10月15日。

R01：Campanteほか（2015）An ancient extrasolar system with five sub-Earth-size planets。
https://arxiv.org/abs/1501.06227
https://authors.library.caltech.edu/records/ftv0r-1qa84
原著の公開摘要・書誌を確認。主星年齢112±10億年、五つの通過惑星、太陽系より古い小型惑星系の存在を採用。本文PDFは今回の閲覧経路では取得できず、全表を精読したとはしない。2026年現在の唯一の最古記録とは呼ばない。

R02：NASA/JPL（2015年1月28日）古い五惑星系の発見。
https://www.jpl.nasa.gov/news/astronomers-discover-ancient-system-with-five-small-planets/
五惑星、短周期、年齢と星震学の関係を本文で照合。画像は転載していない。

R03：NASAの各惑星カタログ。
https://science.nasa.gov/exoplanet-catalog/kepler-444-b/
https://science.nasa.gov/exoplanet-catalog/kepler-444-c/
https://science.nasa.gov/exoplanet-catalog/kepler-444-d/
https://science.nasa.gov/exoplanet-catalog/kepler-444-e/
https://science.nasa.gov/exoplanet-catalog/kepler-444-f/
表示模型の半径、軌道距離、丸めた周期を照合。半径は地球比0.403、0.497、0.530、0.546、0.741。これを質量の比として使わない。大気・地表の成分・地形は観測していない。

E01：今回の説明模型と算術。
112億年−46億年＝66億年。2015年の主星の推定年齢を背景に、惑星系も同時期にできたとみなす比較。約±10億年の幅を保持。年齢と、今届く光が旅してきた時間を同一視しない。
主星Aと近傍五惑星に画角を限定し、遠方の伴星B・Cは表示しない。軌道は円・同一面の模式近似、位相は撮影用に選択したもの。2026年の精密な天体暦ではない。軌道図では星と惑星を拡大、サイズ比較では同じ半径倍率を使う。外観のクレーター・色は説明用の創作で、ケプラー444の撮影地図ではない。

音声利用条件：VOICEVOX:四国めたん。
https://voicevox.hiroshiba.jp/term/
https://zunko.jp/con_ongen_kiyaku.html
日本語書体は実行環境のNoto Sans CJK JPを参照。フォントファイルは配布しない。
'''
doc=f'''# 平穏暦全史・前史041
## 太陽が生まれる前から、五つの惑星が回っていた

第1版。音声・装飾字幕・音楽・効果音を合成した試写用動画。{P['duration']:.3f}秒、1080×1920、毎秒24コマ、{P['frames']}コマ。

## 今回の問い
太陽系より古い、小さな惑星を持つ星系は知られているか。第2巻P041の計画を継承し、ケプラー444の年齢・大きさ・軌道を分けて見せる。

## ナレーションと実音声時刻
{script}

## 動きと画面の磨き込み
年齢比較は二つの目盛りの現在をそろえ、112億年と46億年の長さを同じ倍率で示す。次の場面では太陽系誕生より前の66億年を独立して強調する。五惑星の大きさ比較、最内側と水星、最外側と金星を別々の場面へ分け、図を同時に詰め込まない。共通の時計による公転では、それぞれの周期比を保持し、最も外側の一周が語りの区間内に入るよう時間を合わせる。

## 立体表現と継承範囲
地形を持つ球面メッシュ、法線、表面の粒状材質、空間内のカメラ、五つの軌道、主星の表面の模様を新規制作した。1080×1920へ直接描画し、4サンプルの輪郭処理を使用。低解像度試作の拡大、静止画の拡大移動、生成画像、光学補間は採用していない。年齢の目盛りと数値は説明用の二次元表示。
前史040の制作記録・代表場面と基準第5版の比較画像はこの会話で確認した。実行環境の起動障害により、前史040の制作ZIPを新しい環境へ展開して流用したとはしない。声の設定、字幕の意匠、音声と時間軸を分ける手順を継承し、天体の模型・音楽は新規に構成した。

## 音声・発音と同期
四国めたん・ノーマル、話速1.01、音高−0.015、抑揚1.08、48kHzの原音6区間を生成した。原音の速度は編集で変更していない。各子音長・母音長を93.75Hzの合成フレームへ丸めて積算し、原音WAVのサンプル数との一致を検査。句読点に対応する実音素の区間から字幕を作り、文字数による等分割は使用しない。独立した音声認識文・単語時刻も原音と共に保管する。
ケプラー444は「ケプラー、よんよんよん」。百十二億年、四十六億年、六十六億歳、十日、水星、金星は読みを指定した。音素の点検と独立音声認識は、耳での自然さの確認と区別する。
音楽・効果音はオリジナルの計算生成。語りの実波形を使って発話中の背景音を下げ、別の混音原本を正規化。高画質版・軽量版へ同じAAC音声を再圧縮せず格納し、そのバイト一致を検査する。

{sources}

## 検証結果と未実施の確認
完成MP4の全コマ・音声の復号、コマ時刻、黒画面候補、同一画像の連続、原音と完成音声、字幕の文字幅、軌道線の終点と惑星位置を機械的に検査。実測値はvalidation/final_validation.json。
**この実行ではローカルの作業環境が起動できず、許可されたGitHub Actions上で描画・合成・検査した。完成動画の連続視聴、完成代表画像の目視確認、耳による全編試聴、投稿端末の確認は未実施。** 過去の作品の確認成功を今回の成功へ転記しない。検査用の完成動画から抜き出した画像はvalidation/final_samplesに保管。

## 再編集
正本はtimeline.json、素材はassets、原音はaudio/raw、描画はcode/render.py。全編の再生成はprepare.py→render.py proof→各shot→finish.py。用意した環境の依存関係はrequirements.txt。投稿・公開・再生リストの変更は行わない。
'''
(ROOT/f'{stem}_script_sources.md').write_text(doc,encoding='utf-8');shutil.copy2(ROOT/f'{stem}_script_sources.md',OUT)
(ROOT/'requirements.txt').write_text('numpy\nscipy\npillow\nmoderngl==5.12.0\nglcontext==3.0.0\nav\ntrimesh\nrequests\n')
(ROOT/'README.md').write_text('前史041の再編集用資料。システムにFFmpeg、Mesa/EGL、Noto Sans CJK JPを用意し、requirements.txtを導入する。原音を生成し直す必要はない。作業フォルダーの名前はp041。codeのPythonを同じ作業ディレクトリーで実行する。描画内容の限界・未実施検査は台本資料を参照。\n',encoding='utf-8')
for p in Path('p041_20261015').glob('*.py'):shutil.copy2(p,ROOT/'code'/p.name)
for p in (ROOT/'captions').iterdir():shutil.copy2(p,OUT)
# Geometry interchange export; renderer code remains the material/animation master.
try:
    import trimesh
    scene=trimesh.Scene()
    for i in range(5):
        m=np.load(ROOT/f'assets/globe_{i}.npz');mesh=trimesh.Trimesh(vertices=m['vertices']*DATA_RADIUS if False else m['vertices'],faces=m['triangles'],process=False)
        mesh.vertices*=.46*[.403,.497,.530,.546,.741][i];mesh.apply_translation([i*1.3,0,0]);scene.add_geometry(mesh,node_name=f'planet_{i+1}')
    scene.export(ROOT/'assets/five_planet_size_models.glb')
except ImportError:pass
inventory=[]
for p in sorted(ROOT.rglob('*')):
    if p.is_file():inventory.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)))
(ROOT/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
archive=OUT/f'{stem}_production.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            assert p.suffix.lower() not in ['.ttf','.otf','.ttc','.woff','.woff2']
            z.write(p,Path('HEION-P041-v1')/p.relative_to(ROOT))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;summary['package_members']=len(z.infolist())
summary['package_bytes']=archive.stat().st_size;summary['package_sha256']=sha(archive);Path('status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('COMPLETE',json.dumps(summary,ensure_ascii=False),flush=True)
