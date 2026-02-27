"""
Lambda 환경변수 JSON 파일 생성 스크립트
Firebase JSON 등 특수문자가 포함된 값을 안전하게 전달하기 위해
--cli-input-json 방식으로 파일을 생성합니다.
"""
import json
import os

config = {
    "FunctionName": "stock-news-sync",
    "Environment": {
        "Variables": {
            "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", "").strip(),
            "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "").strip(),
            "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", "").strip(),
            "FIREBASE_SERVICE_ACCOUNT": os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip(),
            "FIREBASE_DATABASE_URL": os.environ.get("FIREBASE_DATABASE_URL", "").strip(),
            "SUPABASE_URL": os.environ.get("SUPABASE_URL", "").strip(),
            "SUPABASE_SERVICE_ROLE_KEY": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        }
    }
}

with open("lambda_env.json", "w") as f:
    json.dump(config, f)

print("lambda_env.json generated successfully")
