import re
KW={'dying':3,'dead':3,'unconscious':3,'convulsing':3,'critical':3,'bleeding':2.5,'poisoned':2.5,'broken':2.5,'severe':2.5,'trapped':2.5,'emergency':2.5,'injured':2,'wound':2,'limping':2,'distress':2,'hurt':1.5,'weak':1.5,'sick':1,'ill':1}
try:
    import spacy; nlp=spacy.load('en_core_web_sm'); SP=True
except: SP=False
def analyze_text(text):
    if not text: return 5.0
    t=text.lower(); raw=0.0
    if SP:
        for tok in nlp(t): raw+=KW.get(tok.lemma_,0)
    else:
        for w in re.findall(r'\b\w+\b',t): raw+=KW.get(w,0)
    return round(min(30.0,(raw/15.0)*30.0),2)
