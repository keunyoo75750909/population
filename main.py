import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정 (페이지 제목, 레이아웃 등)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 따뜻한 톤을 위한 간단한 Custom CSS 스타일 적용
st.markdown("""
    <style>
    /* 전체 배경색을 따뜻한 아이보리 톤으로 설정 */
    .main {
        background-color: #FDFBF7;
    }
    /* 카드 및 메트릭 박스 스타일링 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border: 1px solid #F0EAE1;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 2. 데이터 로드 및 캐싱 (속도 최적화)
# ------------------------------------------------------------------------------
@st.cache_data
def load_population_data():
    """
    GitHub에 업로드된 압축 CSV 파일을 판다스로 직접 읽어옵니다.
    GitHub의 'blob' URL 대신 직접 파일 데이터를 가져올 수 있는 'raw' URL을 사용합니다.
    """
    # GitHub Raw 링크 주소 (zip 파일도 pandas가 자동으로 압축을 해제하고 읽습니다)
    raw_url = "https://raw.githubusercontent.com/keunyoo75750909/population/main/population_ts_yearly_gender.zip"
    
    # CSV 데이터 읽기
    df = pd.read_csv(raw_url)
    
    # 가장 최신 연도만 추출 (예: 2026년)
    latest_year = int(df['연도'].max())
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 진행 상태 표시
with st.spinner("인구 데이터를 불러오는 중입니다..."):
    df, latest_year = load_population_data()


# ------------------------------------------------------------------------------
# 3. 앱 타이틀 및 안내 문구
# ------------------------------------------------------------------------------
st.title("🏡 우리 동네 인구 피라미드")
st.markdown(f"**{latest_year}년 최신 데이터** 기준 전국 읍·면·동별 연령 및 성별 인구 구조를 확인해 보세요.")
st.divider()


# ------------------------------------------------------------------------------
# 4. 상단 드롭다운 메뉴 (시도 → 시군구 → 동 3단계 연동)
# ------------------------------------------------------------------------------
st.subheader("📍 지역 선택")

col_sido, col_sigungu, col_dong = st.columns(3)

# 1) 시도 선택
with col_sido:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 2) 시군구 선택 (선택된 시도에 해당하는 데이터만 필터링)
df_sido = df[df['시도'] == selected_sido]
with col_sigungu:
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 3) 동 선택 (선택된 시도 및 시군구에 해당하는 데이터만 필터링)
df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]
with col_dong:
    dong_list = sorted(df_sigungu['동'].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)


# ------------------------------------------------------------------------------
# 5. 선택한 동네의 데이터 추출 및 가공
# ------------------------------------------------------------------------------
selected_data = df_sigungu[df_sigungu['동'] == selected_dong]

if not selected_data.empty:
    row = selected_data.iloc[0]
    
    # 나이 라벨 생성: '0세', '1세', ..., '99세', '100세 이상'
    # 세로축의 아래(0세)부터 위(100세 이상)로 쌓일 순서입니다.
    age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]
    
    # 남/여 나이별 인구수 컬럼 이름 생성 후 값 가져오기
    male_cols = [f"남_{age}" for age in age_labels]
    female_cols = [f"여_{age}" for age in age_labels]
    
    male_counts = [row[col] if col in row else 0 for col in male_cols]
    female_counts = [row[col] if col in row else 0 for col in female_cols]
    
    # 피라미드 그래프 작성을 위해 남자 인구수는 음수(-)로 변환
    male_x = [-x for x in male_counts]
    female_x = female_counts

    # 요약 정보 계산
    total_male = sum(male_counts)
    total_female = sum(female_counts)
    total_pop = total_male + total_female
    
    st.write("") # 간격 조정
    
    # 요약 메트릭 표시
    m1, m2, m3 = st.columns(3)
    m1.metric("총 인구수", f"{total_pop:,} 명")
    m2.metric("남성 인구수", f"{total_male:,} 명", f"{total_male/total_pop*100:.1f}%" if total_pop > 0 else "0%")
    m3.metric("여성 인구수", f"{total_female:,} 명", f"{total_female/total_pop*100:.1f}%" if total_pop > 0 else "0%")
    
    st.divider()

    # --------------------------------------------------------------------------
    # 6. X축 눈금(Tick) 깔끔하게 정렬하는 함수
    # --------------------------------------------------------------------------
    def get_nice_ticks(max_val):
        """
        음수/양수로 이루어진 X축 눈금을 양수 표기로 깔끔하게 보기 위해 계산하는 함수입니다.
        """
        if max_val == 0:
            return [-10, 0, 10], ["10", "0", "10"]
        
        # 눈금 간격 단위 계산
        raw_step = max_val / 4
        magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
        residual = raw_step / magnitude
        
        if residual > 5:
            step = 10 * magnitude
        elif residual > 2:
            step = 5 * magnitude
        elif residual > 1:
            step = 2 * magnitude
        else:
            step = magnitude
            
        step = int(max(1, step))
        num_steps = math.ceil(max_val / step)
        
        vals = [i * step for i in range(-num_steps, num_steps + 1)]
        texts = [f"{abs(v):,}" for v in vals]
        return vals, texts

    max_population = max(max(male_counts), max(female_counts))
    x_vals, x_texts = get_nice_ticks(max_population)

    # --------------------------------------------------------------------------
    # 7. Plotly 인구 피라미드 그래프 작성 (따뜻한 톤)
    # --------------------------------------------------------------------------
    fig = go.Figure()

    # 남자 막대 (왼쪽, 음수값) - 따뜻한 슬레이트 블루 톤 (#4A6984)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=male_x,
        name='남자',
        orientation='h',
        marker_color='#4A6984',
        customdata=male_counts,
        hovertemplate='<b>%{y}</b><br>남자 인구: %{customdata:,}명<extra></extra>'
    ))

    # 여자 막대 (오른쪽, 양수값) - 따뜻한 코랄 오렌지 톤 (#E07A5F)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_x,
        name='여자',
        orientation='h',
        marker_color='#E07A5F',
        customdata=female_counts,
        hovertemplate='<b>%{y}</b><br>여자 인구: %{customdata:,}명<extra></extra>'
    ))

    # 그래프 레이아웃 세부 설정
    fig.update_layout(
        title=dict(
            text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 인구 피라미드 ({latest_year}년)",
            font=dict(size=22, color="#2B2D42")
        ),
        barmode='overlay', # 두 막대를 좌우로 교차 배치
        bargap=0.05,       # 막대 간격 최소화
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#FDFBF7', # 차트 배경을 따뜻한 아이보리로 설정
        
        # X축 설정 (음수 값을 양수 명수로 표시)
        xaxis=dict(
            title="<b>인구수 (명)</b>",
            tickvals=x_vals,
            ticktext=x_texts,
            gridcolor='#EAE0D5',
            zerolinecolor='#8D99AE',
            zerolinewidth=1.5
        ),
        
        # [핵심] Y축 설정: 0세부터 100세 이상 순서 그대로 고정 (맨 아래 0세, 맨 위 100세 이상)
        yaxis=dict(
            title="<b>나이</b>",
            type='category',
            categoryorder='array',
            categoryarray=age_labels, # 배열의 첫번째 요소('0세')가 가장 아래에 배치됨
            gridcolor='#EAE0D5'
        ),
        
        # 범례(Legend) 설정
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=14)
        ),
        
        height=1000, # 100개 연령대가 시원하게 보이도록 높이 지정
        margin=dict(l=60, r=60, t=100, b=60)
    )

    # 스트림릿 화면에 그래프 출력
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("선택하신 지역의 인구 데이터가 존재하지 않습니다.")
