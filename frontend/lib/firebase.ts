// lib/firebase.ts
import { initializeApp, getApps } from "firebase/app";
import { getDatabase } from "firebase/database";

const firebaseConfig = {
  apiKey: "AIzaSyCI7b_yhFYjeVucGefA96rmoh_IM_fH3XM",
  authDomain: "stock-news-sync.firebaseapp.com",
  databaseURL: "https://stock-news-sync-default-rtdb.firebaseio.com",
  projectId: "stock-news-sync",
  storageBucket: "stock-news-sync.firebasestorage.app",
  messagingSenderId: "618499401683",
  appId: "1:618499401683:web:59cb2e07b43234717f7126",
  measurementId: "G-8XKL7JZW8N"
};

// 앱이 중복 초기화되지 않도록 방지하는 코드
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const db = getDatabase(app);

export { db };