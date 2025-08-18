// 类型定义
export interface Task {
  id: number;
  title: string;
  file_name: string;
  file_size: number;
  file_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface Issue {
  id: number;
  issue_type: string;
  description: string;
  location: string;
  severity: string;
  suggestion: string;
  feedback_type?: 'accept' | 'reject';
  feedback_comment?: string;
}

export interface TaskDetail {
  task: Task;
  issues: Issue[];
}