import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchProjects, fetchStoryboard, generateProjectAudio, mapProjectResponse, safeParseError } from './projects';
import type { ProjectApiResponse } from '../types/project';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('mapProjectResponse', () => {
  it('camelCase に変換できる', () => {
    const apiResponse: ProjectApiResponse = {
      id: '1234',
      title: 'タイトル',
      location: '所在地',
      highlight: '魅力',
      audience: 'entry',
      duration: 'short',
      tone: 'trust',
      call_to_action: '資料請求はこちら',
      created_at: '2024-01-01T00:00:00Z',
      summary: 'サマリ',
      sections: [{ title: '導入', body: '本文' }],
      scenes: [{ cue: '導入', description: '説明' }],
    };

    const result = mapProjectResponse(apiResponse);
    expect(result.callToAction).toBe('資料請求はこちら');
    expect(result.sections).toHaveLength(1);
  });
});

describe('safeParseError', () => {
  it('detail が配列のときメッセージを結合する', async () => {
    const response = new Response(
      JSON.stringify({ detail: [{ msg: 'タイトルは2文字以上' }, { msg: 'CTAを入力してください' }] }),
      {
        status: 422,
        headers: { 'Content-Type': 'application/json' },
      },
    );

    await expect(safeParseError(response)).resolves.toBe('タイトルは2文字以上 / CTAを入力してください');
  });

  it('JSONでない場合はHTTPステータスを返す', async () => {
    const response = new Response('error', { status: 500 });
    await expect(safeParseError(response)).resolves.toBe('APIエラー: 500');
  });
});

describe('generateProjectAudio', () => {
  it('音声Blobとファイル名を返す', async () => {
    const response = new Response('audio-data', {
      status: 200,
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Disposition': 'attachment; filename="demo.mp3"',
      },
    });
    vi.spyOn(global, 'fetch').mockResolvedValue(response as unknown as Response);

    const result = await generateProjectAudio('demo-id');
    expect(result.contentType).toBe('audio/mpeg');
    expect(result.filename).toBe('demo.mp3');
    await expect(result.blob.text()).resolves.toBe('audio-data');
  });

  it('エラー時に例外を投げる', async () => {
    const errorResponse = new Response(
      JSON.stringify({ detail: 'エラーが発生しました' }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      },
    );
    vi.spyOn(global, 'fetch').mockResolvedValue(errorResponse as unknown as Response);

    await expect(generateProjectAudio('demo-id')).rejects.toThrow('エラーが発生しました');
  });
});

describe('fetchProjects', () => {
  it('一覧を取得し ProjectResponse 配列に変換する', async () => {
    const payload = [
      {
        id: '1',
        title: 'タイトル',
        location: '東京',
        highlight: '魅力',
        audience: 'entry',
        duration: 'short',
        tone: 'trust',
        call_to_action: '資料請求はこちら',
        created_at: '2024-01-01T00:00:00Z',
        summary: 'サマリ',
        sections: [],
        scenes: [],
      },
    ];
    const response = new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    vi.spyOn(global, 'fetch').mockResolvedValue(response as unknown as Response);

    const results = await fetchProjects();
    expect(results).toHaveLength(1);
    expect(results[0].callToAction).toBe('資料請求はこちら');
  });

  it('エラー時は例外を投げる', async () => {
    const response = new Response('error', { status: 500 });
    vi.spyOn(global, 'fetch').mockResolvedValue(response as unknown as Response);

    await expect(fetchProjects()).rejects.toThrow('APIエラー: 500');
  });
});

describe('fetchStoryboard', () => {
  it('APIレスポンスをStoryBoardItem配列へ変換する', async () => {
    const response = new Response(
      JSON.stringify(
        {
          items: [
            {
              scene: '導入 (1/3)',
              shot_type: 'タイトルアニメーション',
              broll_idea: 'B-roll A',
              key_message: '概要',
              overlay_text: 'テロップ',
            },
          ],
        }
      ),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    );
    vi.spyOn(global, 'fetch').mockResolvedValue(response as unknown as Response);

    const storyboard = await fetchStoryboard('demo');
    expect(storyboard).toHaveLength(1);
    expect(storyboard[0].shotType).toBe('タイトルアニメーション');
  });

  it('エラー時は例外を投げる', async () => {
    const response = new Response('oops', { status: 404 });
    vi.spyOn(global, 'fetch').mockResolvedValue(response as unknown as Response);

    await expect(fetchStoryboard('demo')).rejects.toThrow('APIエラー: 404');
  });
});
