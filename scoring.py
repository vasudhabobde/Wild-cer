from datetime import datetime

SP = {
    'amur leopard':30,'javan rhino':30,'tiger':27,'bengal tiger':27,'lion':26,
    'elephant':26,'indian elephant':26,'cheetah':25,'snow leopard':28,'rhino':22,
    'pangolin':20,'indian pangolin':20,'leopard':21,'sloth bear':18,
    'golden eagle':16,'barn owl':15,'eagle':14,'owl':13,'vulture':18,
    'indian vulture':18,'wolf':17,'indian wolf':17,'falcon':13,'turtle':12,
    'deer':8,'fox':9,'bat':8,'squirrel':6,'rabbit':5,'cat':5,'dog':5,
    'python':14,'cobra':13,'crocodile':16,'gharial':18,'monitor lizard':12,
    'hyena':14,'striped hyena':14,'jackal':9,'otter':12,'peacock':8,
    'heron':8,'stork':9,'crane':10,'sarus crane':12
}

# How long the animal has been injured → urgency boost (added directly to time_score)
# Longer = more urgent (suffering longer, condition likely worsening)
INJURED_SINCE_BOOST = {
    'just_now':    0,    # just found — no extra urgency yet
    'lt_1h':       8,    # less than 1 hour
    '1_3h':        16,   # 1–3 hours — significant
    '3_6h':        22,   # 3–6 hours — serious
    '6_12h':       27,   # 6–12 hours — very serious
    'gt_12h':      30,   # more than 12 hours — critical
    'unknown':     12,   # unknown → moderate boost (err on side of caution)
}

def get_species_score(n):
    if not n: return 10.0
    n = n.lower()
    if n in SP: return float(SP[n])
    for k, v in SP.items():
        if k in n: return float(v)
    return 10.0

def get_time_score(dt=None):
    """Time since the report was submitted (how long ago report came in)."""
    if dt is None: return 15.0
    return round(min(30.0, (datetime.now() - dt).total_seconds() / 3600 * 5), 2)

def get_injured_since_score(injured_since):
    """Extra urgency score based on how long the animal has been injured."""
    if not injured_since:
        return 12.0   # default moderate
    return float(INJURED_SINCE_BOOST.get(injured_since, 12.0))

def compute_priority_score(inj, txt, spc, tim, injured_since_boost=0.0):
    """
    Weights:
      35% image injury score
      25% text description severity
      20% species conservation importance
      10% time since report submitted
      10% time animal has been injured (new — more urgent if injured longer)
    """
    inj_pct  = (inj / 40.0)  * 100
    txt_pct  = (txt / 30.0)  * 100
    spc_pct  = (spc / 30.0)  * 100
    tim_pct  = (tim / 30.0)  * 100
    inj_s_pct= (min(injured_since_boost, 30.0) / 30.0) * 100

    raw = (0.35 * inj_pct +
           0.25 * txt_pct +
           0.20 * spc_pct +
           0.10 * tim_pct +
           0.10 * inj_s_pct)

    s = round(min(100.0, max(0.0, raw)), 2)
    level = 'HIGH' if s >= 71 else ('MEDIUM' if s >= 41 else 'LOW')
    return s, level
