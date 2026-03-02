"use client";

import { useState } from "react";
import { X } from "lucide-react";
import {
  auth,
  googleProvider,
  signInWithPopup,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
} from "@/lib/firebase";

interface AuthModalProps {
  onClose: () => void;
}

type Tab = "login" | "signup";

function getKoreanError(code: string | undefined, message: string): string {
  switch (code) {
    case "auth/email-already-in-use":
      return "이미 사용 중인 이메일입니다.";
    case "auth/weak-password":
      return "비밀번호는 6자 이상이어야 합니다.";
    case "auth/user-not-found":
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "이메일 또는 비밀번호가 올바르지 않습니다.";
    case "auth/invalid-email":
      return "올바른 이메일 형식이 아닙니다.";
    case "auth/popup-blocked":
      return "팝업이 차단되었습니다. 팝업 허용 후 다시 시도하세요.";
    case "auth/popup-closed-by-user":
      return "";
    case "auth/unauthorized-domain":
      return "승인되지 않은 도메인입니다. Firebase Console에서 도메인을 추가해주세요.";
    default:
      return message || "오류가 발생했습니다. 다시 시도해주세요.";
  }
}

export default function AuthModal({ onClose }: AuthModalProps) {
  const [tab, setTab] = useState<Tab>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "signup") {
        await createUserWithEmailAndPassword(auth, email, password);
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
      onClose();
    } catch (err: unknown) {
      const code = (err as { code?: string }).code;
      const message = (err as { message?: string }).message ?? "";
      const korean = getKoreanError(code, message);
      if (korean) setError(korean);
      console.error("인증 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      await signInWithPopup(auth, googleProvider);
      onClose();
    } catch (err: unknown) {
      const code = (err as { code?: string }).code;
      const message = (err as { message?: string }).message ?? "";
      const korean = getKoreanError(code, message);
      if (korean) setError(korean);
      console.error("Google 로그인 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-sm mx-4 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-white font-bold text-lg">
            {tab === "login" ? "로그인" : "회원가입"}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-white transition-colors"
            aria-label="닫기"
          >
            <X size={18} />
          </button>
        </div>

        {/* 탭 */}
        <div className="flex gap-1 mb-6 bg-slate-800 rounded-lg p-1">
          <button
            onClick={() => { setTab("login"); setError(""); }}
            className={`flex-1 text-[13px] font-semibold py-1.5 rounded-md transition-colors ${
              tab === "login"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            로그인
          </button>
          <button
            onClick={() => { setTab("signup"); setError(""); }}
            className={`flex-1 text-[13px] font-semibold py-1.5 rounded-md transition-colors ${
              tab === "signup"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            회원가입
          </button>
        </div>

        {/* 이메일/비밀번호 폼 */}
        <form onSubmit={handleEmailAuth} className="space-y-3">
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-[13px] text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
          <input
            type="password"
            placeholder="비밀번호 (6자 이상)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-[13px] text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />

          {error && (
            <p className="text-red-400 text-[12px] text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-[13px] py-2.5 rounded-lg transition-colors"
          >
            {loading ? "처리 중..." : tab === "login" ? "로그인" : "회원가입"}
          </button>
        </form>

        {/* 구분선 */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px bg-slate-700" />
          <span className="text-slate-500 text-[11px]">또는</span>
          <div className="flex-1 h-px bg-slate-700" />
        </div>

        {/* Google 로그인 */}
        <button
          onClick={handleGoogle}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 border border-slate-700 text-white text-[13px] font-semibold py-2.5 rounded-lg transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Google로 계속하기
        </button>
      </div>
    </div>
  );
}
