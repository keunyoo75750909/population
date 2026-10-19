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

# 따뜻한 톤을 위한 Custom CSS 스타일 적용
st.markdown("""
    <style>
    /* 전체 배경색을 따뜻한 아이보리 톤으로 설정 */
    .main {
        background-color: #FDFBF7;
    }
    /* 지표 카드 박스 스타일링 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border: 1px solid #F0EAE1;
    }
    /* 피라미드 아래 특징 요약 박스 스타일링 */
    .summary-box {
        background-color: #FFFDF9;
        border-left: 5px solid #E07A5F;
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        font-size: 1.05rem;
        line-height: 1.6;
        color: #2B2D42;
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
# 5. 선택한 동네의 데이터 추출 및 주요 지표 계산
# ------------------------------------------------------------------------------
selected_data = df_sigungu[df_sigungu['동'] == selected_dong]

if not selected_data.empty:
    row = selected_data.iloc[0]
    
    # 나이 라벨 생성: '0세', '1세', ..., '99세', '100세 이상'
    age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]
    
    # 남/여 나이별 인구수 추출
    male_counts = [row[f"남_{age}"] if f"남_{age}" in row else 0 for age in age_labels]
    female_counts = [row[f"여_{age}"] if f"여_{age}" in row else 0 for age in age_labels]
    
    # 연령별 전체 인구수 (남 + 여)
    age_totals = [m + f for m, f in zip(male_counts, female_counts)]
    
    # [지표 1] 총인구수
    total_pop = sum(age_totals)
    
    # [지표 2] 평균연령 (0~99세는 해당 나이, 100세 이상은 100세로 계산)
    if total_pop > 0:
        weighted_age_sum = sum(i * count for i, count in enumerate(age_totals[:100]))
        weighted_age_sum += 100 * age_totals[100]
        avg_age = weighted_age_sum / total_pop
    else:
        avg_age = 0.0
        
    # [지표 3] 유소년 인구(0~14세) 및 고령 인구(65세 이상) 비율
    child_pop = sum(age_totals[0:15])          # 유소년(0~14세)
    elderly_pop = sum(age_totals[65:])         # 고령(65세 이상)
    
    child_ratio = (child_pop / total_pop * 100) if total_pop > 0 else 0.0
    elderly_ratio = (elderly_pop / total_pop * 100) if total_pop > 0 else 0.0

    st.write("")

    # --------------------------------------------------------------------------
    # 6. 상단 지표 카드 3개 나란히 배치 (총인구, 평균연령, 고령화율)
    # --------------------------------------------------------------------------
    card1, card2, card3 = st.columns(3)
    
    # 1) 총인구 카드
    card1.metric(
        label="👥 총인구",
        value=f"{total_pop:,} 명"
    )
    
    # 2) 평균연령 카드
    card2.metric(
        label="🎂 평균연령",
        value=f"{avg_age:.1f} 세"
    )
    
    # 3) 고령화율 카드 (20% 초과 시 ⚠️ 주의 표시)
    if elderly_ratio >= 20.0:
        card3.metric(
            label="👵 고령화율 (65세 이상) ⚠️ 주의",
            value=f"{elderly_ratio:.1f} %",
            delta="초고령사회 (20% 이상)",
            delta_color="inverse"
        )
    else:
        card3.metric(
            label="👵 고령화율 (65세 이상)",
            value=f"{elderly_ratio:.1f} %",
            delta="일반" if elderly_ratio < 14.0 else "고령사회 (14% 이상)",
            delta_color="normal"
        )

    st.write("")


    # --------------------------------------------------------------------------
    # 7. X축 눈금(Tick) 계산 함수
    # --------------------------------------------------------------------------
    def get_nice_ticks(max_val):
        if max_val == 0:
            return [-10, 0, 10], ["10", "0", "10"]
        
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

    male_x = [-x for x in male_counts] # 남자는 왼쪽(음수)
    female_x = female_counts          # 여자는 오른쪽(양수)
    max_population = max(max(male_counts), max(female_counts))
    x_vals, x_texts = get_nice_ticks(max_population)


    # --------------------------------------------------------------------------
    # 8. Plotly 인구 피라미드 그래프 작성
    # --------------------------------------------------------------------------
    fig = go.Figure()

    # 남자 막대 (슬레이트 블루 #4A6984)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=male_x,
        name='남자',
        orientation='h',
        marker_color='#4A6984',
        customdata=male_counts,
        hovertemplate='<b>%{y}</b><br>남자 인구: %{customdata:,}명<extra></extra>'
    ))

    # 여자 막대 (코랄 오렌지 #E07A5F)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_x,
        name='여자',
        orientation='h',
        marker_color='#E07A5F',
        customdata=female_counts,
        hovertemplate='<b>%{y}</b><br>여자 인구: %{customdata:,}명<extra></extra>'
    ))

    # 레이아웃 세부 설정
    fig.update_layout(
        title=dict(
            text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 인구 피라미드 ({latest_year}년)",
            font=dict(size=22, color="#2B2D42")
        ),
        barmode='overlay',
        bargap=0.05,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#FDFBF7',
        
        # X축 설정
        xaxis=dict(
            title="<b>인구수 (명)</b>",
            tickvals=x_vals,
            ticktext=x_texts,
            gridcolor='#EAE0D5',
            zerolinecolor='#8D99AE',
            zerolinewidth=1.5
        ),
        
        # Y축 설정: 0세가 맨 아래, 100세 이상이 맨 위로 고정
        yaxis=dict(
            title="<b>나이</b>",
            type='category',
            categoryorder='array',
            categoryarray=age_labels,
            gridcolor='#EAE0D5'
        ),
        
        # 범례 설정
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=14)
        ),
        
        height=1000,
        margin=dict(l=60, r=60, t=100, b=60)
    )

    # 그래프 출력
    st.plotly_chart(fig, use_container_width=True)


    # --------------------------------------------------------------------------
    # 9. 피라미드 하단: '이 동네는 아이가 많은가요, 어르신이 많은가요?' 자동 한 줄 진단
    # --------------------------------------------------------------------------
    if child_ratio > elderly_ratio:
        summary_text = (
            f"👧👶 **이 동네는 아이들이 상대적으로 많은 편입니다!**<br>"
            f"유소년(0~14세) 비율이 **{child_ratio:.1f}%**로, 고령 인구(65세 이상) 비율(**{elderly_ratio:.1f}%**)보다 더 높아서 "
            f"어린이와 가족 단위 인구가 비교적 많이 거주하는 활기찬 동네입니다."
        )
    elif elderly_ratio >= 20.0:
        summary_text = (
            f"👵👴 **이 동네는 어르신들이 상대적으로 많이 거주하는 초고령화 지역입니다.**<br>"
            f"65세 이상 어르신 비율이 **{elderly_ratio:.1f}%**(20% 이상)로, 아이들(0~14세, **{child_ratio:.1f}%**)에 비해 "
            f"어르신 인구 비중이 확연히 높은 편입니다."
        )
    elif elderly_ratio > child_ratio:
        summary_text = (
            f"🏡👵 **이 동네는 아이들보다 어르신 비율이 조금 더 높은 편입니다.**<br>"
            f"65세 이상 어르신 비율(**{elderly_ratio:.1f}%**)이 유소년 비율(**{child_ratio:.1f}%**)보다 높아 "
            f"차분하고 조용한 주거 지역의 특성을 보입니다."
        )
    else:
        summary_text = (
            f"⚖️ **이 동네는 아이들과 어르신의 비율이 비슷하게 균형을 이루고 있습니다.**<br>"
            f"유소년 비율(**{child_ratio:.1f}%**)과 고령 인구 비율(**{elderly_ratio:.1f}%**)이 균형을 이루고 있습니다."
        )

    # 커스텀 스타일 박스로 표시
    st.markdown(f'<div class="summary-box">{summary_text}</div>', unsafe_allow_html=True)

else:
    st.warning("선택하신 지역의 인구 데이터가 존재하지 않습니다.")
