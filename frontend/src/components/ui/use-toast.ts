import { useState, useCallback } from 'react';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

let toastListeners: Array<(toasts: Toast[]) => void> = [];
let toastList: Toast[] = [];

function notify() {
  toastListeners.forEach(l => l([...toastList]));
}

export function toast({ title, description, variant = 'default' }: Omit<Toast, 'id'>) {
  const id = Math.random().toString(36).slice(2);
  toastList = [...toastList, { id, title, description, variant }];
  notify();
  setTimeout(() => {
    toastList = toastList.filter(t => t.id !== id);
    notify();
  }, 4000);
}

export function useToast() {
  const [toasts] = useState<Toast[]>([]);
  const subscribe = useCallback((listener: (t: Toast[]) => void) => {
    toastListeners.push(listener);
    return () => { toastListeners = toastListeners.filter(l => l !== listener); };
  }, []);
  return { toasts, subscribe, toast };
}