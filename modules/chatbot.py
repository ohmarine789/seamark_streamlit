# pip uninstall -y langchain-google-genai google-generativeai
# 2. 최신 버전(4.0.0 이상)으로 재설치
# pip install -U langchain-google-genai
# 429 RESOURCE_EXHAUSTED → 요청은 갔고, 쿼터만 없음 
import os
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from modules.vector_db import VectorDB
from dotenv import load_dotenv

load_dotenv()

class Chatbot:
    def __init__(self):
       
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",   # 무료버전 종료 현제 유료 버전
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=1.0,  # 문서에서 Gemini 3.0+ (1.5 포함) 권장값인 1.0으로 설정
            max_retries=2
        )
       
        self.vdb = VectorDB()
        self.system_prompt = """
            당신은 전문 마케팅 컨설턴트입니다. 
            제공된 [실제 데이터]를 바탕으로 비즈니스 전략을 제안하세요.
            데이터에 없는 내용은 지어내지 마세요.
        """

    def get_response(self, user_query, chat_history):
        # 벡터 DB 검색 (기존 로직 유지)
        try:
            related_docs = self.vdb.query_similar_data(user_query, k=5)
            context = "\n".join([doc.page_content for doc in related_docs])
        except:
            context = "데이터를 찾을 수 없습니다."

        # [최신 문서 반영] Invocation 구조 최적화
        messages = [
            SystemMessage(content=f"{self.system_prompt}\n\n[데이터 맥락]\n{context}"),
        ]
        
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_query))
        
        # 호출 및 응답 반환
        response = self.llm.invoke(messages)
        
        # [주의] Gemini 1.5/2.5는 .content가 직접 문자열을 반환합니다.
        return response.content