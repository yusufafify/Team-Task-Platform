export interface AssistantMessage {
  id: number
  role: 'user' | 'assistant'
  body: string
  created_at: string
}

export interface AssistantTurn {
  question: AssistantMessage
  answer: AssistantMessage
  cached: boolean
}
