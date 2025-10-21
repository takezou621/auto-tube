import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { createProject, fetchProjects, fetchStoryboard, generateProjectAudio } from '../services/projects';
import type { Audience, Duration, ProjectResponse, Tone } from '../types/project';
import type { StoryboardItem } from '../types/storyboard';

interface FormState {
  title: string;
  location: string;
  highlight: string;
  audience: Audience;
  duration: Duration;
  callToAction: string;
  tone: Tone;
}

const initialFormState: FormState = {
  title: '湾岸タワーレジデンス38F ラグジュアリープラン',
  location: '東京都江東区豊洲エリア',
  highlight: '湾岸再開発の波に乗り想定利回り4.2%、夜景特化の付加価値で差別化',
  audience: 'entry',
  duration: 'standard',
  callToAction: 'まずは無料オンライン相談で、投資戦略を一緒に設計しましょう',
  tone: 'trust',
};

export default function Home() {
  const [form, setForm] = useState<FormState>(initialFormState);
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioFilename, setAudioFilename] = useState<string | null>(null);
  const [history, setHistory] = useState<ProjectResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [storyboard, setStoryboard] = useState<StoryboardItem[]>([]);
  const [storyboardLoading, setStoryboardLoading] = useState(false);
  const [storyboardError, setStoryboardError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const result = await fetchProjects();
      setHistory(result);
    } catch (err) {
      if (err instanceof Error) {
        setHistoryError(err.message);
      } else {
        setHistoryError('履歴の取得に失敗しました');
      }
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const handleChange = (key: keyof FormState) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await createProject(form);
      setProject(result);
      setAudioUrl(null);
      setAudioFilename(null);
      setAudioError(null);
      await loadHistory();
    } catch (err) {
      setProject(null);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('予期せぬエラーが発生しました');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAudio = async () => {
    if (!project) return;
    setAudioLoading(true);
    setAudioError(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    try {
      const result = await generateProjectAudio(project.id);
      const url = URL.createObjectURL(result.blob);
      setAudioUrl(url);
      setAudioFilename(result.filename);
    } catch (err) {
      if (err instanceof Error) {
        setAudioError(err.message);
      } else {
        setAudioError('音声生成に失敗しました');
      }
    } finally {
      setAudioLoading(false);
    }
  };

  const handleSelectHistory = (item: ProjectResponse) => {
    setProject(item);
    setForm({
      title: item.title,
      location: item.location,
      highlight: item.highlight,
      audience: item.audience,
      duration: item.duration,
      callToAction: item.callToAction,
      tone: item.tone,
    });
    setAudioLoading(false);
    setAudioError(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioUrl(null);
    setAudioFilename(null);
  };

  useEffect(() => {
    if (!project) {
      setStoryboard([]);
      setStoryboardError(null);
      setStoryboardLoading(false);
      return;
    }
    setStoryboardLoading(true);
    setStoryboardError(null);
    void fetchStoryboard(project.id)
      .then(setStoryboard)
      .catch((err: unknown) => {
        if (err instanceof Error) {
          setStoryboardError(err.message);
        } else {
          setStoryboardError('ストーリーボードの取得に失敗しました');
        }
      })
      .finally(() => setStoryboardLoading(false));
  }, [project]);

  const callToActionPreview = useMemo(() => {
    return form.callToAction || 'クロージングで伝えるメッセージを入力してください';
  }, [form.callToAction]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-widest text-slate-400">AUTO TUBE / for Real Estate Investors</p>
            <h1 className="text-3xl font-semibold text-white sm:text-4xl">不動産投資YouTube 自動生成ワークスペース</h1>
          </div>
          <div className="rounded-md bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">
            ステップ: 入力 → 台本生成 → 音声化
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-8 px-6 py-10 lg:grid-cols-[360px_1fr]">
        <section className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl shadow-black/20">
          <h2 className="text-lg font-semibold text-white">ステップ1: プロジェクト入力</h2>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <fieldset className="space-y-2">
              <label className="block text-sm text-slate-300" htmlFor="title">
                物件/企画タイトル
              </label>
              <input
                id="title"
                required
                value={form.title}
                onChange={handleChange('title')}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              />
            </fieldset>

            <fieldset className="space-y-2">
              <label className="block text-sm text-slate-300" htmlFor="location">
                ロケーション
              </label>
              <input
                id="location"
                required
                value={form.location}
                onChange={handleChange('location')}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              />
            </fieldset>

            <fieldset className="space-y-2">
              <label className="block text-sm text-slate-300" htmlFor="highlight">
                アピールポイント（150字以内）
              </label>
              <textarea
                id="highlight"
                required
                maxLength={200}
                value={form.highlight}
                onChange={handleChange('highlight')}
                className="h-28 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              />
            </fieldset>

            <fieldset className="grid gap-2">
              <label className="block text-sm text-slate-300" htmlFor="audience">
                想定視聴者
              </label>
              <select
                id="audience"
                value={form.audience}
                onChange={handleChange('audience')}
                className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              >
                <option value="entry">初心者向け</option>
                <option value="experienced">経験者向け</option>
                <option value="investor">富裕層向け</option>
              </select>
            </fieldset>

            <fieldset className="grid gap-2">
              <label className="block text-sm text-slate-300" htmlFor="duration">
                動画尺
              </label>
              <select
                id="duration"
                value={form.duration}
                onChange={handleChange('duration')}
                className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              >
                <option value="short">ショート (~45秒)</option>
                <option value="standard">スタンダード (~90秒)</option>
                <option value="long">ロング (~150秒)</option>
              </select>
            </fieldset>

            <fieldset className="grid gap-2">
              <label className="block text-sm text-slate-300" htmlFor="tone">
                トーン
              </label>
              <select
                id="tone"
                value={form.tone}
                onChange={handleChange('tone')}
                className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              >
                <option value="trust">信頼重視</option>
                <option value="energetic">エネルギッシュ</option>
                <option value="premium">プレミアム</option>
              </select>
            </fieldset>

            <fieldset className="space-y-2">
              <label className="block text-sm text-slate-300" htmlFor="cta">
                クロージング CTA
              </label>
              <textarea
                id="cta"
                required
                maxLength={120}
                value={form.callToAction}
                onChange={handleChange('callToAction')}
                className="h-20 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              />
            </fieldset>

            {error && (
              <div className="rounded-md border border-rose-500/70 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? '生成中…' : '台本を生成する'}
            </button>

            <p className="text-xs text-slate-500">
              送信するとバックエンドの FastAPI がテンプレートベースで台本とシーン指示を返します。
            </p>
          </form>
        </section>

        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-lg shadow-black/10">
            <h2 className="text-lg font-semibold text-white">ステップ2: 台本プレビュー</h2>
            {project ? (
              <div className="mt-4 space-y-4">
                <div className="rounded border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                  <p className="font-semibold">サマリ</p>
                  <p className="mt-1 leading-relaxed text-emerald-50/90">{project.summary}</p>
                </div>
                <div className="space-y-3">
                  {project.sections.map((section) => (
                    <article key={section.title} className="rounded-md border border-slate-800 bg-slate-950/80 px-4 py-3">
                      <h3 className="text-sm font-semibold text-white">{section.title}</h3>
                      <p className="mt-1 text-sm leading-relaxed text-slate-200">{section.body}</p>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mt-4 rounded-md border border-slate-800 bg-slate-950/70 px-4 py-6 text-sm text-slate-400">
                生成結果がここに表示されます。フォームを入力して「台本を生成する」をクリックしてください。
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-inner shadow-black/20">
            <h2 className="text-lg font-semibold text-white">ステップ3: シーン＆CTAメモ</h2>
            <div className="mt-4 space-y-3">
              <div className="rounded-md border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-200">
                <p className="font-semibold text-white">クロージング案</p>
                <p className="mt-1 leading-relaxed text-slate-200">{callToActionPreview}</p>
              </div>
              {project && (
                <ul className="space-y-2 text-sm text-slate-300">
                  {project.scenes.map((scene) => (
                    <li key={scene.cue} className="rounded-md border border-slate-800 bg-slate-950/60 px-4 py-3">
                      <p className="font-semibold text-white">{scene.cue}</p>
                      <p className="text-slate-300">{scene.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-inner shadow-black/20">
            <h2 className="text-lg font-semibold text-white">ステップ4: 音声生成</h2>
            <div className="mt-4 space-y-4">
              <button
                type="button"
                onClick={handleGenerateAudio}
                disabled={!project || audioLoading}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {audioLoading ? '音声生成中…' : 'ナレーション音声を生成する'}
              </button>
              {audioError && (
                <div className="rounded-md border border-rose-500/70 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
                  {audioError}
                </div>
              )}
              {audioUrl ? (
                <div className="space-y-3">
                  <audio controls className="w-full" src={audioUrl}>
                    お使いのブラウザでは音声を再生できません。
                  </audio>
                  <a
                    href={audioUrl}
                    download={audioFilename ?? 'autotube.mp3'}
                    className="inline-flex items-center gap-2 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200 hover:bg-emerald-500/20"
                  >
                    音声ファイルをダウンロード
                  </a>
                </div>
              ) : (
                <p className="text-sm text-slate-400">台本を生成すると音声化できます。</p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-inner shadow-black/20">
            <h2 className="text-lg font-semibold text-white">ステップ5: 生成履歴</h2>
            <div className="mt-4 space-y-3">
              {historyLoading && <p className="text-sm text-slate-400">履歴を読み込み中...</p>}
              {historyError && (
                <div className="rounded-md border border-rose-500/70 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
                  {historyError}
                </div>
              )}
              {!historyLoading && !historyError && history.length === 0 && (
                <p className="text-sm text-slate-400">まだ履歴がありません。台本を生成するとここに表示されます。</p>
              )}
              {!historyLoading && !historyError && history.length > 0 && (
                <ul className="space-y-2">
                  {history.map((item) => {
                    const isActive = project?.id === item.id;
                    const created = new Date(item.createdAt).toLocaleString('ja-JP');
                    return (
                      <li
                        key={item.id}
                        className={`rounded-md border px-4 py-3 text-sm transition ${
                          isActive
                            ? 'border-emerald-500 bg-emerald-500/10 text-emerald-100'
                            : 'border-slate-800 bg-slate-950/60 text-slate-200 hover:bg-slate-950/80'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="font-semibold text-white">{item.title}</p>
                            <p className="text-xs text-slate-400">{created}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleSelectHistory(item)}
                            className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200 hover:bg-emerald-500/20"
                          >
                            読み込む
                          </button>
                        </div>
                        <p className="mt-2 text-xs text-slate-300">
                          {item.highlight}
                        </p>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 shadow-inner shadow-black/20">
            <h2 className="text-lg font-semibold text-white">ステップ6: ストーリーボード</h2>
            <div className="mt-4 space-y-3">
              {!project && <p className="text-sm text-slate-400">履歴または新規生成でプロジェクトを選択すると表示されます。</p>}
              {project && storyboardLoading && <p className="text-sm text-slate-400">ストーリーボードを生成中...</p>}
              {project && storyboardError && (
                <div className="rounded-md border border-rose-500/70 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
                  {storyboardError}
                </div>
              )}
              {project && !storyboardLoading && !storyboardError && storyboard.length > 0 && (
                <div className="space-y-2">
                  {storyboard.map((item, idx) => (
                    <article key={`${item.scene}-${idx}`} className="rounded-md border border-slate-800 bg-slate-950/70 px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <h3 className="text-sm font-semibold text-white">{item.scene}</h3>
                        <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-200">{item.shotType}</span>
                      </div>
                      <p className="mt-2 text-xs text-slate-300">B-roll案: {item.brollIdea}</p>
                      <p className="text-xs text-slate-300">キー: {item.keyMessage}</p>
                      <p className="text-xs text-slate-400">テロップ: {item.overlayText}</p>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
