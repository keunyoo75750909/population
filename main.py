import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. 페이지 기본 설정 및 제목 표시
# ==========================================
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 앱 제목 및 설명 문구
st.title("👨‍👩‍👧‍👦 동네별 인구 피라미드")
st.caption("전국 읍·면·동의 최신 연도 인구 구조를 피라미드 그래프로 확인해보세요.")


# ==========================================
# 2. 데이터 불러오기 (캐싱 처리로 로딩 속도 최적화)
# ==========================================
@st.cache_data
def load_data():
    # GitHub 웹페이지 주소를 pandas가 읽을 수 있는 Raw 링크로 변환합니다.
    url = "https://github.com/keunyoo75750909/population/blob/main/population_ts_yearly_gender.zip"
    raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    
    # 압축된 CSV 파일 읽기
    df = pd.read_csv(raw_url)
    
    # 데이터셋 내 가장 최신 연도만 선택
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 실행
with st.spinner("최신 인구 데이터를 불러오는 중입니다..."):
    df, latest_year = load_data()

st.sidebar.info(f"📅 기준 연도: **{latest_year}년**")


# ==========================================
# 3. 나이 라벨 및 성별 열(Column) 이름 추출
# ==========================================
# '남_'으로 시작하는 열을 찾아 0세부터 100세 이상까지의 나이 순서를 파악합니다.
male_cols = [c for c in df.columns if c.startswith("남_")]

# '남_' 접두사를 제거하여 나이 라벨 리스트 생성 ('0세', '1세', ..., '100세 이상')
age_labels = [c.replace("남_", "") for c in male_cols]

# 나이 라벨에 대응하는 여성 데이터 열 이름 생성 ('여_0세', '여_1세', ...)
female_cols = [f"여_{age}" for age in age_labels]


# ==========================================
# 4. 지역 선택 드롭다운 (시도 -> 시군구 -> 동)
# ==========================================
st.subheader("📍 지역 선택")

# 화면 상단에 드롭다운 3개를 가로 1줄로 배치
col1, col2, col3 = st.columns(3)

# 1) 시·도 선택
with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("시·도 선택", sido_list)

# 선택된 시·도 데이터 필터링
df_sido = df[df["시도"] == selected_sido]

# 2) 시·군·구 선택
with col2:
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

# 선택된 시·군·구 데이터 필터링 (오류가 난 부분을 df_sido 참조로 수정)
df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]

# 3) 읍·면·동 선택
with col3:
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("읍·면·동 선택", dong_list)

# 최종 선택된 동네 데이터 필터링
selected_data = df_sigungu[df_sigungu["동"] == selected_dong]


# ==========================================
# 5. 인구 피라미드 그래프 그리기
# ==========================================
if not selected_data.empty:
    # 선택한 지역의 1행 데이터에서 남성/여성 나이별 인구수 추출
    row = selected_data.iloc[0]
    male_pop = [int(row[col]) for col in male_cols]
    female_pop = [int(row[col]) for col in female_cols]

    # 총 인구수 계산
    total_male = sum(male_pop)
    total_female = sum(female_pop)
    total_pop = total_male + total_female

    # 동네 인구 현황 요약 카드 출력
    st.markdown("---")
    st.subheader(f"📊 {selected_sido} {selected_sigungu} {selected_dong} 인구 현황")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("총 인구수", f"{total_pop:,} 명")
    m_col2.metric("남성 인구수", f"{total_male:,} 명")
    m_col3.metric("여성 인구수", f"{total_female:,} 명")

    # 남성 인구수는 왼쪽 배치를 위해 음수(-) 값으로 변환
    male_pop_neg = [-val for val in male_pop]

    # Plotly 시각화 객체 생성
    fig = go.Figure()

    # 남성 막대 그래프 (왼쪽 배치, 따뜻한 슬레이트 블루)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#4A6FA5"),
        hovertemplate="<b>%{y}</b><br>남성 인구: %{customdata:,}명<extra></extra>",
        customdata=male_pop  # 마우스 호버(툴팁) 시에는 양수 값으로 표시
    ))

    # 여성 막대 그래프 (오른쪽 배치, 따뜻한 로즈 테라코타)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#E07A5F"),
        hovertemplate="<b>%{y}</b><br>여성 인구: %{x:,}명<extra></extra>"
    ))

    # X축(인구수) 눈금을 양수로 대칭 표기하기 위한 설정
    max_val = max(max(male_pop, default=1), max(female_pop, default=1))
    step = max(1, int(max_val /
