export interface FileItem {
  name: string;
  size: number;
  last_modified: string;
  has_translation: boolean;
  translation_name?: string;
}

export interface Task {
  id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  stage: string;
  progress: number;
  created_at: string;
  config: TranslationConfig;
  output_file?: string;
  error?: string;
}

export interface TranslationConfig {
  model: string;
  chunk_size: number;
  max_retries: number;
  temperature: number;
  timeout: number;
  include_toc: boolean;
  include_metadata: boolean;
}

export interface TaskResponse {
  success: boolean;
  task_id?: string;
  message: string;
  error?: string;
}

export interface PaperDownloadRequest {
  url: string;
  object_name?: string;
}

export interface TranslationRequest {
  object_name: string;
  config: TranslationConfig;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  name: string;
  message: string;
}