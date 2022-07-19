from janome.tokenizer import Tokenizer
import zipfile
import os.path, urllib.request as req
import MeCab
import pandas as pd
import re

# ZIPファイルをダウンロード --- (※1)
url = "https://www.aozora.gr.jp/cards/000035/files/301_ruby_5915.zip" # ここを作品に合わせて入れ替える
local = "301_ruby_5915.zip" # ここを作品に合わせて入れ替える
if not os.path.exists(local):
    print("ZIPファイルをダウンロード")
    req.urlretrieve(url, local)

# ZIPファイル内のテキストファイルを読む --- (※2)
zf = zipfile.ZipFile(local, 'r') # zipファイルを読む
fp= zf.open('ningen_shikkaku.txt', 'r') # アーカイブ内のテキストを読む(作品名に合わせる)
bindata = fp.read()
text = bindata.decode('shift_jis') # テキストがShift_JISなのでデコード

# テキストの先頭にあるヘッダとフッタを削除 --- (※2)
text = re.split(r'\-{5,}',text)[2]
text = re.split(r'底本：', text)[0]
text = text.strip()

# 形態素解析 --- (※3)
t = Tokenizer()
results = []
# テキストを一行ずつ処理する
lines = text.split("\r\n")
for line in lines:
    s = line
    s = s.replace('｜', '')
    s = re.sub(r'《.+?》', '', s) # ルビを削除
    s = re.sub(r'［＃.+?］', '', s) # 入力注を削除
    tokens = t.tokenize(s) # 形態素解析
    # 必要な語句だけを対象とする --- (※4)
    r = []
    for tok in tokens:
        if tok.base_form == "*": # 単語の基本系を採用
            w = tok.surface
        else:
            w = tok.base_form
        ps = tok.part_of_speech # 品詞情報
        hinsi = ps.split(',')[0]
        if hinsi in ['名詞', '形容詞', '動詞', '記号']:
            r.append(w)
    rl = (" ".join(r)).strip()
    results.append(rl)

# 日本語評価極性辞書をダウンロード
req.urlretrieve('https://www.cl.ecei.tohoku.ac.jp/resources/sent_lex/wago.121808.pn', 'wago.121808.pn')

# 日本語評価極性辞書を読み込む
wago = pd.read_csv('wago.121808.pn', header=None, sep='\t')

# 単語とスコアを対応させる辞書を作成
word2score = {}
values = {'ポジ（経験）': 1, 'ポジ（評価）': 1, 'ネガ（経験）': -1, 'ネガ（評価）': -1}
for word, label in zip(wago.loc[:, 1], wago.loc[:, 0]):
    word2score[word] = values[label]

# 各文章のスコアを算出
score = 0
size = 0
size_all = 0
size_line = 0
scores = []
lines = []
for words in results:
  www = words.split(' ')
  score_line = 0
  for word in www:
    size_all += 1
    if word in word2score:
       print("単語：", end="")
       print(word, end=" ")
       print("スコア：", end="")
       print(word2score[word])
       score += word2score[word]
       score_line += word2score[word]
       size += 1
  if score_line != 0:
    size_line += 1
    lines.append(size_line)
    scores.append(score)

scores_df = pd.DataFrame({
    'lines': lines,
    'score': scores})
scores_df.to_csv("output_shikkaku.csv", encoding="shift_jis") 

# 合計スコアを単語数で割る

print("全体の単語数：", end="")
print(size_all)
print("合計スコア：", end="")
print(score, end=" ")
print("スコア付き単語数：", end="")
print(size)

if size == 0:
 size = 1

score = score / size

print("平均スコア：", end="")
print(score)