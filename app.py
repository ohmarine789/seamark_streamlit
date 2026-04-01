import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import Visualizer
from modules.chatbot import Chatbot


# 1. 데이터 로드 로직 분리
@st.cache_data(ttl=600, show_spinner="데이터를 동기화하는 중입니다...")
def load_gsheet_data():
    try:
        db = SheetManager()
        df = db.get_all_responses_df()
        # 수치형 데이터 변환
        numeric_cols = ['평균가', '물량(킬로그램)', '총 판매액']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].replace('[,]', '', regex=True), errors='coerce')
        return df
    except Exception as e:
        st.error(f"구글 시트 연결 실패: {e}")
        return pd.DataFrame()

# 2. 메뉴별 렌더링 함수 정의
def render_dashboard(df, viz):
    """데이터 검색 및 시각화 화면"""
    st.subheader("🔍 통합 검색 필터")
    
    col1, col2 = st.columns(2)
    with col1:
        markets = st.multiselect("위판장 선택", options=sorted(df['위판장명'].unique()))
    with col2:
        fish_col = '수산물표준코드명' if '수산물표준코드명' in df.columns else '어종명'
        fishes = st.multiselect("어종 선택", options=sorted(df[fish_col].unique()))

    # 필터링
    filtered_df = df.copy()
    if markets:
        filtered_df = filtered_df[filtered_df['위판장명'].isin(markets)]
    if fishes:
        filtered_df = filtered_df[filtered_df[fish_col].isin(fishes)]

    st.dataframe(filtered_df, use_container_width=True)
    st.divider()
    viz.render_charts(filtered_df)

def render_price_analysis(df, viz):
    """금액 비교 분석 화면"""
    st.subheader("💰 어종별 기준 금액 상위 판매처")
    
    fish_col = '수산물표준코드명' if '수산물표준코드명' in df.columns else '어종명'
    
    col_f, col_p = st.columns(2)
    with col_f:
        target_fish = st.selectbox("어종 선택", options=sorted(df[fish_col].unique()))
    with col_p:
        threshold_price = st.number_input("기준 가격 입력 (평균가 이상)", min_value=0, value=10000)

    high_price_df = df[(df[fish_col] == target_fish) & (df['평균가'] > threshold_price)]
    
    if not high_price_df.empty:
        st.success(f"'{target_fish}'을(를) {threshold_price:,}원보다 높게 판매한 위판장 목록입니다.")
        display_df = high_price_df[['위판장명', fish_col, '평균가', '물량(킬로그램)', '총 판매액']]
        st.table(display_df.sort_values(by='평균가', ascending=False))
        viz.plot_price_comparison(high_price_df, target_fish)
    else:
        st.info(f"해당 가격({threshold_price:,}원)을 초과하여 판매된 기록이 없습니다.")

# def render_ai_report():
#     """AI 분석 리포트 화면"""
#     st.write("## 🤖 AI 분석 리포트")
#     # 여기에 AI 분석 관련 로직 추가 가능

def render_chatbot_ui(show_ai_ui):
    # 1. CSS Injection: 오른쪽 하단 플로팅 버튼 및 채팅창 스타일
    st.markdown("""
        <style>
        .floating-chat {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background-color: #FF4B4B;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 60px;
            font-size: 30px;
            cursor: pointer;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
            z-index: 9999;
        }
        .st-emotion-cache-hqmjvr{
          max-height:200px;
        
        }
        </style>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # # 플로팅 버튼
    # if st.button("💬", key="chat_button"):
    #     st.session_state.chat_open = not st.session_state.chat_open

    # 3. 채팅창 사이드바
    # if st.session_state.chat_open:
    if show_ai_ui:
        with st.sidebar:
            st.title("🤖 AI 마케팅 어드바이저")
            
            # --- [FAQ 섹션] 벡터 DB 관련 정보 제공 ---
            with st.expander("📌 벡터 DB & 데이터 동기화 FAQ", expanded=True):
                st.markdown("""
                * **Q. 데이터가 실시간인가요?** 자동 동기화 시점에 `vector_db`에 정제되어 저장됩니다.
                * **Q. 특수문자 처리는요?** 내부 `clean_text` 로직이 불필요한 기호를 자동 제거합니다.
                * **Q. 답변의 기준은?** 구글 시트의 실시간 데이터를 임베딩하여 분석합니다.
                """)
            
            st.info("데이터를 기반으로 궁금한 점을 물어보세요!")
            st.divider()

            # 채팅 히스토리 및 인터페이스
            chat_container = st.container(height=400)

            # 첫 방문 시 웰컴 메시지
            if not st.session_state.messages:
                welcome = "분석 준비가 완료되었습니다. **다른 질문이 있으신가요?**"
                st.session_state.messages.append({"role": "assistant", "content": welcome})

            for message in st.session_state.messages:
                with chat_container.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 채팅 입력 및 처리
            if prompt := st.chat_input("메시지를 입력하세요...", key="chat_input_widget"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container.chat_message("user"):
                    st.markdown(prompt)

                with chat_container.chat_message("assistant"):
                    with st.spinner("데이터 분석 중..."):
                        # bot = get_chatbot() #
                        bot = Chatbot()
                        response = bot.get_response(prompt, st.session_state.messages[:-1]) #
                        st.markdown(response)
                        st.caption("💡 다른 질문이 있으신가요? 언제든 말씀해 주세요.")
                
                st.session_state.messages.append({"role": "assistant", "content": response})    


# 3. 메인 실행 함수
def main():
    st.set_page_config(
        page_title="해양수산 실시간 위판 데이터",
        layout="wide",
        page_icon="🐟"
    )

    # 데이터 로드
    df = load_gsheet_data()

    if df.empty:
        st.warning("구글 시트에 데이터가 없거나 연결 설정(.env)을 확인해주세요.")
        return

    st.title("🐟 실시간 위판장별 어종 데이터 분석")

    # 사이드바 메뉴
    menu = st.sidebar.selectbox("메뉴 선택", ["데이터 검색 및 시각화", "금액 비교 분석"])
    
    # AI 체크 버튼 메뉴
    show_ai_ui = st.sidebar.checkbox("AI 분석", False)
  
   
    # 시각화 객체 생성
    viz = Visualizer(df)

    # 메뉴별 분기 (함수 호출로 간결화)
    if menu == "데이터 검색 및 시각화":
        render_dashboard(df, viz)
    elif menu == "금액 비교 분석":
        render_price_analysis(df, viz)

    if show_ai_ui:
        render_chatbot_ui(show_ai_ui)


if __name__ == "__main__":
    main()