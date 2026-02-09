import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 검색기", layout="wide")

# 2. 데이터 로딩 및 분석 함수 (선생님의 "잘 나오는 코드" 로직 100% 유지)
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
    elite_sire_map = defaultdict(list)
    # branch_map: 말 이름 -> 그 아래 '가지'로 직접 연결된 자식들 텍스트 리스트 (자마 추출용)
    branch_map = {}

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()

        # [중요] 현재 노드의 직계 자식(가지)들 텍스트 수집 (선생님 요청 사항)
        direct_children = []
        for child in node:
            c_text = child.get('TEXT', '')
            if c_text:
                direct_children.append(c_text.strip())
        branch_map[my_clean] = direct_children

        # 연도 및 엘리트 여부 추출
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0
        is_elite = '@' in my_clean

        mare_info = {'name': my_clean, 'year': birth_year, 'is_elite': is_elite}

        # 엘리트(@) 자마라면 씨수말(부모)의 실적으로 등록
        if is_elite and parent_clean != "Unknown":
            elite_sire_map[parent_clean].append(mare_info)
        
        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_sire_map, branch_map, None

# --- 메인 화면 시작 ---
st.title("🐎 엘리트 씨수말 및 종빈마 자마 비교")

# [보안] 암호 확인 (기능 유지)
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password: st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 불러오기 (함수 결과 정확히 3개로 받음)
elite_map, branch_map, error_message = load_and_analyze_data()
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

# --- [메인 기능: 엘리트 씨수말 랭킹] ---
st.markdown("### 📊 연도별 엘리트 씨수말 랭킹")
st.caption("씨수말을 클릭하면 엘리트 딸들이 보이고, 딸 옆의 체크박스를 누르면 자마 목록이 나타납니다.")

sorted_results = []
for sire_name, daughters in elite_map.items():
    filtered = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered:
        sorted_results.append((sire_name, filtered, len(daughters)))

# 엘리트 배출 수 기준 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if not sorted_results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    st.info(f"✅ 총 {len(sorted_results)}두의 엘리트 배출 씨수말이 검색되었습니다.")
    
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results[:50], 1):
        stars = "⭐" * min(len(daughters), 10)
        
        # 1단계: 씨수말 클릭 (Expander)
        with st.expander(f"[{i}위] {sire_name} (기간 내 @: {len(daughters)}두 / 전체: {total_count}두) {stars}"):
            st.write(f"📂 **{sire_name}**의 엘리트 딸(@) 목록입니다. 자마를 보려면 체크하세요.")
            
            for idx, d in enumerate(daughters):
                # 2단계: 엘리트 딸 옆에 체크박스 배치
                # 각 체크박스에 고유 ID(key)를 부여하여 충돌 방지
                col1, col2 = st.columns([0.1, 0.9])
                is_checked = col1.checkbox("", key=f"cb_{i}_{idx}")
                col2.write(f"⭐ **{d['name']}** ({d['year']}년생)")
                
                # 3단계: 체크박스 클릭 시에만 해당 딸의 '가지연결' 자마 노출
                if is_checked:
                    kids = branch_map.get(d['name'], [])
                    if kids:
                        with st.container(border=True):
                            st.caption(f"🐎 {d['name']}가 배출한 자마 목록")
                            k_cols = st.columns(3) # 3열로 예쁘게 출력
                            for k_idx, k_name in enumerate(kids):
                                k_cols[k_idx % 3].write(f"- {k_name}")
                    else:
                        st.caption("└ 연결된 자마 데이터가 없습니다.")
            st.divider()
