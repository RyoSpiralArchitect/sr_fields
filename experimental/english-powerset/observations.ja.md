# 12個のFieldで、返す一言はどう変わったか

「みんなが笑った場面を、帰り道にも思い返していた。嫌だったのかは、自分でもわからない」。この一つの英語対話について、Bの次の一言をGPT-4.1 miniに書いてもらった。12個のFieldの全4,095組に、すべてOFFの対照を追加。各条件を同じ3つのseedで1回ずつ試し、**12,288件すべて**の英文が揃った。使用量を公開Batch料金で換算すると **約2.10米ドル**。

いちばん差が大きかったのは、GentleFieldを足したときの「もう少し話す？」という聞き返しだった。他の11個とseedが同じ6,144組を比べると、疑問符のある返答は **64.01% → 90.74%（+26.73ポイント）**。seedを分けても+23.78〜+28.66ポイントで、話すかどうかを相手に委ねる定型表現も+21.01ポイントだった。HeartFieldではその定型表現が+15.84ポイント、長さが平均+1.58語。ThresholdFieldでは疑問符が−7.49ポイントだった。

**組み合わせにも差がある。** DreamFieldがOFFのとき、GentleFieldを足すと質問率は70.12%から91.34%へ。DreamFieldがONのときは57.91%から90.14%へ。GentleFieldによる増え幅は後者が11.00ポイント大きい。両方ONの質問率そのものが最高、という意味ではない。

たとえばseed 202でDreamFieldだけを基準にした、実際の一組：

| 条件 | Bの返答（原文） |
| --- | --- |
| DreamField | Maybe it means it affected you more than you realize. |
| DreamField ＋ GentleField | It sounds like it left an impression—do you want to talk more about it? |

「名づけを保留できたか」は、単語の数だけでは判定できなかった。事前に決めた感情語が出たのは全体で **21件（0.17%）**。一方で実際の返答には *“Would you like to talk more about what made you uncomfortable?”* もある。話す選択を相手に渡しながら「居心地が悪かった」という解釈を置いている。反対に、上の表の1行目は感情語を使わずに相手の内面を推測する。次に読むなら、「聞き返したか」と「本人の言っていないことを前提にしたか」を別々に見るのがよい。

12,288件の英文は、大文字小文字・句読点などをそろえると736種類の単語列になった。最多の一文は696回出ている。この一場面で見えたのは、Fieldごとに特定の言い回しが選ばれやすくなる傾向。別の対話でも再現するか、話し手にとって望ましいかはまだ測っていない。

[英語の詳報・検証と限界](observations.md) · [主要3指標の図](results/primary-contrasts.svg) · [全12個の比較](results/field-contrasts.csv) · [全66ペア](results/pair-interactions.csv) · [データの読み方](results/README.md)
