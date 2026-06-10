import hashlib
from functools import wraps
from flask import session, redirect, url_for, flash
def _h(p): return hashlib.sha256(p.encode()).hexdigest()
OFFICIALS={'admin':_h('wildcer2024'),'rescue_officer':_h('rescue123')}
NAMES={'admin':'Administrator','rescue_officer':'Rescue Officer'}
def verify_login(u,p): return OFFICIALS.get(u.lower())==_h(p)
def login_user(u): session['ok']=True;session['u']=u.lower();session['n']=NAMES.get(u.lower(),u)
def logout_user(): session.clear()
def is_logged_in(): return session.get('ok',False)
def current_user(): return {'username':session.get('u',''),'name':session.get('n','')}
def official_required(f):
    @wraps(f)
    def d(*a,**k):
        if not is_logged_in():
            flash('Please log in to access the dashboard.','warning')
            return redirect(url_for('login'))
        return f(*a,**k)
    return d
