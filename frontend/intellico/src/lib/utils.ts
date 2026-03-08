import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Cleans up markdown formatting and formats text for display
 * Removes markdown characters and converts them to plain text with proper formatting
 */
export function cleanMarkdown(text: string): string {
  if (!text) return "";

  return text
    // Remove header markers (#, ##, etc.) but keep the text
    .replace(/^#{1,6}\s+/gm, '')
    // Remove bold markers (**text** or __text__)
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    // Remove italic markers (*text* or _text_)
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_(.*?)_/g, '$1')
    // Remove strikethrough markers (~~text~~)
    .replace(/~~(.*?)~~/g, '$1')
    // Remove code markers (inline `code` and block ```code```)
    .replace(/`([^`]+)`/g, '$1')
    .replace(/```[\s\S]*?```/g, '')
    // Remove blockquote markers (>)
    .replace(/^>\s+/gm, '')
    // Remove link markers [text](url) - keep the text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // Clean up extra whitespace
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
