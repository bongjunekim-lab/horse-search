import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 비교기", layout="wide")

# 2. 데이터 로딩 및 분석 함수 (가지연결 기반)
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
    # offspring_map: 부모 노드(TEXT) -> 자식 노드들의 정보 리스트
    offspring_map = defaultdict(list)
    # elite_list: 이름에 '@'가 포함된 모든 엘리트 종빈마들의 리스트
    elite_list = []

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0
        is_elite = '@' in my_clean

        info = {
            'name': my_clean,
            'year': birth_year,
            'is_elite': is_elite
        }

        # [가지연결 저장] 부모 노드 밑에 현재 노드를 자식으로 등록
        if parent_clean != "Unknown":
            offspring_map[parent_clean].append(info)
        
        # [엘리트 리스트 저장] 랭킹 및 비교를 위해 @표시된 말만 따로 수집
        if is_elite:
            # 엘리트 말 본인의 정보와 함께 부모(씨수말) 정보도 저장
            info['sire'] = parent_clean
            elite_list.append(info)

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return (offspring_map, elite_list), None

# --- 메인 화면 ---
st.title("🐎 엘리트 종빈마 자마 비교 시스템")

# [보안] 암호 확인
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password: st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 불러오기
data, error_message = load_and_analyze_data()
if error_message:
    st.error(f"❌ {error_message}")
    st.stop()

offspring_map, elite_list = data

# 3. 사이드바 검색 및 필터
st.sidebar.header("🔍 필터 설정")
search_sire = st.sidebar.text_input("씨수말(Sire) 이름 검색", placeholder="예: Mr. Prospector")
selected_year = st.sidebar.slider("태생 연도 범위", 1900, 2026, (1900, 2026))

# 데이터 필터링 (엘리트 종빈마 기준)
filtered_elites = [
    e for e in elite_list 
    if (not search_sire or search_sire.lower() in e['sire'].lower()) and
       (selected_year[0] <= e['year'] <= selected_year[1])
]

# --- 4. 메인 비교 화면 ---
st.markdown(f"### 📊 검색된 엘리트 종빈마: {len(filtered_elites)}두")
st.caption("파란색 체크박스를 선택하면 해당 종빈마가 배출한 자마(가지연결) 목록을 펼쳐서 비교할 수 있습니다.")

if not filtered_elites:
    st.warning("조건에 맞는 엘리트 종빈마가 없습니다.")
else:
    # 테이블 헤더 성격의 구분선
    st.divider()
    
    for i, elite in enumerate(filtered_elites):
        # 한 줄 구성 (체크박스 + 정보)
        cols = st.columns([0.05, 0.95])
        
        # 파란색 느낌을 주는 체크박스 (Streamlit 기본형)
        # 각 체크박스는 고유한 key가 필요하므로 이름과 인덱스를 조합
        is_checked = cols[0].checkbox("", key=f"chk_{i}_{elite['name']}")
        
        # 우측 정보 표시
        with cols[1]:
            st.markdown(f"⭐ **{elite['name']}** (부친: {elite['sire']})")
            
            # 체크박스가 눌렸을 때만 자식(가지연결) 노드들을 보여줌
            if is_checked:
                children = offspring_map.get(elite['name'], [])
                if children:
                    # 자식들을 연도순으로 정렬
                    sorted_children = sorted(children, key=lambda x: x['year'])
                    
                    # 자식들을 박스 안에 예쁘게 나열
                    with st.container(border=True):
                        st.write(f"📂 **{elite['name']}**의 배출 자마 ({len(sorted_children)}두)")
                        child_cols = st.columns(3) # 3열로 나누어 출력
                        for idx, child in enumerate(sorted_children):
                            icon = "⭐" if child['is_elite'] else "🐎"
                            child_cols[idx % 3].write(f"{icon} {child['name']} ({child['year'] if child['year'] > 0 else '미상'}년)")
                else:
                    st.info("이 종빈마 아래로 연결된 자마(가지) 데이터가 없습니다.")
        
        st.divider()


