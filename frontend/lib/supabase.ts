import { createClient } from "@supabase/supabase-js";
import type { User, AuthChangeEvent, Session, AuthError } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseAnonKey || "placeholder"
);

/** Google OAuth 로그인 (리디렉션 방식) */
export async function signInWithGoogle(): Promise<void> {
  await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.origin },
  });
}

/** 이메일/비밀번호 로그인 */
export async function signInWithEmail(
  email: string,
  password: string
): Promise<void> {
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

/** 이메일/비밀번호 회원가입 */
export async function signUpWithEmail(
  email: string,
  password: string
): Promise<void> {
  const { error } = await supabase.auth.signUp({ email, password });
  if (error) throw error;
}

/** 로그아웃 */
export async function signOut(): Promise<void> {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

/** 인증 상태 구독 — cleanup 함수를 반환 */
export function onAuthStateChange(
  callback: (user: User | null) => void
): () => void {
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(
    (_event: AuthChangeEvent, session: Session | null) => {
      callback(session?.user ?? null);
    }
  );
  return () => subscription.unsubscribe();
}

export type { User, AuthError };
