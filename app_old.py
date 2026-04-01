import streamlit as st
import pandas as pd
import webbrowser
from modules.data_manager import SheetManager
from modules.visualizer import Visualizer
from modules.chatbot import Chatbot   # 쳇봇



# @st.cache_resource
# def get_chatbot():
#     return Chatbot()


def main():
    st.set_page_config(page_title="해양수산 실시간 위판 데이터",
                        layout="wide",
                        page_icon="🐟"
                        )

    # 1. 데이터 로드 (구글 시트 연동)
    @st.cache_data(ttl=600, show_spinner="데이터를 동기화하는 중입니다...")  # 10분마다 캐시 갱신
    def load_gsheet_data():
        try:
            db = SheetManager()
            df = db.get_all_responses_df()
            # 수치형 데이터 변환 (구글 시트에서 가져올 때 문자열일 경우 대비)
            numeric_cols = ['평균가', '물량(킬로그램)', '총 판매액']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].replace('[,]', '', regex=True), errors='coerce')
            return df
        except Exception as e:
            st.error(f"구글 시트 연결 실패: {e}")
            return pd.DataFrame()

    df = load_gsheet_data()

    if df.empty:
        st.warning("구글 시트에 데이터가 없거나 연결 설정(.env)을 확인해주세요.")
        return

    st.title("🐟 실시간 위판장별 어종 데이터 분석")

    # 사이드바 메뉴
    menu = st.sidebar.selectbox("메뉴 선택", ["데이터 검색 및 시각화", "금액 비교 분석", "AI 분석"])

    viz = Visualizer(df)

    if menu == "데이터 검색 및 시각화":
        st.subheader("🔍 통합 검색 필터")
        
        col1, col2 = st.columns(2)
        with col1:
            # '위판장명' 컬럼 기준 검색
            markets = st.multiselect("위판장 선택", options=sorted(df['위판장명'].unique()))
        with col2:
            # '수산물표준코드명' 또는 '어종명' (시트 헤더에 맞게 조정)
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

    elif menu == "금액 비교 분석":
        st.subheader("💰 어종별 기준 금액 상위 판매처")
        
        fish_col = '수산물표준코드명' if '수산물표준코드명' in df.columns else '어종명'
        
        col_f, col_p = st.columns(2)
        with col_f:
            target_fish = st.selectbox("어종 선택", options=sorted(df[fish_col].unique()))
        with col_p:
            # 평균가 기준 비교
            threshold_price = st.number_input("기준 가격 입력 (평균가 이상)", min_value=0, value=10000)

        # 필터: 선택한 어종 중 기준 가격보다 높은 데이터
        high_price_df = df[(df[fish_col] == target_fish) & (df['평균가'] > threshold_price)]
        
        if not high_price_df.empty:
            st.success(f"'{target_fish}'을(를) {threshold_price:,}원보다 높게 판매한 위판장 목록입니다.")
            display_df = high_price_df[['위판장명', fish_col, '평균가', '물량(킬로그램)', '총 판매액']]
            st.table(display_df.sort_values(by='평균가', ascending=False))
            
            viz.plot_price_comparison(high_price_df, target_fish)
        else:
            st.info(f"해당 가격({threshold_price:,}원)을 초과하여 판매된 기록이 없습니다.")

    elif menu == "AI 분석":
        st.write("## 🤖 AI 분석 리포트")
    # 🔥 쳇봇 UI를 메인 루프 마지막에 한 번만 호출

if __name__ == "__main__":
    main()