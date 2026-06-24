import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000
})

export function assetUrl(path?: string | null): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_BASE_URL}${path}`
}

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { detail?: string })?.detail || error.message
  }
  return error instanceof Error ? error.message : '请求失败'
}

