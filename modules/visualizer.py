import streamlit as st
import plotly.express as px

class Visualizer:
    def __init__(self, df):
        self.df = df

    def render_charts(self, df):
        if df.empty:
            return

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 위판장별 평균 단가 현황")
            # 데이터가 많을 수 있으므로 상위 15개만 표시
            plot_df = df.nlargest(15, '평균가')
            fig1 = px.bar(plot_df, x='위판장명', y='평균가', color='수산물표준코드명' if '수산물표준코드명' in df.columns else None,
                          text_auto='.2s', title="상위 단가 위판장")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("### ⚖️ 어종별 물량(kg) 비중")
            fish_col = '수산물표준코드명' if '수산물표준코드명' in df.columns else '어종명'
            fig2 = px.pie(df, values='물량(킬로그램)', names=fish_col, hole=0.3)
            st.plotly_chart(fig2, use_container_width=True)

    def plot_price_comparison(self, df, fish_name):
        st.markdown(f"### 📊 {fish_name} 단가 및 물량 상관관계")
        fig = px.scatter(df, x='위판장명', y='평균가', size='물량(킬로그램)', 
                         color='평균가', hover_data=['총 판매액'],
                         labels={'평균가':'단가(원)', '물량(킬로그램)':'중량(kg)'})
        st.plotly_chart(fig, use_container_width=True)