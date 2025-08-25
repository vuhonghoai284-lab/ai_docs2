// 类型定义
export interface Task {
  id: number;
  title: string;
  file_name: string;
  file_size?: number;
  file_type?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  issue_count?: number;  // 新增：问题数量
  model_label?: string;   // 新增：模型名称
  document_chars?: number; // 新增：文档字符数
  processing_time?: number; // 新增：处理耗时(秒)
  created_at: string;
  completed_at?: string;
  error_message?: string;
  created_by?: string; // 新增：创建人ID
  created_by_name?: string; // 新增：创建人名称
  created_by_type?: string; // 新增：创建人类型
  user_id?: number; // 新增：用户ID
  file_id?: number; // 新增：文件ID
  ai_model_id?: number; // 新增：AI模型ID
}

export interface Issue {
  id: number;
  issue_type: string;
  description: string;
  location: string;
  severity: string;
  confidence?: number;        // 新增：模型置信度 (0.0-1.0)
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