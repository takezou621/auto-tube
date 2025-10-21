export type Audience = 'entry' | 'experienced' | 'investor';
export type Duration = 'short' | 'standard' | 'long';
export type Tone = 'trust' | 'energetic' | 'premium';

export interface CreateProjectPayload {
  title: string;
  location: string;
  highlight: string;
  audience: Audience;
  duration: Duration;
  callToAction: string;
  tone: Tone;
}

export interface ScriptSection {
  title: string;
  body: string;
}

export interface SceneOutline {
  cue: string;
  description: string;
}

export interface ProjectResponse extends CreateProjectPayload {
  id: string;
  createdAt: string;
  summary: string;
  sections: ScriptSection[];
  scenes: SceneOutline[];
}

export interface ProjectApiResponse {
  id: string;
  title: string;
  location: string;
  highlight: string;
  audience: Audience;
  duration: Duration;
  tone: Tone;
  call_to_action: string;
   created_at: string;
  summary: string;
  sections: ScriptSection[];
  scenes: SceneOutline[];
}
