import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 시스템", layout="wide")

# CSS 스타일 설정 (색상 및 폰트)
st.markdown("""
    <style>
    .sire-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #333;
    }
    .sire-title {
        font-weight: bold;
        font-size: 1.6em;
        color: #333333;
        margin-bottom: 10px;
    }
    .elite-mare {
        color: #1E90FF !important;
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 10px;
        margin-left: 10px;
    }
    .progeny-item {
        margin-left: 40px;
        margin-bottom: 5px;
        color: #555555;
        font-size: 1.05em;
    }
    hr { margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로딩 함수 (캐시를 일시적으로 비활성화하여 파일 로딩 오류 체크)
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, "파일을 찾을 수 없습니다. 경로를 확인해주세요."

    try:
        # 파일 내용을 먼저 읽어서 비어있는지 확인
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_data = f.read()
            if not xml_data.strip():
                return None, "파일 내용이 비어 있습니다."
        
        root = ET.fromstring(xml_data)
        
        # ID 맵핑 (화살표 추적용)
        id_map = {}
        for node in root.iter('node'):
            nid = node.get('ID')
            if nid:
                id_map[nid] = node.get('TEXT', '')

        year_pattern = re.compile(r'(\d{4})')
        elite_sire_map = defaultdict(list)

        def traverse(node, parent_text="Unknown"):
            my_text = node.get('TEXT', '')
            if my_text and '@' in my_text:
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                
                progeny = []
                # 화살표 연결 자마 추출
                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_map:
                        progeny.append(f"🔗 [연결] {id_map[dest_id]}")
                
                # 하위 가지 자마 추출
                for child in node.findall('node'):
                    c_text = child.get('TEXT', '')
                    if c_text:
                        progeny.append(f"🌿 [가지] {c_text}")

                mare_info = {
                    'name': my_text.strip(),
                    'year': birth_year,
                    'progeny': progeny
                }
                if parent_text != "Unknown":
                    elite_sire_map[parent_text.strip()].append(mare_info)
            
            for child in node.findall('node'):
                traverse(child, my_text)

        traverse(root)
        return elite_sire_map, None
    except Exception as e:
        return None, f"분석 중 오류 발생: {str(e)}"

# --- 메인 화면 ---
st.title("🐎 씨수말 랭킹 및 엘리트 자마 상세 (자동 펼침)")

# 보안 암호
password = st.text_input("접속 암호", type="password")
if password != "3811":
    if password: st.error("암호 오류")
    st.stop()

elite_map, err = load_and_analyze_data()
if err:
    st.error(err)
    st.stop()

# 사이드바 설정
start_y, end_y = st.sidebar.slider("종빈마 출생 연도 설정", 1900, 2030, (1900, 2026))

# 데이터 정리
results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

results.sort(key=lambda x: len(x[1]), reverse=True)

# --- 결과 출력 (클릭 없이 바로 보임) ---
if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    for i, (sire, daughters, total) in enumerate(results[:50], 1):
        # 씨수말 구역 시작
        st.markdown(f"""
            <div class="sire-container">
                <div class="sire-title">{i}위. {sire} (기간내: {len(daughters)} / 누적: {total})</div>
                <hr>
        """, unsafe_allow_html=True)
        
        for d in daughters:
            # 엘리트 종빈마 (파란색 강조)
            st.markdown(f"<div class='elite-mare'>⭐ {d['name']} ({d['year']}년생)</div>", unsafe_allow_html=True)
            
            # 자마 목록
            if d['progeny']:
                for p in d['progeny']:
                    st.markdown(f"<div class='progeny-item'>{p}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='progeny-item' style='color:#bbb;'>- 연결된 자마 정보 없음</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True) # 구역 끝
