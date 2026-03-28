import os
import sys

# Ensure project root is on sys.path so imports like `from app import create_app` work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import User, HoCau, LoaiCa, HoCauLoaiCa, DatCho, KhuyenMai, DanhGia


app = create_app()

with app.app_context():
    # Clear and create
    db.drop_all()
    db.create_all()

    # Create admin
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('admin123')

    user1 = User(username='khach', email='khach@example.com', role='customer')
    user1.set_password('password')

    db.session.add_all([admin, user1])
    db.session.commit()

    # Create ponds
    p1 = HoCau(name='Hồ Cầu Long Biên', description='Hồ đẹp, gần trung tâm', address='Long Biên, Hà Nội', district='Long Biên', area=500.0, price_per_hour=150000)
    p2 = HoCau(name='Hồ Cầu Tây Hồ', description='Hồ rộng, view yên tĩnh', address='Tây Hồ, Hà Nội', district='Tây Hồ', area=800.0, price_per_hour=200000)
    db.session.add_all([p1, p2])
    db.session.commit()

    # Fish types
    f1 = LoaiCa(name='Cá chép', description='Cá to', price=50000)
    f2 = LoaiCa(name='Cá trắm', description='Cá khỏe', price=70000)
    db.session.add_all([f1, f2])
    db.session.commit()

    # Link fish to ponds
    link1 = HoCauLoaiCa(ho_cau_id=p1.id, loai_ca_id=f1.id, quantity=20)
    link2 = HoCauLoaiCa(ho_cau_id=p2.id, loai_ca_id=f2.id, quantity=15)
    db.session.add_all([link1, link2])
    db.session.commit()

    # Sample booking
    from datetime import date, time
    b1 = DatCho(user_id=user1.id, ho_cau_id=p1.id, date=date.today(), start_time=time(hour=8, minute=0), end_time=time(hour=11, minute=0), num_people=2, status='confirmed')
    db.session.add(b1)
    db.session.commit()

    # Promotion
    km = KhuyenMai(code='KM10', title='Giảm 10%', description='Giảm 10% cho đơn đặt trong tuần', percent=10.0)
    db.session.add(km)
    db.session.commit()

    # Review
    r1 = DanhGia(user_id=user1.id, ho_cau_id=p1.id, rating=5, content='Rất thích hồ này', approved=True)
    db.session.add(r1)
    db.session.commit()

    print('Đã tạo dữ liệu mẫu. Admin: admin/admin123, User: khach/password')

