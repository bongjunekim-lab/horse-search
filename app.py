import streamlit as st
# --- 비밀번호 기능 시작 ---
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":  # "5500"를 원하는 비밀번호로 바꾸세요
    st.warning("암호가 틀렸습니다. 올바른 암호를 입력해야 보입니다.")
    st.stop()
# --- 비밀번호 기능 끝 ---
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 기본 설정
st.set_page_config(page_title="엘리트 혈통 추적기", page_icon="🧬", layout="wide")

# 2. 제목 및 설명
st.title("🐎 암말우성 씨수말 (Broodmare Sire)")
st.markdown("""
### 💡 프로그램 소개
지정한 기간 내에 태어난 **엘리트 종빈마**를 찾아, 그들의 부친(Broodmare Sire)별로 묶어서 보여줍니다.

> **엘리트 종빈마란?** > G급(Grade) 자마를 줄줄이 배출한, 유전력이 검증된 **슈퍼 씨암말**을 지칭합니다.
""")

# 3. 데이터 로딩 및 분석 함수 (캐싱으로 속도 최적화)
@st.cache_data
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
    merged_sire_map = defaultdict(list)

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

            # (수정됨) 엘리트 여부 상관없이 부모 이름만 있으면 무조건 저장!
            if parent_clean and parent_clean != "Unknown":
                merged_sire_map[parent_clean].append(mare_info)
        
        for child in node:
            traverse(child, parent_text=my_text)

    traverse(root)
    return merged_sire_map, None
# --- 메인 화면 로직 ---

# 데이터 불러오기
sire_map, error_message = load_and_analyze_data()

if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

# 사이드바: 검색 조건 설정
st.sidebar.header("🔍 검색 옵션")
start_year, end_year = st.sidebar.slider(
    "검색할 기간을 선택하세요:",
    min_value=1900, max_value=2030,
    value=(1900, 2030)
)

# --- [종빈마 자마 검색 기능] ---
st.divider()
st.markdown("### 🐎 엘리트 종빈마 자마 검색")
st.caption("찾고 싶은 종빈마(엄마)의 이름을 입력하면, 그 말의 선(Line)에 연결된 자식들을 보여줍니다.")

search_keyword = st.text_input("종빈마(엄마) 이름을 입력하세요", placeholder="예: Mariah's Storm")

if search_keyword:
    st.markdown(f"#### 🔎 '{search_keyword}' 검색 결과")
    found_mom = False
    
    for parent_name, children_list in sire_map.items():
        if search_keyword.lower() in parent_name.lower():
            found_mom = True
            with st.container():
                st.success(f"✅ **[{parent_name}]** (이)가 배출한 자마 목록")
                sorted_children = sorted(children_list, key=lambda x: x['year'])
                for child in sorted_children:
                    st.write(f"- 🐎 **{child['name']}** ({child['year']}년생)")
            st.divider()

    if not found_mom:
        st.warning("검색된 종빈마가 없습니다.")

# --- 원래 결과 분석 로직 (순위표) ---
st.divider()
st.markdown("### 📊 연도별 씨수말 랭킹")

sorted_results = []
for sire_name, daughters in sire_map.items():
    filtered_daughters = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered_daughters:
        sorted_results.append((sire_name, filtered_daughters, len(daughters)))

sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if not sorted_results:
    st.warning(f"⚠️ {start_year}년 ~ {end_year}년 사이에 검색된 엘리트 자마가 없습니다.")
else:
    st.success(f"✅ 총 {len(sorted_results)}두의 씨수말이 배출한 엘리트 자마를 찾았습니다.")
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results, 1):
        with st.expander(f"[{i}위] {sire_name} (검색 기간 내: {len(daughters)}두)"):
            for d in daughters:
                st.write(f"- {d['name']} ({d['year']}년생)")
