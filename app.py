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
    # 엘리트(@) 자마 데이터만 저장하는 맵
    elite_sire_map = defaultdict(list)

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        parent_clean = parent_text.strip()

        if my_text:
            # 이름에 '@'가 포함된 경우만 분석 대상으로 삼음
            if '@' in my_text:
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                
                mare_info = {
                    'name': my_text.strip(),
                    'year': birth_year,
                    'is_elite': True
                }

                if parent_clean and parent_clean != "Unknown":
                    # 씨수말(부마) 별로 엘리트 자마 정보를 저장
                    elite_sire_map[parent_clean].append(mare_info)
        
        for child in node:
            traverse(child, parent_text=my_text)

    traverse(root)
    return elite_sire_map, None

# --- 메인 화면 시작 ---
st.title("🐎 암말우성 씨수말 랭킹 검색")

# [보안] 암호 확인
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password:
        st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 불러오기 (종빈마 검색용 full_map 제거)
elite_map, error_message = load_and_analyze_data()
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

# --- [종빈마 검색 기능 삭제됨] ---

# --- [엘리트 씨수말 랭킹] ---
st.markdown("### 📊 암말우성 씨수말 순위")
st.caption("※ 이름에 '@'가 포함된 엘리트 종빈마 배출 수를 기준으로 집계합니다.")

sorted_results = []
for sire_name, daughters in elite_map.items():
    # 설정된 기간 내에 태어난 엘리트 자마들만 필터링
    filtered = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered:
        # (씨수말 이름, 필터링된 리스트, 전체 엘리트 수)
        sorted_results.append((sire_name, filtered, len(daughters)))

# 기간 내 엘리트 자마가 많은 순으로 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if sorted_results:
    st.info(f"✅ 총 {len(sorted_results)}두의 씨수말이 검색되었습니다.")
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results[:50], 1):
        stars = "⭐" * min(len(daughters), 10)
        
        # UI 개선: 순위와 이름, 개수를 보기 쉽게 표시
        with st.expander(f"[{i}위] {sire_name} (선택기간: {len(daughters)}두 / 누적: {total_count}두) {stars}"):
            for d in daughters:
                st.write(f"- ⭐ {d['name']} ({d['year']}년생)")
else:
    st.warning("해당 조건에 맞는 데이터가 없습니다.")
