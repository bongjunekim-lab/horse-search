import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정
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
    /* G1-7 수말 및 @, # 암말 강조 (적색) */
    .premium-progeny {
        color: #D32F2F !important;
        font-weight: bold;
    }
    .star-daughter {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    .sire-deep-blue-bold {
        color: #0000FF !important;
        font-weight: 900 !important;
    }
    .hr-line {
        margin: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    .score-box {
        background-color: #F8F9FA;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #FFC107;
        margin-bottom: 15px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, None, "파일을 찾을 수 없습니다."
    try:
        tree = ET.parse(file_path); root = tree.getroot()
        id_to_text = {}; id_to_parent_text = {}
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
                progeny_info = []; seen_ids = set()
                mare_pure_name = normalize_name(my_text)
                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_to_text:
                        if dest_id in seen_ids: continue
                        child_raw_text = id_to_text[dest_id]
                        child_pure_name = normalize_name(child_raw_text)
                        if mare_pure_name == child_pure_name: continue
                        progeny_info.append(dest_id)
                        seen_ids.add(dest_id)
                mare_info = {'name': my_text.strip(), 'year': birth_year, 'progeny_ids': progeny_info}
                if parent_text != "Unknown": elite_sire_map[parent_text.strip()].append(mare_info)
            for child in node.findall('node'): traverse(child, my_text)
        traverse(root); return elite_sire_map, id_to_text, id_to_parent_text, None
    except Exception as e: return None, None, None, f"분석 오류: {str(e)}"

# UI 메인
st.title("🐎 암말우성 씨수말 랭킹과 점수")
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.stop()

elite_map, id_to_text, id_to_parent_text, err = load_and_analyze_data()
if err: st.error(err); st.stop()

start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))
results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered: results.append((sire, filtered, len(daughters)))

g1_pattern = re.compile(r'G1-(\d+)')

# 데이터 가공 및 점수 계산 (조건 수정 완료)
scored_results = []
for sire, daughters, total in results:
    n1 = len(daughters) 
    s2 = 0              
    n2 = 0              
    productive_k = set() 
    
    for d in daughters:
        for p_id in d['progeny_ids']:
            child_name = id_to_text.get(p_id, "")
            
            g1_match = g1_pattern.search(child_name)
            is_high_g1 = bool(g1_match and int(g1_match.group(1)) >= 7)
            is_daughter = '암)' in child_name
            
            # N2 조건: @ 또는 # 이 포함된 암말
            is_n2 = ('@' in child_name or '#' in child_name) and is_daughter
            # S2 조건: G1-7 이상이면서 수말(암말 표기가 없는 경우)
            is_s2 = is_high_g1 and not is_daughter
            
            if is_n2:
                n2 += 1
                productive_k.add(d['name'])
            if is_s2:
                s2 += 1
                productive_k.add(d['name'])
                
    k = len(productive_k)
    score = (1.0 * n1) + (1.5 * s2) + (2.0 * n2) + (1.0 * k)
    
    scored_results.append({
        'sire': sire,
        'daughters': daughters,
        'n1': n1,
        's2': s2,
        'n2': n2,
        'k': k,
        'score': score
    })

# 합산 점수 기준 내림차순 정렬
scored_results.sort(key=lambda x: x['score'], reverse=True)

if not scored_results: 
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    for i, data in enumerate(scored_results[:100], 1):
        sire = data['sire']
        daughters = data['daughters']
        n1 = data['n1']
        score = data['score']
        stars = "⭐" * n1
        
        with st.expander(f"[{i}위] {sire} (엘리트 종빈마: {n1}두) {stars} | 🏆 총점: {score:.1f}점"):
            st.markdown(f"""
            <div class='score-box'>
                📊 점수 산출식: (1.0 × N1) + (1.5 × S2) + (2.0 × N2) + (1.0 × K)<br>
                결과: (1.0 × {n1}) + (1.5 × {data['s2']}) + (2.0 × {data['n2']}) + (1.0 × {data['k']}) = <span style='color:red; font-size:1.1em;'>{score:.1f}점</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            sire_to_mothers = defaultdict(set)
            for d in daughters:
                for p_id in d['progeny_ids']:
                    p_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[p_sire_name].add(d['name'])
            nick_sires = [s for s, mothers in sire_to_mothers.items() if len(mothers) >= 2]
            bg_palette = ["#FFEBEE", "#E0F2F1", "#F3E5F5", "#E8F5E9", "#FBE9E7"]
            border_palette = ["#D32F2F", "#00796B", "#7B1FA2", "#388E3C", "#E64A19"]
            nick_style_map = {}
            color_idx = 0
            for ns in nick_sires:
                nick_style_map[ns] = (border_palette[color_idx % 5], bg_palette[color_idx % 5])
                color_idx += 1

            for d in daughters:
                st.markdown(f"<div class='elite-mare'>&#128142; {d['name']}</div>", unsafe_allow_html=True)
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        father_name = id_to_parent_text.get(p_id, "정보 없음")
                        
                        g1_match = g1_pattern.search(child_name)
                        is_high_g1 = bool(g1_match and int(g1_match.group(1)) >= 7)
                        is_daughter = '암)' in child_name
                        is_elite_daughter = ('@' in child_name or '#' in child_name) and is_daughter
                        is_high_g1_son = is_high_g1 and not is_daughter
                        
                        # [1] 자마 스타일 (N2 및 S2 조건 충족 시 적색 클래스 적용)
                        if is_high_g1_son or is_elite_daughter:
                            child_display = f"<span class='premium-progeny'>{child_name}</span>"
                        elif '*' in child_name and is_daughter:
                            child_display = f"<span class='star-daughter'>{child_name}</span>"
                        else: child_display = child_name
                        
                        # [2] 부마 스타일
                        if is_high_g1_son or is_elite_daughter:
                            if father_name in nick_style_map:
                                b_c, bg_c = nick_style_map[father_name]
                                father_display = f"<span style='color:#0000FF; background-color:{bg_c}; font-weight:900; padding:2px 6px; border-radius:4px; border: 1px solid {b_c}60;'>{father_name}</span>"
                            else:
                                father_display = f"<span class='sire-deep-blue-bold'>{father_name}</span>"
                        else:
                            if father_name in nick_style_map:
                                b_c, bg_c = nick_style_map[father_name]
                                father_display = f"<span style='color:{b_c}; background-color:{bg_c}; font-weight:400; padding:2px 6px; border-radius:4px; border: 1px solid {b_c}60;'>{father_name}</span>"
                            else: father_display = f"<b>{father_name}</b>"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_display} ({father_display})</div>", unsafe_allow_html=True)

