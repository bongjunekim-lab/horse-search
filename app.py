import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 분석기", layout="wide")

# 2. 데이터 분석 함수 (가지연결 로직 적용)
@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, f"파일을 찾을 수 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, None, f"파일 로딩 오류: {e}"

    year_pattern = re.compile(r'(\d{4})')
    
    # [데이터 저장소]
    # elite_sire_map: 씨수말 -> 그 아래에 있는 @ 엘리트 자마들의 리스트
    elite_sire_map = defaultdict(list)
    # branch_map: 어떤 말(노드) -> 그 말의 바로 아래 가지(자식 노드)들의 텍스트 리스트
    branch_map = {}

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        # 현재 노드의 직계 자식(가지)들 수집
        direct_children = []
        for child in node:
            child_text = child.get('TEXT', '')
            if child_text:
                direct_children.append(child_text.strip())
        
        # 가지연결 정보 저장
        branch_map[my_clean] = direct_children

        # 엘리트(@) 여부 및 연도 확인
        is_elite = '@' in my_clean
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0

        # @가 붙은 엘리트 말이라면 씨수말(부모)의 실적으로 기록
        if is_elite and parent_clean != "Unknown":
            elite_sire_map[parent_clean].append({
                'name': my_clean,
                'year': birth_year
            })

        # 하위 노드로 계속 탐색
        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_sire_map, branch_map, None

# --- 메인 화면 시작 ---
st.title("🐎 엘리트 혈통 및 가지연결 자마 분석")
st.caption("암호 입력을 삭제하여 바로 이용하실 수 있습니다.")

# 데이터 로딩
elite_map, branch_map, error_message = load_and_analyze_data()
if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

# 사이드바: 연도 필터링
st.sidebar.header("🔍 검색 설정")
start_year, end_year = st.sidebar.slider(
    "자마 태생 연도 범위:",
    1900, 2030, (1900, 2026)
)

# 랭킹 데이터 정렬 (1차 결과물)
sorted_results = []
for sire_name, elites in elite_map.items():
    filtered = [e for e in elites if start_year <= e['year'] <= end_year]
    if filtered:
        sorted_results.append((sire_name, filtered, len(elites)))

# 엘리트 배출 수가 많은 순서로 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

# --- 화면 출력 ---
if not sorted_results:
    st.warning("설정된 기간 내에 검색된 엘리트 데이터가 없습니다.")
else:
    st.info(f"✅ 총 {len(sorted_results)}두의 엘리트 배출 씨수말이 검색되었습니다. (상위 50위 표시)")
    
    for i, (sire_name, elites, total_count) in enumerate(sorted_results[:50], 1):
        # 1. 랭킹 기본 정보 표시
        stars = "⭐" * min(len(elites), 10)
        
        cols = st.columns([0.05, 0.95])
        # 2차 결과를 보기 위한 체크박스
        chk_key = f"chk_{i}_{sire_name}"
        show_detail = cols[0].checkbox("", key=chk_key)
        
        with cols[1]:
            st.markdown(f"**[{i}위] {sire_name}** (기간 내 @: {len(elites)}두 / 전체 @: {total_count}두) {stars}")
            
            # 2. 체크박스 선택 시 가지연결 자마 상세 분석 (2차 결과물)
            if show_detail:
                with st.container(border=True):
                    st.write(f"📂 **{sire_name}** 배출 엘리트 종빈마(@)들의 '하부 가지' 분석")
                    for elite_mare in elites:
                        # 가지연결 로직: 엘리트 종빈마 이름으로 branch_map에서 자식들 검색
                        offspring_branches = branch_map.get(elite_mare['name'], [])
                        
                        st.markdown(f"👉 **엘리트 종빈마: {elite_mare['name']}**")
                        if offspring_branches:
                            # 자식들을 3열로 나누어 출력
                            sub_cols = st.columns(3)
                            for idx, child_name in enumerate(offspring_branches):
                                sub_cols[idx % 3].write(f"- 🐎 {child_name}")
                        else:
                            st.caption("이 말 아래로 연결된 하위 가지(자마) 데이터가 없습니다.")
        st.divider()
