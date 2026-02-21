import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정: 눈부심 방지 및 가독성 최적화
st.markdown("""
    <style>
    .elite-mare {
        color: #0077CC !important;
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .progeny-item {
        margin-left: 30px;
        margin-bottom: 3px;
        color: #333333;
        font-size: 1.05em;
    }
    .top-progeny {
        color: #800080 !important; /* G1 7승 이상 보라색 */
        font-weight: bold;
    }
    .elite-daughter {
        color: #003366 !important; /* 번식 우수 딸 네이비 */
        font-weight: bold;
    }
    .star-daughter {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    .hr-line {
        margin: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, None, "파일을 찾을 수 없습니다."

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        id_to_text = {}
        id_to_parent_text = {}
        
        for parent in root.iter('node'):
            p_text = parent.get('TEXT', 'Unknown')
            for child in parent.findall('node'):
                c_id = child.get('ID')
                if c_id:
                    id_to_text[c_id] = child.get('TEXT', '')
                    id_to_parent_text[c_id] = p_text

        year_pattern = re.compile(r'(\d{4})')
        elite_sire_map = defaultdict(list)

        def normalize_name(text):
            clean = text.replace('@', '').replace('#', '').replace('*', '')
            clean = clean.replace('암)', '').replace('수)', '').replace('거)', '')
            clean = clean.replace('가.', '').replace('나.', '').replace('다.', '')
            clean = clean.split('(')[0]
            return clean.strip().lower()

        def traverse(node, parent_text="Unknown"):
            my_text = node.get('TEXT', '')
            
            if my_text and '@' in my_text:
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                
                progeny_info = [] 
                seen_ids = set()
                mare_pure_name = normalize_name(my_text)

                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    
                    if dest_id in id_to_text:
                        if dest_id in seen_ids:
                            continue

                        child_raw_text = id_to_text[dest_id]
                        child_pure_name = normalize_name(child_raw_text)
                        
                        if mare_pure_name == child_pure_name:
                            continue
                        
                        progeny_info.append(dest_id)
                        seen_ids.add(dest_id)
                
                mare_info = {
                    'name': my_text.strip(),
                    'year': birth_year,
                    'progeny_ids': progeny_info 
                }
                if parent_text != "Unknown":
                    elite_sire_map[parent_text.strip()].append(mare_info)
            
            for child in node.findall('node'):
                traverse(child, my_text)

        traverse(root)
        return elite_sire_map, id_to_text, id_to_parent_text, None
    except Exception as e:
        return None, None, None, f"분석 오류: {str(e)}"

# --- UI 메인 ---
st.title("🐎 암말우성 씨수말 랭킹 및 1대 자마 성적 분석 (G1-7 기준)")

password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.stop()

elite_map, id_to_text, id_to_parent_text, err = load_and_analyze_data()
if err:
    st.error(err); st.stop()

start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))

results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

results.sort(key=lambda x: len(x[1]), reverse=True)

g1_pattern = re.compile(r'G1-(\d+)')

if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    for i, (sire, daughters, total) in enumerate(results[:100], 1):
        num_mares = len(daughters)
        stars = "⭐" * num_mares
        expander_title = f"[{i}위] {sire} (엘리트 종빈마: {num_mares}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            
            sire_to_mothers = defaultdict(set)
            for d in daughters:
                for p_id in d['progeny_ids']:
                    p_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[p_sire_name].add(d['name'])
            
            nick_sires = [s for s, mothers in sire_to_mothers.items() if len(mothers) >= 2]
            
            # --- [핵심 개선] 20개의 완전히 다른 고대비 색상 팔레트 ---
            palette = [
                ("#E74C3C", "#FDEDEC"), # 1. 강렬한 빨강
                ("#2874A6", "#EBF5FB"), # 2. 파랑 (Mr. Prospector)
                ("#1E8449", "#EAFAF1"), # 3. 녹색 (Roberto)
                ("#8E44AD", "#F4ECF7"), # 4. 보라 (Seattle Slew)
                ("#D35400", "#FEF5E7"), # 5. 짙은 주황
                ("#117A65", "#E8F8F5"), # 6. 청록
                ("#FF1493", "#FFE7F4"), # 7. 핫핑크
                ("#8B4513", "#F4EBE6"), # 8. 갈색
                ("#000080", "#E6E6F2"), # 9. 네이비 (남색)
                ("#B8860B", "#FCF8E8"), # 10. 올리브 골드
                ("#1ABC9C", "#E8F8F5"), # 11. 밝은 민트
                ("#34495E", "#EAECEE"), # 12. 다크 챠콜
                ("#E67E22", "#FDEBD0"), # 13. 당근색
                ("#9B59B6", "#EBDEF0"), # 14. 연보라
                ("#C0392B", "#FADBD8"), # 15. 벽돌색(다크레드)
                ("#27AE60", "#D5F5E3"), # 16. 네프라이트 그린
                ("#F39C12", "#FEF5E7"), # 17. 골드 옐로우
                ("#4A235A", "#F5EEF8"), # 18. 다크 퍼플
                ("#0E6251", "#E8F8F5"), # 19. 다크 청록
                ("#7B241C", "#F9EBEA")  # 20. 버건디 와인색
            ]
            
            # 고정 색상(녹, 파, 보)을 제외한 17개의 자율 할당 팔레트 생성
            reserved_hex = ["#1E8449", "#2874A6", "#8E44AD"]
            available_palette = [c for c in palette if c[0] not in reserved_hex]
            
            nick_color_map = {}
            p_idx = 0
            
            for ns in nick_sires:
                ns_lower = ns.lower()
                # 1. 고정 마명 처리
                if "roberto" in ns_lower:
                    nick_color_map[ns] = ("#1E8449", "#EAFAF1")
                elif "mr. prospector" in ns_lower or "mr.prospector" in ns_lower:
                    nick_color_map[ns] = ("#2874A6", "#EBF5FB")
                elif "seattle slew" in ns_lower:
                    nick_color_map[ns] = ("#8E44AD", "#F4ECF7")
                else:
                    # 2. 남은 17개 색상을 순서대로 돌려가며 무한 할당 (빨간색 도배 방지)
                    nick_color_map[ns] = available_palette[p_idx % len(available_palette)]
                    p_idx += 1

            for d in daughters:
                st.markdown(f"<div class='elite-mare'>💎 {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        father_name = id_to_parent_text.get(p_id, "정보 없음")
                        
                        child_display = child_name
                        
                        g1_match = g1_pattern.search(child_name)
                        is_high_g1 = g1_match and int(g1_match.group(1)) >= 7
                        
                        is_elite_daughter = False 
                        is_star_daughter = False  
                        
                        if '암)' in child_name:
                            parts = child_name.split('암)')
                            prefix = parts[0] 
                            
                            if ('@' in prefix) or ('#' in prefix):
                                is_elite_daughter = True
                            if '*' in prefix:
                                is_star_daughter = True
                        
                        if is_high_g1:
                            child_display = f"<span class='top-progeny'>{child_name}</span>"
                        elif is_elite_daughter:
                            child_display = f"<span class='elite-daughter'>{child_name}</span>"
                        elif is_star_daughter:
                            child_display = f"<span class='star-daughter'>{child_name}</span>"
                        
                        # --- [하이라이트 박스 렌더링] ---
                        if father_name in nick_color_map:
                            text_color, bg_color = nick_color_map[father_name]
                            father_display = f"<span style='color:{text_color}; background-color:{bg_color}; font-weight:900; padding:2px 6px; border-radius:4px; border: 1px solid {text_color}60;'>{father_name}</span>"
                        else:
                            father_display = f"<b>{father_name}</b>"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_display} ({father_display})</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='progeny-item' style='color:#999;'>- 연결된 화살표 자마 정보 없음</div>", unsafe_allow_html=True)
