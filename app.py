import os, uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import database, image_processing, text_processing, scoring, visualization
from auth import official_required, verify_login, login_user, logout_user, is_logged_in, current_user

app = Flask(__name__)
app.secret_key = os.environ.get('WILDCER_SECRET', 'wildcer-dev-secret-change-in-production')
UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOADS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOADS, exist_ok=True)
database.init_db()

def allowed(f): return '.' in f and f.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','gif','webp'}
def save_img(f):
    if f and f.filename and allowed(f.filename):
        n = secure_filename(uuid.uuid4().hex + '.' + f.filename.rsplit('.', 1)[1].lower())
        p = os.path.join(UPLOADS, n); f.save(p); return n
    return None

@app.context_processor
def ctx(): return dict(official_logged_in=is_logged_in(), official_user=current_user())

# ── Public pages ──────────────────────────────────────────────────────────────
@app.route('/')
def home(): return render_template('home.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/our-work')
def our_work(): return render_template('our_work.html')

@app.route('/opportunities')
def opportunities(): return render_template('opportunities.html')

@app.route('/publications')
def publications(): return render_template('publications.html')

@app.route('/csr-partnership')
def csr(): return render_template('csr.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

@app.route('/wildlife-rescue')
def wildlife_rescue(): return render_template('wildlife_rescue.html')

@app.route('/donate')
def donate(): return render_template('donate.html')

@app.route('/support')
def support(): return render_template('support.html')

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/officials/login', methods=['GET', 'POST'])
def login():
    if is_logged_in(): return redirect(url_for('dashboard'))
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '')
        if verify_login(u, p):
            login_user(u)
            flash(f"Welcome, {current_user()['name']}.", 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/officials/logout')
def logout():
    logout_user(); flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ── Protected dashboard ───────────────────────────────────────────────────────
@app.route('/wildlife/dashboard')
@official_required
def dashboard(): return render_template('wildlife/dashboard.html', user=current_user(), counts=database.get_rescue_counts())

# ── Public API ────────────────────────────────────────────────────────────────
@app.route('/api/rescue/submit', methods=['POST'])
def api_submit():
    try:
        species        = request.form.get('species', '').strip()
        location       = request.form.get('location', '').strip()
        description    = request.form.get('description', '').strip()
        name           = request.form.get('reporter_name', '').strip()
        phone          = request.form.get('reporter_phone', '').strip()
        latitude       = request.form.get('latitude', type=float)
        longitude      = request.form.get('longitude', type=float)
        injured_since  = request.form.get('injured_since', 'unknown').strip() or 'unknown'

        if not all([species, location, description]):
            return jsonify({'error': 'Species, location and description are required.'}), 400

        # Accept base64 camera image or file upload
        img_path = None
        b64 = request.form.get('image_b64', '').strip()
        if b64 and b64.startswith('data:image'):
            import base64 as _b64, uuid as _uuid
            header, data = b64.split(',', 1)
            ext = 'jpg'
            if 'png' in header: ext = 'png'
            elif 'webp' in header: ext = 'webp'
            fname = _uuid.uuid4().hex + '.' + ext
            fpath = os.path.join(UPLOADS, fname)
            with open(fpath, 'wb') as f:
                f.write(_b64.b64decode(data))
            img_path = fname
        else:
            img_path = save_img(request.files.get('image'))

        inj  = image_processing.analyze_image(img_path)
        txt  = text_processing.analyze_text(description)
        spc  = scoring.get_species_score(species)
        tim  = scoring.get_time_score(datetime.now())
        injs = scoring.get_injured_since_score(injured_since)
        score, level = scoring.compute_priority_score(inj, txt, spc, tim, injs)

        cid = database.insert_case({
            'species': species, 'location': location, 'description': description,
            'image_path': img_path, 'latitude': latitude, 'longitude': longitude,
            'injury_score': inj, 'text_score': txt, 'species_score': spc,
            'time_score': tim, 'priority_score': score, 'priority_level': level,
            'injured_since': injured_since})
        return jsonify({'success': True, 'case_id': cid, 'priority_level': level}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Officials-only API ────────────────────────────────────────────────────────
@app.route('/api/rescue/cases')
@official_required
def api_cases(): return jsonify(database.get_all_cases())

@app.route('/api/rescue/attend', methods=['POST'])
@official_required
def api_attend():
    try:
        case_id = request.json.get('case_id')
        attended = request.json.get('attended', True)
        database.update_attended(case_id, attended)
        counts = database.get_rescue_counts()
        return jsonify({'success': True, 'counts': counts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rescue/counts')
@official_required
def api_counts():
    return jsonify(database.get_rescue_counts())

@app.route('/api/rescue/charts')
@official_required
def api_charts():
    cases = database.get_all_cases()
    return jsonify({'priority_distribution': visualization.get_priority_distribution(cases),
                    'species_distribution':  visualization.get_species_distribution(cases),
                    'score_breakdown':       visualization.get_score_breakdown(cases),
                    'map_markers':           visualization.get_map_markers(cases)})

@app.route('/api/rescue/seed', methods=['POST'])
@official_required
def api_seed():
    demo = [
        {'species':'Bengal Tiger','location':'Tadoba Andhari Tiger Reserve, Maharashtra',
         'description':'Tiger found with leg wound near village boundary, unable to walk properly. Urgent attention needed.',
         'image_path':None,'latitude':20.1564,'longitude':79.3288,'injury_score':35,'text_score':28,'species_score':27,'time_score':20},
        {'species':'Sloth Bear','location':'Pench Tiger Reserve, Madhya Pradesh',
         'description':'Bear cub separated from mother, appears injured and distressed near forest edge.',
         'image_path':None,'latitude':21.7646,'longitude':79.3129,'injury_score':26,'text_score':20,'species_score':18,'time_score':15},
        {'species':'Indian Vulture','location':'Melghat Tiger Reserve, Amravati',
         'description':'Vulture found grounded and unable to fly. Wing appears broken.',
         'image_path':None,'latitude':21.5731,'longitude':77.1614,'injury_score':22,'text_score':18,'species_score':18,'time_score':12},
        {'species':'Leopard','location':'Nagpur District, Maharashtra',
         'description':'Leopard spotted near human settlement with visible injury on front paw.',
         'image_path':None,'latitude':21.1458,'longitude':79.0882,'injury_score':28,'text_score':22,'species_score':21,'time_score':18},
        {'species':'Indian Elephant','location':'Kaziranga National Park, Assam',
         'description':'Elephant calf separated from herd, limping badly, very distressed.',
         'image_path':None,'latitude':26.5775,'longitude':93.1711,'injury_score':28,'text_score':20,'species_score':26,'time_score':15},
        {'species':'Barn Owl','location':'Nagpur, Maharashtra',
         'description':'Owl found on road with drooping wing, unable to fly.',
         'image_path':None,'latitude':21.1458,'longitude':79.0882,'injury_score':10,'text_score':10,'species_score':15,'time_score':5},
    ]
    for c in demo:
        s, l = scoring.compute_priority_score(c['injury_score'],c['text_score'],c['species_score'],c['time_score'])
        c['priority_score'] = s; c['priority_level'] = l; database.insert_case(c)
    return jsonify({'seeded': len(demo)})

@app.route('/uploads/<filename>')
def uploaded_file(filename): return send_from_directory(UPLOADS, filename)

if __name__ == '__main__':
    print("\n  Wild-CER Platform starting...")
    print("  Homepage     ->  http://127.0.0.1:5000/")
    print("  Report Case  ->  http://127.0.0.1:5000/wildlife-rescue")
    print("  Staff Login  ->  http://127.0.0.1:5000/officials/login")
    print("  Dashboard    ->  http://127.0.0.1:5000/wildlife/dashboard")
    print("\n  Login: admin / wildcer2024\n")
    app.run(debug=True, host='0.0.0.0', port=5005)
