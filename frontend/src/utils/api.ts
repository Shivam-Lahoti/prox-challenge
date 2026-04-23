import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  message: string;
  artifacts?: Array<{
    type: string;
    data: any;
  }>;
  images?: string[];
  conversation_id: string;
}

export const sendMessage = async (
  message: string,
  conversationId?: string
): Promise<ChatResponse> => {
  const response = await axios.post(`${API_BASE_URL}/chat`, {
    message,
    conversation_id: conversationId,
  });
  return response.data;
};

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};