import { CreateProjectPayload, ProjectApiResponse, ProjectResponse } from '../types/project';
import type { StoryboardItem } from '../types/storyboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function createProject(payload: CreateProjectPayload): Promise<ProjectResponse> {
  const response = await fetch(`${API_BASE_URL}/api/projects/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: payload.title,
      location: payload.location,
      highlight: payload.highlight,
      audience: payload.audience,
      duration: payload.duration,
      call_to_action: payload.callToAction,
      tone: payload.tone,
    }),
  });

  if (!response.ok) {
    const message = await safeParseError(response);
    throw new Error(message);
  }

  const data = (await response.json()) as ProjectApiResponse;
  return mapProjectResponse(data);
}

export async function generateProjectAudio(projectId: string): Promise<{
  blob: Blob;
  contentType: string;
  filename: string;
}> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/tts`, {
    method: 'POST',
  });

  if (!response.ok) {
    const message = await safeParseError(response);
    throw new Error(message);
  }

  const contentType = response.headers.get('content-type') ?? 'audio/mpeg';
  const filename = parseFilename(response.headers.get('content-disposition')) ?? `${projectId}.mp3`;
  const blob = await response.blob();
  return { blob, contentType, filename };
}

export async function fetchProjects(): Promise<ProjectResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/projects/`);

  if (!response.ok) {
    const message = await safeParseError(response);
    throw new Error(message);
  }

  const data = (await response.json()) as ProjectApiResponse[];
  return data.map(mapProjectResponse);
}

export async function fetchStoryboard(projectId: string): Promise<StoryboardItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/storyboard`);

  if (!response.ok) {
    const message = await safeParseError(response);
    throw new Error(message);
  }

  const data = (await response.json()) as { items: Array<{
    scene: string;
    shot_type: string;
    broll_idea: string;
    key_message: string;
    overlay_text: string;
  }> };

  return data.items.map((item) => ({
    scene: item.scene,
    shotType: item.shot_type,
    brollIdea: item.broll_idea,
    keyMessage: item.key_message,
    overlayText: item.overlay_text,
  }));
}

export function mapProjectResponse(data: ProjectApiResponse): ProjectResponse {
  return {
    id: data.id,
    title: data.title,
    location: data.location,
    highlight: data.highlight,
    audience: data.audience,
    duration: data.duration,
    tone: data.tone,
    callToAction: data.call_to_action,
    createdAt: data.created_at,
    summary: data.summary,
    sections: data.sections,
    scenes: data.scenes,
  };
}

export async function safeParseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (body?.detail) {
      return Array.isArray(body.detail)
        ? body.detail.map((item: { msg?: string }) => item.msg ?? '入力エラー').join(' / ')
        : String(body.detail);
    }
  } catch (_) {
    // JSON で無い場合は fallback
  }
  return `APIエラー: ${response.status}`;
}

function parseFilename(disposition: string | null): string | null {
  if (!disposition) return null;
  const match = disposition.match(/filename="?(?<name>[^";]+)"?/);
  return match?.groups?.name ?? null;
}
