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
        return None, None, f"파일을 찾을 수 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, None, f"파일 로딩 오류: {e}"

    year_pattern = re.compile(r'(\d{4})')
    
    # [데이터 창고]
    # 1. elite_sire_map: 씨수말 랭킹용 (자식 중 @가 있는 엘리트만 저장)
    elite_sire_map = defaultdict(list)
    # 2. offspring_map: 종빈마 검색용 (엄마 말의 모든 가지연결 자식 저장)
    offspring_map = defaultdict(list)

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        parent_clean = parent_text.strip()
        my_clean = my_text.strip()
        
        # 연도 및 엘리트 여부 추출
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0
        is_elite = '@' in my_clean

        mare_info = {
            'name': my_clean,
            'year': birth_year,
            'is_elite': is_elite
        }

        # [핵심 로직 1] 부모-자식 관계 저장 (가지연결)
        if parent_clean != "Unknown":
            # 종빈마 검색을 위해 모든 관계 저장
            offspring_map[parent_clean].append(mare_info)
            
            # [핵심 로직 2] 랭킹 집계용: 오직 @가 붙은 엘리트만 씨수말의 실적으로 인정
            if is_elite:
                elite_sire_map[parent_clean].append(mare_info)
        
        # 자식 노드로 이동 (재귀)
        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_sire_map, offspring_map, None

# --- 메인 화면 시작 ---
st.title("🐎 엘리트 종빈마 및 자마 통합 검색 시스템")

# [보안] 암호 확인
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password: st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 불러오기
elite_map, full_offspring_map, error_message = load_and_analyze_data()
if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

# 사이드바: 기간 설정
st.sidebar.header("🔍 기간 설정")
start_year, end_year = st.sidebar.slider(
    "자마의 태어난 연도를 선택하세요:",
    min_value=1900, max_value=2030,
    value=(1900, 2026)
)

# --- [기능 1: 엘리트 종빈마 자마 검색] ---
st.divider()
st.markdown("### 🔍 엘리트 종빈마(@) 이름으로 자마(자식) 찾기")
st.caption("엄마 말의 이름을 입력하면, 마인드맵상 '가지연결'로 이어진 모든 자식 노드를 보여줍니다.")

search_keyword = st.text_input("종빈마(엄마) 이름을 입력하세요", placeholder="예: Mariah's Storm, Crimson Saint")

if search_keyword:
    st.markdown(f"#### 🔎 '{search_keyword}' 검색 결과")
    found_any = False
    for mom_name, children in full_offspring_map.items():
        if search_keyword.lower() in mom_name.lower():
            found_any = True
            with st.container():
                # 엄마 말 이름에 @가 있으면 강조
                mom_display = f"⭐ **[{mom_name}]**" if '@' in mom_name else f"**[{mom_name}]**"
                st.success(f"✅ {mom_display} 종빈마의 가지연결 자마 목록")
                for child in sorted(children, key=lambda x: x['year']):
                    icon = "⭐" if child['is_elite'] else "🐎"
                    st.write(f"- {icon} **{child['name']}** ({child['year'] if child['year'] > 0 else '연도미상'}년생)")
            st.divider()
    if not found_any:
        st.warning(f"❌ '{search_keyword}' 이름으로 연결된 자식 데이터를 찾을 수 없습니다.")

# --- [기능 2: 엘리트 배출 씨수말 랭킹] ---
st.divider()
st.markdown("### 📊 연도별 엘리트 씨수말 랭킹 (Broodmare Sire)")
st.caption("※ 오직 이름에 '@'가 포함된 엘리트 종빈마만 집계에 반영됩니다.")

sorted_results = []
for sire_name, daughters in elite_map.items():
    # 필터링: 기간 내에 태어난 '엘리트(@)' 자마들만
    filtered = [d for d in daughters if start_year <= d['year'] <= end_year]
    if filtered:
        # (씨수말 이름, 기간내 엘리트 수, 전체 엘리트 수)
        sorted_results.append((sire_name, filtered, len(daughters)))

# 기간 내 엘리트 자마가 많은 순서로 정렬
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

if sorted_results:
    st.info(f"✅ 총 {len(sorted_results)}두의 엘리트 배출 씨수말이 검색되었습니다.")
    for i, (sire_name, daughters, total_count) in enumerate(sorted_results[:50], 1):
        # 자마 수만큼 별점 표시 (최대 10개)
        stars = "⭐" * min(len(daughters), 10)
        # 랭킹 제목: 전체 실적이 아닌 '엘리트 실적'만 정확히 표시
        with st.expander(f"[{i}위] {sire_name} (기간 내 엘리트: {len(daughters)}두 / 전체 엘리트: {total_count}두) {stars}"):
            for d in daughters:
                st.write(f"- ⭐ {d['name']} ({d['year'] if d['year'] > 0 else '연도미상'}년생)")
else:
    st.warning("선택하신 기간에 해당하는 엘리트 데이터가 없습니다.")



