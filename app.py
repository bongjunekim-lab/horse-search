import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 페이지 설정
st.set_page_config(page_title="엘리트 종빈마 자마 검색", layout="wide")

# --- 1. 데이터 로딩 및 분석 함수 ---
@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, f"파일을 찾을 수 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, f"파일 로딩 오류: {e}"

    year_pattern = re.compile(r'(\d{4})')
    sire_map = defaultdict(list)

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        parent_clean = parent_text.strip()

        if my_text:
            year_match = year_pattern.search(my_text)
            birth_year = int(year_match.group(1)) if year_match else 0
            is_elite = '@' in my_text

            mare_info = {
                'name': my_text.strip(),
                'year': birth_year,
                'is_elite': is_elite
            }

            # 부모 이름만 있으면 무조건 자식으로 등록 (필터링 해제)
            if parent_clean and parent_clean != "Unknown":
                sire_map[parent_clean].append(mare_info)
        
        for child in node:
            traverse(child, parent_text=my_text)

    traverse(root)
    return sire_map, None

# --- 2. 메인 화면 로직 ---
st.title("🐎 암말우성 씨수말 & 종빈마 검색")

# 암호 확인
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":  # 기존 암호 유지
    if password:
        st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 불러오기
sire_map, error_message = load_and_analyze_data()
if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

# 사이드바 설정
st.sidebar.header("🔍 검색 옵션")
start_year, end_year = st.sidebar.slider(
    "검색할 기간(자마 태생 연도)을 선택하세요:",
    min_value=1900, max_value=2030,
    value=(1900, 2024)
)

# --- [핵심 기능: 종빈마 자마 검색] ---
st.markdown("### 🔍 엘리트 종빈마 자마 검색")
st.info("찾고 싶은 종빈마(엄마)의 이름을 입력하세요. 연결된 모든 자마가 검색됩니다.")

search_keyword = st.text_input("종빈마 이름을 입력하세요 (예: Mariah's Storm, Buy The Cat)", placeholder="영문 이름을 입력해 주세요")

if search_keyword:
    st.markdown(f"#### 🔎 '{search_keyword}' 검색 결과")
    found_mom = False
    
    for parent_name, children_list in sire_map.items():
        if search_keyword.lower() in parent_name.lower():
            found_mom = True
            with st.container():
                st.success(f"✅ **[{parent_name}]** (이)가 배출한 자마 목록")
                # 연도순 정렬
                sorted_children = sorted(children_list, key=lambda x: x['year'])
                for child in sorted_children:
                    # 엘리트 마크 표시
                    elite_tag = " [ELITE @]" if child['is_elite'] else ""
                    st.write(f"- 🐎 **{child['name']}** ({child['year']}년생){elite_tag}")
            st.divider()

    if not found_mom:
        st.warning(f"❌ '{search_keyword}' 이름으로 등록된 종빈마 데이터를 찾을 수 없습니다.")

# --- [기존 기능: 연도별 씨수말 랭킹] ---
st.divider()
st.markdown("### 📊 연도별 씨수말 배출 랭킹")

sorted_results = []
for sire_name, daughters in sire_map.items():
    # 선택한 연도 범위 내의 자마만 필터링
    filtered = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered:
        sorted_results.append((sire_name, filtered, len(daughters)))

# 자마가 많은 순서대로 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if sorted_results:
    st.success(f"✅ 총 {len(sorted_results)}두의 씨수말 데이터를 찾았습니다.")
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results[:50], 1): # 상위 50개만 표시
        with st.expander(f"[{i}위] {sire_name} (기간 내: {len(daughters)}두 / 전체: {total_count}두)"):
            for d in daughters:
                st.write(f"- {d['name']} ({d['year']}년생)")
else:
    st.warning("선택한 기간에 해당하는 데이터가 없습니다.")
