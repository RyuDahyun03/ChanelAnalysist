import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 페이지 설정 및 커스텀 디자인 (이미지 반영)
# ==========================================
st.set_page_config(page_title="똑주부 채널 AI 분석", layout="wide", initial_sidebar_state="expanded")

# 다크 테마 및 카드 UI 스타일링 (CSS)
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    /* 상단 헤더 스타일 */
    h1, h2, h3 {
        color: #FFFFFF;
        font-weight: 700;
    }
    /* KPI 메트릭 카드 스타일 */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
        color: #A0A0A0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2D2D2D;
        color: #00E676 !important; /* 포인트 컬러 (네온 그린) */
        border-bottom: 2px solid #00E676;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 가공 함수 (Data Processing)
# ==========================================
def time_str_to_seconds(time_str):
    """ '0:00:26' 형태의 문자열을 초(seconds) 단위 정수로 변환 """
    if pd.isna(time_str): return 0
    parts = str(time_str).split(':')
    try:
        if len(parts) == 3:
            return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0])*60 + int(parts[1])
    except:
        return 0
    return 0

@st.cache_data
def process_content_data(df):
    """ 영상별 표 데이터 가공 (리텐션 계산) """
    if '콘텐츠' in df.columns and df.iloc[0]['콘텐츠'] == '합계':
        df = df.iloc[1:].copy() # 합계 행 제거
        
    # 필수 컬럼 정리 및 형변환
    cols_to_keep = ['동영상 제목', '조회수', '노출 클릭률 (%)', '평균 시청 지속 시간', '길이']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    df_clean = df[existing_cols].copy()
    
    if '평균 시청 지속 시간' in df_clean.columns:
        df_clean['평균시청초'] = df_clean['평균 시청 지속 시간'].apply(time_str_to_seconds)
    
    # 리텐션(%) 계산
    if '평균시청초' in df_clean.columns and '길이' in df_clean.columns:
        df_clean['리텐션 (%)'] = (df_clean['평균시청초'] / pd.to_numeric(df_clean['길이'], errors='coerce')) * 100
        df_clean['리텐션 (%)'] = df_clean['리텐션 (%)'].round(1)
        
    return df_clean.dropna(subset=['조회수'])

# ==========================================
# 3. 사이드바 및 파일 업로드 UI
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254068.png", width=50) # 임시 로고
    st.title("Data Upload")
    st.markdown("분석할 CSV 파일들을 업로드해주세요.")
    
    file_content = st.file_uploader("1. 영상별 표 데이터 (필수)", type=['csv'])
    file_traffic = st.file_uploader("2. 트래픽 소스 (선택)", type=['csv'])
    file_trend = st.file_uploader("3. 일자별 총계 (선택)", type=['csv'])

# ==========================================
# 4. 메인 대시보드 레이아웃
# ==========================================
st.title("📊 똑주부 채널 AI 분석 대시보드")

if file_content is not None:
    # 데이터 로드 및 가공
    df_raw = pd.read_csv(file_content)
    df_content = process_content_data(df_raw)
    
    # --- [KPI 메트릭 섹션] ---
    st.markdown("### 채널 핵심 지표 (Top 20 기준)")
    col1, col2, col3, col4 = st.columns(4)
    
    total_views = df_content['조회수'].sum()
    avg_ctr = df_content['노출 클릭률 (%)'].mean()
    avg_retention = df_content['리텐션 (%)'].mean() if '리텐션 (%)' in df_content.columns else 0
    
    col1.metric("총 조회수", f"{int(total_views):,} 회")
    col2.metric("평균 노출 클릭률 (CTR)", f"{avg_ctr:.1f} %")
    col3.metric("평균 숏폼 리텐션", f"{avg_retention:.1f} %")
    col4.metric("분석 영상 수", f"{len(df_content)} 개")
    
    st.markdown("---")
    
    # --- [상세 분석 탭 섹션] ---
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 콘텐츠 및 훅(Hook) 진단", "🚦 트래픽 체질 분석", "👥 타겟 & 수익", "🤖 AI 기획안 제안"])
    
    with tab1:
        st.markdown("#### 노출 클릭률 vs 리텐션 매트릭스")
        if '리텐션 (%)' in df_content.columns:
            # 버블 차트 (조회수 크기 반영)
            fig = px.scatter(df_content, x='노출 클릭률 (%)', y='리텐션 (%)', size='조회수', 
                             hover_name='동영상 제목', color='조회수',
                             color_continuous_scale='Viridis', template='plotly_dark')
            fig.add_hline(y=avg_retention, line_dash="dash", line_color="gray", annotation_text="평균 리텐션")
            fig.add_vline(x=avg_ctr, line_dash="dash", line_color="gray", annotation_text="평균 CTR")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 가공된 영상 데이터")
            st.dataframe(df_content.sort_values(by='조회수', ascending=False).head(10), use_container_width=True)
            
    with tab2:
        st.markdown("#### 트래픽 소스 분포")
        if file_traffic is not None:
            df_traffic = pd.read_csv(file_traffic)
            if '트래픽 소스' in df_traffic.columns and df_traffic.iloc[0]['트래픽 소스'] == '합계':
                df_traffic = df_traffic.iloc[1:]
            
            fig_pie = px.pie(df_traffic, values='조회수', names='트래픽 소스', hole=0.4, template='plotly_dark')
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("사이드바에 '트래픽 소스' 데이터를 업로드해주세요.")
            
    with tab3:
        st.markdown("#### 일자별 트렌드 추이")
        if file_trend is not None:
            df_trend = pd.read_csv(file_trend)
            # '유효 조회수' 혹은 '순 시청자수' 컬럼을 찾아 그래프화
            target_col = '유효 조회수' if '유효 조회수' in df_trend.columns else '순 시청자수'
            fig_line = px.line(df_trend, x='날짜', y=target_col, markers=True, template='plotly_dark')
            fig_line.update_traces(line_color='#00E676')
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("사이드바에 '일자별 총계' 데이터를 업로드해주세요.")

    with tab4:
        st.markdown("#### 🧠 AI 보조 연출자 (기획안 생성)")
        st.markdown("위에서 가공된 정량적 데이터를 바탕으로 Gemini AI가 다음 주 기획안을 작성합니다.")
        
        if st.button("🚀 AI 분석 리포트 생성하기", use_container_width=True):
            st.warning("여기에 Gemini API 연동 로직이 들어갈 예정입니다.")
            # TODO: df_content, df_traffic의 텍스트 요약을 Gemini API로 전송하는 로직 추가

else:
    st.info("👈 왼쪽 사이드바에서 '표 데이터.csv' 파일을 먼저 업로드해주세요.")
