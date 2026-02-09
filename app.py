import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 비교기", layout="wide")

# 2. [1차 로직] 데이터 로딩 및 분석 함수 (계층 구조 분석)
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
    
    # 데이터 저장소
    elite_sire_map = defaultdict(list) # 랭킹용 (씨수말 -> @ 엘리트 자마 리스트)
    node_children_map = {}            # 가지연결용 (부모노드 -> 직계 자식노드 리스트)

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        # 정보 분석
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0
        is_elite = '@' in my_clean

        # [가지연결 데이터 수집] 현재 노드의 직계 자식들만 발췌
        direct_children = []
        for child in node:
            child_text = child.get('TEXT', '')
            if child_text:
                direct_children.append(child_text.strip())
        
        node_children_map[my_clean] = direct_children

        # [랭킹 데이터 수집] @ 표시가 있는 말만 씨수말 실적으로 저장
        if is_elite and parent_clean != "Unknown":
            elite_sire_map[parent_clean].append({
                'name': my_clean,
                'year': birth_year
            })

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_sire_map, node_children_map, None

# --- 메인 화면 시작 ---
st.title("🐎 암말우성 씨수말 & 종빈마 통합 검색 (가지연결 방식)")

# [보안] 암호 확인
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password: st.error("암호가 틀렸습니다.")
    st.stop()

# [1차 실행] 데이터 불러오기
elite_map, children_map, error_message = load_and_analyze_data()
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

# --- [2차 로직: 화면 출력 및 체크박스 제어] ---
st.markdown("### 📊 연도별 엘리트 씨수말 랭킹")
st.caption("※ 체크박스를 선택하면 해당 엘리트 종빈마(@)로부터 '가지로 직접 연결된' 자마들만 추출합니다.")

# 랭킹 데이터 정렬
sorted_results = []
for sire_name, daughters in elite_map.items():
    filtered = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered:
        sorted_results.append((sire_name, filtered, len(daughters)))

sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if not sorted_results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    st.info(f"✅ 총 {len(sorted_results)}두의 씨수말이 검색되었습니다.")
    
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results[:50], 1):
        # 1. 랭킹 기본 정보 표시 (1차적 결과)
        stars = "⭐" * min(len(daughters), 10)
        
        # 체크박스 레이아웃
        cols = st.columns([0.05, 0.95])
        chk_key = f"chk_{i}_{sire_name}"
        is_selected = cols[0].checkbox("", key=chk_key)
        
        with cols[1]:
            # 씨수말 기본 정보 출력
            st.markdown(f"**[{i}위] {sire_name}** (기간 내 @: {len(daughters)}두 / 전체 @: {total_count}두) {stars}")
            
            # 2. 체크박스 선택 시 가지연결 자마 상세 분석 (2차적 결과)
            if is_selected:
                with st.container(border=True):
                    st.write(f"🔎 **{sire_name}** 배출 엘리트 자마들의 하부 가지(자마) 분석")
                    for d in daughters:
                        # 가지연결 로직: 엘리트 종빈마의 직계 자식 노드만 가져옴
                        offspring = children_map.get(d['name'], [])
                        
                        st.markdown(f"👉 **엘리트 종빈마: {d['name']}**")
                        if offspring:
                            # 자마들을 3열로 표시
                            sub_cols = st.columns(3)
                            for idx, child_name in enumerate(offspring):
                                sub_cols[idx % 3].write(f"- 🐎 {child_name}")
                        else:
                            st.caption("연결된 하부 가지(자마) 데이터가 없습니다.")
        st.divider()
