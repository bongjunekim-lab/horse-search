results = []
for sire, daughters in elite_map.items():
    filtered = []
    for d in daughters:
        # 연도 조건 확인
        year_condition = start_y <= d['year'] <= end_y
        
        # 검색어 조건 확인 (종빈마 이름 또는 자마 이름에 검색어가 포함되는지)
        name_match = True
        if search_query:
            # 1. 종빈마 이름 확인
            mare_match = search_query in d['name'].lower()
            # 2. 자마들 이름 확인
            progeny_match = any(search_query in id_to_text.get(p_id, "").lower() for p_id in d['progeny_ids'])
            # 3. 씨수말(아비) 이름 확인
            sire_match = search_query in sire.lower()
            
            name_match = mare_match or progeny_match or sire_match
            
        if year_condition and name_match:
            filtered.append(d)
            
    if filtered:
        results.append((sire, filtered, len(daughters)))
