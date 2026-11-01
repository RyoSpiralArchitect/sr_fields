export const dictionaries = {
  title: ['Field Observatory', '名づける前の観測室'],
  subtitle: ['Follow signals, read dialogue, and explore ways of responding.', '揺らぎを追い、言葉を読み、応答の仕方を試す。'],
  skip: ['Go to observations', '観測へ進む'], uiLanguage: ['Interface language', '画面の言語'],
  bridges: ['Explore a shared question', '問いで見比べる'],
  bridgeNote: ['Examples linked by a question. Signals and meaning remain different kinds of evidence.', '問いでつないだ例。数値と意味は別の尺度として読みます。'],
  open: ['Leaving meaning open', '保留と断定'], explicit: ['Responding to decisions', '明示への応答'], change: ['Following change', '変化の追跡'],
  tabs: ['Observation views', '観測する記録'], signals: ['Signal traces', '数値の軌跡'], dialogue: ['Dialogue progression', '言葉の経過'],
  pilot: ['Historical replies', '過去の返答'], workbench: ['Compose a prompt', 'プロンプトを組む'],
  scenario: ['Signal pattern', '信号の動き'], threshold: ['Abstention margin (arbitrary units)', '保留幅（任意単位）'],
  seedNote: ['Fixed first seed 1000 · First 32 steps excluded from metrics', '固定した最初の seed 1000 · 最初の32ステップは集計前の準備'],
  stable: ['Stable signal', '変わらない信号'], null: ['No signal', '信号なし'], walk: ['Slow drift', 'ゆっくり漂う'], abrupt: ['Abrupt reversals', '急な反転'], iid: ['Independent signs', '毎回入れ替わる'],
  latent: ['Generated signal', '生成した信号'], observation: ['Observation', '観測値'], memory: ['EMA history', '履歴 EMA'], always: ['0 · Always decide', '0 · 毎回判断'],
  traceTitle: ['Time series of the generated signal, observation and EMA history', '生成した信号・観測値・履歴EMAの時系列'],
  decisionTitle: ['Immediate and history-based decisions: positive, open, negative', '即時観測と履歴観測の判断。プラス、保留、マイナス'],
  immediateShort: ['Now', '即時'], memoryShort: ['EMA', '履歴'], openShort: ['Open', '保留'], decided: ['Decided', '判断した割合'], errorRate: ['Error among scored decisions', '判断した部分の誤り'], undefined: ['Undefined', '定義なし'],
  case: ['Dialogue', '対話'], stage: ['Visible stage', '見えている段階'], stageOne: ['Stage 1', '第1段階'], stageTwo: ['Stage 2', '第2段階'], stageThree: ['Stage 3', '第3段階'],
  dialogueNote: ['12 authored cases · 108 decisions · Author references are not independent ground truth', '作成した12対話・108応答 · 作者参照は独立した正解ではありません'],
  originalNote: ['Historical utterances and replies remain in their original Japanese. English titles are reading aids, not new experiment outputs.', '過去の発言と返答は日本語の原文を保持しています。英語の見出しは読むための補助であり、新しい実験結果ではありません。'],
  sameInput: ['Compare the same input', '同じ入力で見比べる'], pilotNote: ['Historical pilot: 17 replies and 1 missing response · No human ratings', '過去の実験：17応答・1欠測 · 人間評価は未実施'],
  pilotWarning: ['This pilot used older prompts containing source quotations. It does not evaluate the current public prompt pack.', 'この実験では原文の引用を含む旧プロンプトを使いました。ここで組める公開版プロンプトの評価とは異なります。'],
  reader: ['Reader', '読み手'], author: ['Author reference', '作者参照'], trajectory: ['Classification history · Hidden stages appear as —', '分類欄の経過 · 未表示の段階は —'],
  immediate: ['Forced binary', 'すぐ二択'], optional: ['Abstention allowed', '保留を選べる'], fixed_wait: ['Wait at stage 1', '最初だけ待つ'], reason: ['Classification reason', 'この分類の理由'],
  actualReplies: ['Actual replies at stage {stage}', '第{stage}段階の実際の返答'], baseline: ['Common instructions only', '共通指示のみ'], plain_rules: ['Policies in ordinary text', '通常文の方針'], field_pack: ['Source-linked Fields (old version)', '出典付きField（旧版）'],
  missing: ['Connection interrupted · No response received', '接続切断 · 返答未取得'],
  composeHeading: ['Choose and combine response policies', '応答の仕方を選んで組み合わせる'],
  composeIntro: ['Twelve proposed policies derived semantically from private sources. Select one, a mix, or all twelve.', '非公開の原典を手がかりに意味論的に書き下ろした12の方針。単一・組み合わせ・全部ONから選べます。'],
  preset: ['Starting combination', '組み合わせの出発点'], custom: ['Custom combination', '自由な組み合わせ'], mode: ['Prompt format', '渡し方'],
  structured: ['Names and JSON structure', '名前とJSON構造を添える'], plain: ['Same policies in ordinary text', '同じ方針を通常文で'],
  promptLanguage: ['System prompt language', 'system promptの言語'],
  languageNote: ['Interface and prompt languages are independent. Replies follow the input language unless you request otherwise.', '画面とプロンプトの言語は別々に選べます。特に指定しなければ、返答は入力の言語に合わせます。'],
  allOn: ['All on', '全部ON'], clear: ['Clear selection', '選択をクリア'], only: ['Only this', 'これだけ'],
  selectionCount: ['{count} of {total} selected', '{total}種類中 {count}種類を選択'], order: ['Prompt order', '渡す順番'],
  up: ['Move {name} earlier', '{name}を前へ'], down: ['Move {name} later', '{name}を後ろへ'], picker: ['Available Fields', '選べるField'],
  baselineSelection: ['Baseline sends common instructions only. Your selection is kept for switching back.', '共通指示のみを送ります。Fieldの選択は、切り替えたときのために残します。'],
  emptySelection: ['Select at least one Field, or switch to common instructions only.', 'Fieldを1つ以上選ぶか、「共通指示のみ」に切り替えてください。'],
  preview: ['Inspect the exact system prompt', '実際に渡すsystem promptを見る'], copy: ['Copy instructions', '指示をコピー'], download: ['Save prompt JSON', 'プロンプトJSONで保存'],
  input: ['Words or dialogue to try', '試したい言葉や対話'], run: ['Try this input once', 'この入力で1回試す'],
  privacy: ['Running sends the input and selected instructions to OpenAI. Records stay local and are not added to the public examples.', '実行時は入力と選んだ方針をOpenAIへ送信します。実行記録は手元に保存され、公開データには追加されません。'],
  about: ['About this observatory', 'この観測室について'],
  aboutText: ['Signals and dialogue cases are authored examples; API replies are saved trials. Choosing an abstention label and preserving uncertainty in actual wording are separate observations.', '数値は作成した信号、対話は作成した短い場面、API応答は保存済みの試行です。保留を選べることと、実際の言葉が意味を決めつけないことを分けて観察します。'],
  unevaluated: ['The current bilingual prompt pack is a semantic derivative. Its effects, cross-language equivalence and combination benefits have not been evaluated.', '現在の日英プロンプトは意味論的な派生版です。効果、言語間の意味の等価性、組み合わせの優位性は未評価です。'],
  manifest: ['Public data inventory', '公開データの記録'], loading: ['Loading…', '読み込み中…'], readOnly: ['Browse mode · API execution disabled', '閲覧モード · API実行は無効'], stopped: ['This session has stopped', 'この実行枠は停止しました'],
  requestCount: ['{used} / {limit} requests used', '実行 {used} / {limit} 回'], promptStatus: ['Public prompt · {language} · SHA-256 {hash} · Effectiveness untested', '公開プロンプト · {language} · SHA-256 {hash} · 効果は未評価'],
  copied: ['Instructions copied.', '指示をコピーしました。'], copyFailed: ['Copy unavailable. You can select and copy the displayed instructions.', 'コピーできませんでした。表示した指示を選択してコピーできます。'],
  waiting: ['Waiting for the reply…', '返答を待っています…'], currentReply: ['Reply from this trial', '今回の返答'], noReply: ['No reply was received.', '返答を取得できませんでした。'], recorded: ['One trial was recorded.', '1回の試行を記録しました。'],
  failureStopped: ['The trial stopped. It will not be retried automatically.', '試行を停止しました。自動で再送しません。'], loadError: ['Could not load the observatory.', '観測室を読み込めませんでした。'],
  invalid_request: ['Check the input, selection and execution budget.', '入力・選択・実行上限を確認してください。'], request_failed: ['The operation could not be completed. No automatic retry will be made.', '処理を完了できませんでした。自動で再送しません。'],
  'quiet-dialogue': ['Small changes and openness', '小さな違いと保留'], 'grounded-ideas': ['Grounded imagination', '足場のある発想'], 'meaning-crossing': ['Meaning across difference', '意味の受け渡し'],
  'open-exploration': ['Open-ended exploration', '方向を開いた探索'], 'all-fields': ['All Fields', 'すべてのField'], 'care-and-pace': ['Care and pace', '受け止め方とペース'], 'source-aware': ['Source-aware expression', '出所を保つ表現'], 'rebuild-and-revisit': ['Rebuild and revisit', '組み直しと再検討'],
  dialogueTitles: [
    ['Reception request I', 'Reception request II', 'External publication I', 'External publication II', 'Friday review', 'Photo usage', 'Submission and meeting deadlines', 'Project response', 'Attendance with a condition', 'Application and review result', 'Acceptance to withdrawal', 'Publication ban to permission'],
    ['受付の依頼①', '受付の依頼②', '社外掲載①', '社外掲載②', '金曜のレビュー', '写真の利用範囲', '提出と打合せの期限', '企画への返事', '人数が条件の参加', '申請と審査結果', '引受けから辞退へ', '掲載禁止から許可へ']],
  pilotTitles: [
    ['An unnamed concern', 'A first step in 30 minutes', 'A desk that remembers rain', 'Announcing a decision to be absent', 'Confirmed event details', 'A reading group with constraints'],
    ['まだ言えない引っかかり', '30分で始める一歩', '雨を覚えている机', '欠席という決定を伝える', '確定した案内', '制約のある読書会']]
};
let language = 'en';
export const getLanguage = () => language;
export function t(key, values = {}) {
  const value = dictionaries[key]?.[language === 'ja' ? 1 : 0] ?? key;
  return typeof value === 'string' ? value.replace(/\{(\w+)\}/g, (_, k) => values[k] ?? `{${k}}`) : value;
}
export function setLanguage(next) {
  language = next === 'ja' ? 'ja' : 'en';
  document.documentElement.lang = language;
  document.title = t('title');
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
}
