import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface AnnotationSession {
  id: string;
  user_id?: string;
  image_name: string;
  image_data: string;
  boxes_data: string;
  created_at: string;
  updated_at: string;
}

export async function saveSession(
  imageName: string,
  imageData: string,
  boxesData: string
): Promise<string | null> {
  try {
    const { data, error } = await supabase
      .from('annotation_sessions')
      .insert([
        {
          image_name: imageName,
          image_data: imageData,
          boxes_data: boxesData,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ])
      .select('id')
      .single();

    if (error) {
      console.error('Error saving session:', error);
      return null;
    }
    return data?.id || null;
  } catch (err) {
    console.error('Failed to save session:', err);
    return null;
  }
}

export async function loadSession(sessionId: string): Promise<AnnotationSession | null> {
  try {
    const { data, error } = await supabase
      .from('annotation_sessions')
      .select('*')
      .eq('id', sessionId)
      .single();

    if (error) {
      console.error('Error loading session:', error);
      return null;
    }
    return data as AnnotationSession;
  } catch (err) {
    console.error('Failed to load session:', err);
    return null;
  }
}

export async function updateSession(
  sessionId: string,
  boxesData: string
): Promise<boolean> {
  try {
    const { error } = await supabase
      .from('annotation_sessions')
      .update({
        boxes_data: boxesData,
        updated_at: new Date().toISOString(),
      })
      .eq('id', sessionId);

    if (error) {
      console.error('Error updating session:', error);
      return false;
    }
    return true;
  } catch (err) {
    console.error('Failed to update session:', err);
    return false;
  }
}
