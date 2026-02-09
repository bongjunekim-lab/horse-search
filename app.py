import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 씨수말 랭킹 시스템", layout="wide")

# 2. 데이터 분석 함수 (검증된 가지연결 로직)
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
    elite_sire_map = defaultdict(list)
    branch_map = {} # 노드 텍스트를 키로 하여 하위 가지(자식)들의 텍스트를 저장

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        # [핵심 요청사항: 가지연결 추출] 현재 노드 바로 아래에 붙어 있는 자식들만 발췌
        direct_children = []
        for child in node:
            child_text = child.get('TEXT', '')
            if child_text:
                direct_children.append(child_text.strip())
        
        branch_map[my_clean] = direct_children

        # 엘리트(@) 및 연도 추출
        is_elite = '@' in my_clean
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0

        # 씨수말(부모) 실적으로 엘리트 자마 등록
        if is_elite and parent_clean != "Unknown":
            elite_sire_map[parent_clean].append({
                'name': my_clean,
                'year': birth_year
            })

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_sire_map, branch_map, None

# --- 메인 화면 시작 ---
st.title("📊 연도별 엘리트 씨수말 랭킹")
st.caption("요청하신 대로 검색란을 삭제하고 랭킹 리스트를 1차적으로 먼저 보여줍니다.")

# 데이터 불러오기
elite_map, branch_map, error_message = load_and_analyze_data()
if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

# 사이드바: 기간 필터
st.sidebar.header("🔍 설정")
start_year, end_year = st.sidebar.slider(
    "자마 태생 연도 범위:",
    min_value=1900, max_value=2030,
    value=(1900, 2026)
)

# 랭킹 데이터 정렬 및 필터링
sorted_results = []
for sire_name, elites in elite_map.items():
    filtered = [e for e in elites if start_year <= e['year'] <= end_year]
    if filtered:
        sorted_results.append((sire_name, filtered, len(elites)))

# 배출 수 기준 내림차순 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

# --- 결과 출력 ---
if not sorted_results:
    st.warning("해당 기간 내에 검색된 엘리트 데이터가 없습니다.")
else:
    st.success(f"✅ 총 {len(sorted_results)}두의 씨수말이 검색되었습니다. (상위 50위)")
    
    for i, (sire_name, elites, total_count) in enumerate(sorted_results[:50], 1):
        # 레이아웃 구성: 체크박스 + 씨수말 정보
        cols = st.columns([0.05, 0.95])
        
        chk_key = f"chk_{i}_{sire_name}"
        show_detail = cols[0].checkbox("", key=chk_key) # 요구하신 체크박스 기능
        
        with cols[1]:
            stars = "⭐" * min(len(elites), 10)
            st.markdown(f"**[{i}위] {sire_name}** (기간 내 @: {len(elites)}두 / 전체 @: {total_count}두) {stars}")
            
            # 체크박스 선택 시에만 '실제로 선으로 연결된' 자마 데이터 노출
            if show_detail:
                with st.container(border=True):
                    st.write(f"📂 **{sire_name}** 배출 엘리트 종빈마(@)의 선으로 연결된 자마 리스트")
                    for elite_mare in elites:
                        # 검증된 가지연결 데이터(Branch) 발췌
                        offspring = branch_map.get(elite_mare['name'], [])
                        
                        st.markdown(f"👉 **엘리트 종빈마: {elite_mare['name']}**")
                        if offspring:
                            # 자마들을 3열로 정렬하여 표시
                            sub_cols = st.columns(3)
                            for idx, child_name in enumerate(offspring):
                                sub_cols[idx % 3].write(f"- 🐎 {child_name}")
                        else:
                            st.caption("이 말 아래로 연결된 하부 가지(자마) 데이터가 없습니다.")
        st.divider()
