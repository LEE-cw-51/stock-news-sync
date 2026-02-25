"use client";

import { Globe, Activity } from "lucide-react";
import { auth, googleProvider, signInWithPopup, signOut } from "@/lib/firebase";
import type { User } from "firebase/auth";
import MarketIndexCard from "@/components/dashboard/MarketIndexCard";
import type { MarketValue } from "@/lib/types";

interface HeaderProps {
  macroList: [string, MarketValue][];
  indexList: [string, MarketValue][];
  user: User | null;
}

export default function Header({ macroList, indexList, user }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-md border-b border-slate-800 shadow-xl">
      {/* 1층: MACRO 지표 */}
      <div className="border-b border-slate-800/50">
        <div className="max-w-7xl mx-auto px-4 h-12 flex items-center gap-6 overflow-x-auto no-scrollbar">
          <div className="flex-shrink-0 flex items-center gap-2 text-indigo-400 font-black text-[11px] border-r border-slate-800 pr-4 uppercase tracking-widest">
            <Globe size={14} /> Macro
          </div>
          <div className="flex items-center gap-8">
            {macroList.map(([name, val]) => (
              <MarketIndexCard key={name} name={name} value={val} variant="macro" />
            ))}
          </div>
        </div>
      </div>

      {/* 2층: MARKET 지수 + 로그인 버튼 */}
      <div>
        <div className="max-w-7xl mx-auto px-4 h-10 flex items-center gap-6 overflow-x-auto no-scrollbar">
          <div className="flex-shrink-0 flex items-center gap-2 text-slate-500 font-black text-[11px] border-r border-slate-800 pr-4 uppercase tracking-widest">
            <Activity size={14} /> Market
          </div>
          <div className="flex items-center gap-6">
            {indexList.map(([name, val]) => (
              <MarketIndexCard key={name} name={name} value={val} variant="index" />
            ))}
          </div>

          {/* 로그인/로그아웃 버튼 */}
          <div className="ml-auto flex-shrink-0 pl-4">
            {user ? (
              <button
                onClick={() => signOut(auth)}
                className="flex items-center gap-2 text-[11px] text-slate-400 hover:text-white transition-colors"
                aria-label="로그아웃"
              >
                {user.photoURL && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={user.photoURL} className="w-6 h-6 rounded-full" alt="프로필 사진" />
                )}
                <span className="hidden sm:inline">{user.displayName}</span>
                <span className="text-slate-700">|</span>
                <span>로그아웃</span>
              </button>
            ) : (
              <button
                onClick={() => signInWithPopup(auth, googleProvider)}
                className="flex items-center gap-2 px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold rounded-full transition-colors"
                aria-label="Google 계정으로 로그인"
              >
                Google 로그인
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
