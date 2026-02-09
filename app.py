import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="엘리트 씨수말 랭킹 시스템", layout="wide")

# 2. 데이터 분석 함수 (가장 안정적인 구조로 재설계)
@st.cache_data
def load_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, f"파일을 찾을 수 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, None, f"데이터 분석 중 오류 발생: {e}"

    year_pattern = re.compile(r'(\d{4})')
    
    # elite_map: 씨수말 -> 그 아래 @가 붙은 엘리트 딸들의 정보
    # line_map: 어떤 말 -> 그 아래 '선(가지)'으로 직접 연결된 자식들의 이름
    elite_map = defaultdict(list)
    line_map = {}

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        # [가지연결 데이터 추출] 현재 노드 바로 아래의 자식 노드들만 발췌
        direct_children = []
        for child in node:
            c_text = child.get('TEXT', '')
            if c_text:
                direct_children.append(c_text.strip())
        line_map[my_clean] = direct_children

        # 엘리트(@) 여부 및 태생 연도 확인
        is_elite = '@' in my_clean
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0

        # 이름에 @가 있으면 부모(씨수말)의 실적으로 등록
        if is_elite and parent_clean != "Unknown":
            elite_map[parent_clean].append({
                'name': my_clean,
                'year': birth_year
            })

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_map, line_map, None

# --- 화면 구성 시작 ---
st.title("📊 연도별 엘리트 씨수말 랭킹")
st.caption("검색란을 제거하고 랭킹을 1차적으로 먼저 보여줍니다. 체크박스를 누르면 자마 상세 비교가 가능합니다.")

# 데이터 불러오기 (정확히 3개의 변수로 받음)
elite_map, line_map, error = load_data()

if error:
    st.error(f"❌ {error}")
    st.stop()

# 사이드바 설정
st.sidebar.header("🔍 설정")
start_y, end_y = st.sidebar.slider("자마 태생 연도 범위:", 1900, 2026, (1900, 2026))

# 랭킹 정렬 로직
sorted_results = []
for sire, daughters in elite_map.items():
    # 설정한 기간 내의 엘리트 딸들만 필터링
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        sorted_results.append((sire, filtered, len(daughters)))

# 실적(필터링된 엘리트 수) 기준 내림차순 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

# --- 결과 출력부 ---
if not sorted_results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    st.success(f"✅ 총 {len(sorted_results)}두의 씨수말 랭킹을 찾았습니다.")
    
    for i, (sire, daughters, total_count) in enumerate(sorted_results[:50], 1):
        # 레이아웃: 체크박스(0.05) + 씨수말 정보(0.95)
        c1, c2 = st.columns([0.05, 0.95])
        
        # 2차 결과(선으로 연결된 자마)를 보기 위한 체크박스
        is_open = c1.checkbox("", key=f"rank_{i}")
        
        with c2:
            stars = "⭐" * min(len(daughters), 10)
            st.markdown(f"**[{i}위] {sire}** (기간 내 @: {len(daughters)}두 / 전체 @: {total_count}두) {stars}")
            
            # 체크박스 선택 시에만 '실제로 선으로 연결된' 데이터 노출
            if is_open:
                with st.container(border=True):
                    st.write(f"📂 **{sire}** 배출 엘리트 종빈마(@)의 선 연결 자마 분석")
                    for elite_mare in daughters:
                        # line_map에서 엘리트 종빈마의 가지에 직접 연결된 자식들만 발췌
                        kids = line_map.get(elite_mare['name'], [])
                        
                        st.markdown(f"👉 **엘리트 종빈마: {elite_mare['name']}**")
                        if kids:
                            # 자마들을 3열로 나누어 출력
                            sub_cols = st.columns(3)
                            for idx, k_name in enumerate(kids):
                                sub_cols[idx % 3].write(f"- 🐎 {k_name}")
                        else:
                            st.caption("연결된 하부 자마 데이터가 없습니다.")
        st.divider()
