import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    # ensure tables match models (recreate schema for test run)
    db.drop_all()
    db.create_all()
    # create admin user if not exists for testing
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

with app.test_client() as c:
    # first check public routes
    for path in ['/', '/auth/login', '/auth/register']:
        resp = c.get(path)
        print(path, resp.status_code)
        if resp.status_code == 200:
            print('OK HTML length', len(resp.data))

    # Instead of posting the login form (CSRF), set the login session directly
    with c.session_transaction() as sess:
        admin_user = User.query.filter_by(username='admin').first()
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True

    # now admin routes should be accessible
    for path in ['/admin/thong_ke', '/admin/api/thong_ke', '/admin/']:
        resp = c.get(path)
        print(path, resp.status_code)
        if resp.status_code == 200:
            print('OK HTML length', len(resp.data))

