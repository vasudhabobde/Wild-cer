from collections import Counter
def get_priority_distribution(c):
    x=Counter(i['priority_level'] for i in c)
    return {'labels':['HIGH','MEDIUM','LOW'],'data':[x.get('HIGH',0),x.get('MEDIUM',0),x.get('LOW',0)]}
def get_species_distribution(c,n=8):
    x=Counter(i['species'].strip().title() for i in c if i.get('species'))
    t=x.most_common(n)
    return {'labels':[i[0] for i in t],'data':[i[1] for i in t]}
def get_score_breakdown(c):
    if not c: return {'labels':[],'data':[]}
    avg=lambda k:round(sum(i.get(k,0) for i in c)/len(c),2)
    return {'labels':['Injury','Text','Species','Time'],'data':[avg('injury_score'),avg('text_score'),avg('species_score'),avg('time_score')]}
def get_map_markers(c):
    return [{'id':i['id'],'lat':i['latitude'],'lng':i['longitude'],'species':i['species'],'location':i['location'],'priority_level':i['priority_level'],'priority_score':i['priority_score']} for i in c if i.get('latitude') and i.get('longitude')]
