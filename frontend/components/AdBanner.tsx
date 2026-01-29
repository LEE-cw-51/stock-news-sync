type AdType = 'top-banner' | 'mobile-sticky' | 'in-feed' | 'side-banner'; // side-banner 추가

export default function AdBanner({ type }: { type: AdType }) {
  // 1. 상단 메인 배너
  if (type === 'top-banner') {
    return (
      <div className="w-full max-w-7xl mx-auto h-[90px] bg-slate-900/50 border border-slate-800 border-dashed flex items-center justify-center text-slate-500 text-xs my-4 rounded-lg">
        📢 AD AREA: Top Billboard (728x90)
      </div>
    );
  }

  // 2. 사이드바 세로 배너 (신규 추가)
  if (type === 'side-banner') {
    return (
      <div className="w-[160px] h-[600px] bg-slate-900/30 border border-slate-800 border-dashed flex flex-col items-center justify-center text-slate-600 text-[10px] rounded-lg sticky top-36">
        <span className="rotate-90 whitespace-nowrap">📢 AD: Skyscraper (160x600)</span>
      </div>
    );
  }

  // 3. 인피드 배너
  if (type === 'in-feed') {
    return (
      <div className="w-full h-[100px] bg-slate-900 border border-slate-800 my-6 flex items-center justify-center text-slate-600 text-[10px] rounded-xl">
        📢 AD AREA: Native In-Feed
      </div>
    );
  }

  // 모바일 스티키는 사용 안 함 (코드만 남겨둠)
  return null; 
}