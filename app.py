import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 검색기", layout="wide")

# 2. 데이터 로딩 및 분석 함수
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
    # 엘리트(@) 전용 맵과 검색용 전체 맵 분리
    elite_sire_map = defaultdict(list)
    full_search_map = defaultdict(list)

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

            if parent_clean and parent_clean != "Unknown":
                # [A] 종빈마 검색용: 모든 말을 저장
                full_search_map[parent_clean].append(mare_info)
                
                # [B] 랭킹 집계용: 오직 이름에 '@'가 있는 엘리트 자마만 저장
                if is_elite:
                    elite_sire_map[parent_clean].append(mare_info)
        
        for child in node:
            traverse(child, parent_text=my_text)

    traverse(root)
    return elite_sire_map, full_search_map, None

# --- 메인 화면 시작 ---
st.title("🐎 암말우성 씨수말 & 종빈마 통합 검색")

# [보안] 암호 확인
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password:
        st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 불러오기
elite_map, full_map, error_message = load_and_analyze_data()
if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

# 사이드바 설정
st.sidebar.header("🔍 기간 설정")
start_year, end_year = st.sidebar.slider(
    "자마의 태어난 연도를 선택하세요:",
    min_value=1900, max_value=2030,
    value=(1900, 2026)
)

# --- [기능 1: 종빈마 자마 검색] ---
st.markdown("### 🔍 종빈마 이름으로 자마(자식) 찾기")
search_keyword = st.text_input("종빈마 이름을 입력하세요", placeholder="예: Mariah's Storm, Buy The Cat")

if search_keyword:
    st.markdown(f"#### 🔎 '{search_keyword}' 검색 결과")
    found_mom = False
    for parent_name, children_list in full_map.items():
        if search_keyword.lower() in parent_name.lower():
            found_mom = True
            with st.container():
                st.success(f"✅ **[{parent_name}]** 종빈마의 배출 자마 목록")
                for child in sorted(children_list, key=lambda x: x['year']):
                    icon = "⭐" if child['is_elite'] else "🐎"
                    st.write(f"- {icon} **{child['name']}** ({child['year']}년생)")
            st.divider()
    if not found_mom:
        st.warning(f"❌ '{search_keyword}' 데이터를 찾을 수 없습니다.")

# --- [기능 2: 엘리트 씨수말 랭킹 (복구 핵심!)] ---
st.divider()
st.markdown("### 📊 연도별 엘리트 씨수말 랭킹 (Broodmare Sire)")
st.caption("※ 오직 이름에 '@'가 포함된 엘리트 종빈마만 집계합니다.")

sorted_results = []
for sire_name, daughters in elite_map.items():
    # 필터링: 기간 내에 태어난 '엘리트' 자마들만
    filtered = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered:
        # (씨수말 이름, 기간내 엘리트 수, 전체 엘리트 수) 저장
        sorted_results.append((sire_name, filtered, len(daughters)))

# 기간 내 엘리트 자마가 많은 순으로 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if sorted_results:
    st.info(f"✅ 총 {len(sorted_results)}두의 엘리트 배출 씨수말이 검색되었습니다.")
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results[:50], 1):
        stars = "⭐" * min(len(daughters), 10)
        # 이제 (전체: 170두)가 아니라 실제 @ 개수인 (전체: 8두) 형식으로 나옵니다.
        with st.expander(f"[{i}위] {sire_name} (기간 내: {len(daughters)}두 / 전체 엘리트: {total_count}두) {stars}"):
            for d in daughters:
                st.write(f"- ⭐ {d['name']} ({d['year']}년생)")
else:
    st.warning("해당 조건에 맞는 엘리트 데이터가 없습니다.")

