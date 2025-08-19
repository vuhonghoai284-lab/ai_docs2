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
  original_text?: string;    // 新增：原文内容
  user_impact?: string;       // 新增：对用户的影响
  reasoning?: string;         // 新增：判定原因
  context?: string;           // 新增：上下文
  feedback_type?: 'accept' | 'reject';
  feedback_comment?: string;
}

export interface TaskDetail {
  task: Task;
  issues: Issue[];
}

export interface AIOutput {
  id: number;
  task_id: number;
  operation_type: string;
  section_title?: string;
  section_index?: number;
  input_text: string;
  raw_output: string;
  parsed_output?: any;
  status: string;
  error_message?: string;
  tokens_used?: number;
  processing_time?: number;
  created_at: string;
}