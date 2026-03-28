from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, HoCau, LoaiCa, DatCho, HoCauLoaiCa, HoatDong, DanhGia, ThongBao, KhuyenMai, HoaDon
from forms import LoginForm, RegisterForm, HoCauForm, LoaiCaForm, BookingForm, PromotionForm, InvoiceForm, ReviewForm
from datetime import datetime, date, timedelta
import io, csv


main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)


@main_bp.route('/')
def index():
    ponds = HoCau.query.limit(6).all()
    return render_template('index.html', ponds=ponds)


@main_bp.route('/ho_cau')
def ho_cau_list():
    q = request.args.get('q', '')
    if q:
        ponds = HoCau.query.filter(HoCau.name.contains(q)).all()
    else:
        ponds = HoCau.query.all()
    return render_template('ho_cau_list.html', ponds=ponds, q=q)


@main_bp.route('/ho_cau/<int:pond_id>')
def ho_cau_detail(pond_id):
    pond = HoCau.query.get_or_404(pond_id)
    form = BookingForm()
    review_form = ReviewForm()
    return render_template('ho_cau_detail.html', pond=pond, form=form, review_form=review_form)


@main_bp.route('/ho_cau/<int:pond_id>/calendar')
def ho_cau_calendar(pond_id):
    pond = HoCau.query.get_or_404(pond_id)
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    days = [start_week + timedelta(days=i) for i in range(7)]
    hours = list(range(6, 21))
    bookings = DatCho.query.filter(DatCho.ho_cau_id == pond.id, DatCho.date >= days[0], DatCho.date <= days[-1]).all()
    slots = {d: {h: None for h in hours} for d in days}
    for b in bookings:
        try:
            st = b.start_time.hour
            et = b.end_time.hour
        except Exception:
            continue
        for h in range(st, et):
            if h in slots.get(b.date, {}):
                slots[b.date][h] = b
    return render_template('ho_cau_calendar.html', pond=pond, days=days, hours=hours, slots=slots)


@main_bp.route('/dat_cho/<int:pond_id>', methods=['POST'])
@login_required
def dat_cho(pond_id):
    pond = HoCau.query.get_or_404(pond_id)
    form = BookingForm()
    if form.validate_on_submit():
        b = DatCho(user_id=current_user.id, ho_cau_id=pond.id, date=form.date.data, start_time=form.start_time.data, end_time=form.end_time.data, num_people=form.num_people.data or 1, note=form.note.data)
        db.session.add(b)
        db.session.commit()
        flash('Đặt chỗ thành công, chờ xác nhận', 'success')
        return redirect(url_for('main.ho_cau_detail', pond_id=pond.id))
    flash('Dữ liệu đặt chỗ không hợp lệ', 'danger')
    return redirect(url_for('main.ho_cau_detail', pond_id=pond.id))


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        db.session.commit()
        flash('Cập nhật thông tin cá nhân thành công', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile.html')


@main_bp.route('/notifications')
@login_required
def notifications():
    notices = ThongBao.query.filter((ThongBao.user_id == None) | (ThongBao.user_id == current_user.id)).order_by(ThongBao.created_at.desc()).all()
    return render_template('notifications.html', notices=notices)


@main_bp.route('/notifications/<int:nid>/read', methods=['POST'])
@login_required
def notification_mark_read(nid):
    n = ThongBao.query.get_or_404(nid)
    n.is_read = True
    db.session.commit()
    return redirect(url_for('main.notifications'))


@main_bp.route('/my/bookings')
@login_required
def my_bookings():
    bookings = DatCho.query.filter_by(user_id=current_user.id).order_by(DatCho.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)


@main_bp.route('/my/bookings/<int:bid>/cancel', methods=['POST'])
@login_required
def my_bookings_cancel(bid):
    b = DatCho.query.get_or_404(bid)
    if b.user_id != current_user.id:
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.my_bookings'))
    b.status = 'cancelled'
    db.session.commit()
    flash('Đã hủy đặt chỗ', 'info')
    return redirect(url_for('main.my_bookings'))


@main_bp.route('/my/invoices')
@login_required
def my_invoices():
    invoices = HoaDon.query.filter_by(user_id=current_user.id).order_by(HoaDon.created_at.desc()).all()
    return render_template('my_invoices.html', invoices=invoices)


@main_bp.route('/my/invoices/<int:iid>')
@login_required
def my_invoice_view(iid):
    inv = HoaDon.query.get_or_404(iid)
    if inv.user_id != current_user.id:
        flash('Không có quyền xem hoá đơn này', 'danger')
        return redirect(url_for('main.my_invoices'))
    return render_template('my_invoice_view.html', inv=inv)


@main_bp.route('/ho_cau/<int:pond_id>/review', methods=['POST'])
@login_required
def ho_cau_review(pond_id):
    pond = HoCau.query.get_or_404(pond_id)
    form = ReviewForm()
    if form.validate_on_submit():
        r = DanhGia(user_id=current_user.id, ho_cau_id=pond.id, rating=int(form.rating.data), content=form.content.data)
        db.session.add(r)
        db.session.commit()
        flash('Gửi đánh giá thành công. Đợi admin duyệt.', 'success')
    else:
        flash('Dữ liệu đánh giá không hợp lệ', 'danger')
    return redirect(url_for('main.ho_cau_detail', pond_id=pond.id))


# Auth routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Đăng nhập thành công', 'success')
            if user.role in ('admin','staff'):
                return redirect(url_for('admin.admin_index'))
            return redirect(url_for('main.index'))
        flash('Tên đăng nhập hoặc mật khẩu không đúng', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing:
            flash('Tên đăng nhập đã tồn tại', 'warning')
            return redirect(url_for('auth.register'))
        u = User(username=form.username.data, email=form.email.data)
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        flash('Đăng ký thành công. Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất', 'info')
    return redirect(url_for('main.index'))


# Admin routes (concise)
@admin_bp.route('/', endpoint='index')
@login_required
def admin_index():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    ponds = HoCau.query.all()
    return render_template('admin/index.html', ponds=ponds)


@admin_bp.route('/ho_cau/new', methods=['GET', 'POST'])
@login_required
def ho_cau_new():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    form = HoCauForm()
    if form.validate_on_submit():
        p = HoCau(name=form.name.data, description=form.description.data, address=form.address.data, district=form.district.data, area=form.area.data or 0, price_per_hour=form.price_per_hour.data or 0, status=form.status.data)
        db.session.add(p)
        db.session.commit()
        flash('Thêm hồ câu thành công', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/ho_cau_form.html', form=form)


@admin_bp.route('/ho_cau/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def ho_cau_edit(pid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    p = HoCau.query.get_or_404(pid)
    form = HoCauForm(obj=p)
    if form.validate_on_submit():
        p.name = form.name.data
        p.description = form.description.data
        p.address = form.address.data
        p.district = form.district.data
        p.area = form.area.data or 0
        p.price_per_hour = form.price_per_hour.data or 0
        p.status = form.status.data
        db.session.commit()
        flash('Cập nhật hồ câu thành công', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/ho_cau_form.html', form=form, pond=p)


@admin_bp.route('/ho_cau/<int:pid>/delete', methods=['POST'])
@login_required
def ho_cau_delete(pid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    p = HoCau.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Đã xóa hồ câu', 'info')
    return redirect(url_for('admin.index'))


@admin_bp.route('/ho_cau/<int:pid>/fish', methods=['GET', 'POST'])
@login_required
def admin_ho_cau_fish(pid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    pond = HoCau.query.get_or_404(pid)
    fishes = LoaiCa.query.all()
    links = HoCauLoaiCa.query.filter_by(ho_cau_id=pond.id).all()
    links_map = {l.loai_ca_id: l for l in links}
    if request.method == 'POST':
        for key, val in request.form.items():
            if not key.startswith('qty_'):
                continue
            try:
                lc_id = int(key.split('_', 1)[1])
                qty = int(val) if val else 0
            except Exception:
                continue
            link = links_map.get(lc_id)
            if link:
                link.quantity = qty
            else:
                if qty > 0:
                    nl = HoCauLoaiCa(ho_cau_id=pond.id, loai_ca_id=lc_id, quantity=qty)
                    db.session.add(nl)
        db.session.commit()
        flash('Cập nhật số lượng loại cá cho hồ thành công', 'success')
        return redirect(url_for('admin.admin_ho_cau_fish', pid=pond.id))
    return render_template('admin/ho_cau_fish.html', pond=pond, fishes=fishes, links=links_map)


@admin_bp.route('/ho_cau/<int:pid>/fish/<int:link_id>/delete', methods=['POST'])
@login_required
def admin_ho_cau_fish_delete(pid, link_id):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    link = HoCauLoaiCa.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Đã xóa loại cá khỏi hồ', 'info')
    return redirect(url_for('admin.admin_ho_cau_fish', pid=pid))


@admin_bp.route('/loai_ca')
@login_required
def loai_ca_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    fishes = LoaiCa.query.all()
    return render_template('admin/loai_ca_list.html', fishes=fishes)


@admin_bp.route('/loai_ca/new', methods=['GET', 'POST'])
@login_required
def loai_ca_new():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    form = LoaiCaForm()
    if form.validate_on_submit():
        f = LoaiCa(name=form.name.data, description=form.description.data, price=form.price.data or 0.0)
        db.session.add(f)
        db.session.commit()
        flash('Tạo loại cá thành công', 'success')
        return redirect(url_for('admin.loai_ca_list'))
    return render_template('admin/loai_ca_form.html', form=form)


@admin_bp.route('/loai_ca/<int:fid>/edit', methods=['GET', 'POST'])
@login_required
def loai_ca_edit(fid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    f = LoaiCa.query.get_or_404(fid)
    form = LoaiCaForm(obj=f)
    if form.validate_on_submit():
        f.name = form.name.data
        f.description = form.description.data
        f.price = form.price.data or 0.0
        db.session.commit()
        flash('Cập nhật loại cá thành công', 'success')
        return redirect(url_for('admin.loai_ca_list'))
    return render_template('admin/loai_ca_form.html', form=form, fish=f)


@admin_bp.route('/loai_ca/<int:fid>/delete', methods=['POST'])
@login_required
def loai_ca_delete(fid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    f = LoaiCa.query.get_or_404(fid)
    db.session.delete(f)
    db.session.commit()
    flash('Đã xóa loại cá', 'info')
    return redirect(url_for('admin.loai_ca_list'))


@admin_bp.route('/users')
@login_required
def admin_users_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users_list.html', users=users)


@admin_bp.route('/users/<int:uid>/edit', methods=['GET', 'POST'])
@login_required
def admin_user_edit(uid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    u = User.query.get_or_404(uid)
    if request.method == 'POST':
        # simple edit: role, full_name, email
        role = request.form.get('role')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        if role in ('customer','staff','admin'):
            u.role = role
        u.full_name = full_name
        u.email = email
        db.session.commit()
        flash('Cập nhật người dùng thành công', 'success')
        return redirect(url_for('admin.admin_users_list'))
    return render_template('admin/user_form.html', user=u)


@admin_bp.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
def admin_user_delete(uid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    u = User.query.get_or_404(uid)
    # Prevent deleting self
    if u.id == current_user.id:
        flash('Không thể xóa chính bạn', 'warning')
        return redirect(url_for('admin.admin_users_list'))
    db.session.delete(u)
    db.session.commit()
    flash('Đã xóa người dùng', 'info')
    return redirect(url_for('admin.admin_users_list'))


@admin_bp.route('/khuyen_mai')
@login_required
def khuyen_mai_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    promos = KhuyenMai.query.all()
    return render_template('admin/khuyen_mai_list.html', promos=promos)


@admin_bp.route('/khuyen_mai/new', methods=['GET', 'POST'])
@login_required
def khuyen_mai_new():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    form = PromotionForm()
    if form.validate_on_submit():
        km = KhuyenMai(code=form.code.data, title=form.title.data, percent=form.percent.data, start_date=form.start_date.data, end_date=form.end_date.data, active=True)
        db.session.add(km)
        db.session.commit()
        flash('Tạo khuyến mãi thành công', 'success')
        return redirect(url_for('admin.khuyen_mai_list'))
    return render_template('admin/khuyen_mai_form.html', form=form)


@admin_bp.route('/khuyen_mai/<int:kid>/edit', methods=['GET', 'POST'])
@login_required
def khuyen_mai_edit(kid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    km = KhuyenMai.query.get_or_404(kid)
    form = PromotionForm(obj=km)
    if form.validate_on_submit():
        km.code = form.code.data
        km.title = form.title.data
        km.percent = form.percent.data
        km.start_date = form.start_date.data
        km.end_date = form.end_date.data
        db.session.commit()
        flash('Cập nhật khuyến mãi thành công', 'success')
        return redirect(url_for('admin.khuyen_mai_list'))
    return render_template('admin/khuyen_mai_form.html', form=form, promo=km)


@admin_bp.route('/khuyen_mai/<int:kid>/delete', methods=['POST'])
@login_required
def khuyen_mai_delete(kid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    km = KhuyenMai.query.get_or_404(kid)
    db.session.delete(km)
    db.session.commit()
    flash('Đã xóa khuyến mãi', 'info')
    return redirect(url_for('admin.khuyen_mai_list'))


@admin_bp.route('/hoa_don')
@login_required
def hoa_don_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    invoices = HoaDon.query.order_by(HoaDon.created_at.desc()).all()
    return render_template('admin/hoa_don_list.html', invoices=invoices)


@admin_bp.route('/hoa_don/<int:inv_id>', methods=['GET', 'POST'])
@login_required
def hoa_don_view(inv_id):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    inv = HoaDon.query.get_or_404(inv_id)
    form = InvoiceForm(obj=inv)
    if form.validate_on_submit():
        inv.payment_method = form.payment_method.data
        inv.status = form.status.data
        db.session.commit()
        flash('Cập nhật hoá đơn thành công', 'success')
        return redirect(url_for('admin.hoa_don_list'))
    return render_template('admin/hoa_don_view.html', inv=inv, form=form)


@admin_bp.route('/dat_cho')
@login_required
def admin_dat_cho_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    bookings = DatCho.query.order_by(DatCho.created_at.desc()).all()
    return render_template('admin/dat_cho_list.html', bookings=bookings)


@admin_bp.route('/dat_cho/<int:b_id>/action', methods=['POST'])
@login_required
def admin_dat_cho_action(b_id):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    action = request.form.get('action')
    b = DatCho.query.get_or_404(b_id)
    if action == 'confirm':
        b.status = 'confirmed'
        flash('Đã xác nhận đặt chỗ', 'success')
    elif action == 'cancel':
        b.status = 'cancelled'
        flash('Đã hủy đặt chỗ', 'warning')
    elif action == 'complete':
        b.status = 'completed'
        flash('Đã hoàn thành đặt chỗ', 'success')
    db.session.commit()
    return redirect(url_for('admin.admin_dat_cho_list'))


@admin_bp.route('/hoat_dong')
@login_required
def admin_hoat_dong_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    activities = HoatDong.query.order_by(HoatDong.start_time.desc()).all()
    return render_template('admin/hoat_dong_list.html', activities=activities)


@admin_bp.route('/hoat_dong/new', methods=['GET', 'POST'])
@login_required
def admin_hoat_dong_new():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    # Minimal creation: pick a confirmed booking to create activity from
    if request.method == 'POST':
        dat_cho_id = request.form.get('dat_cho_id')
        b = DatCho.query.get(int(dat_cho_id)) if dat_cho_id else None
        if not b:
            flash('Đặt chỗ không hợp lệ', 'danger')
            return redirect(url_for('admin.admin_hoat_dong_new'))
        a = HoatDong(dat_cho_id=b.id, user_id=b.user_id, ho_cau_id=b.ho_cau_id, start_time=datetime.combine(b.date, b.start_time), end_time=datetime.combine(b.date, b.end_time), hours=(datetime.combine(b.date, b.end_time) - datetime.combine(b.date, b.start_time)).seconds/3600.0, status='active')
        db.session.add(a)
        db.session.commit()
        flash('Tạo hoạt động thành công', 'success')
        return redirect(url_for('admin.admin_hoat_dong_list'))
    bookings = DatCho.query.filter_by(status='confirmed').all()
    return render_template('admin/hoat_dong_form.html', bookings=bookings)


@admin_bp.route('/hoat_dong/<int:aid>/checkin', methods=['POST'])
@login_required
def hoat_dong_checkin(aid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    a = HoatDong.query.get_or_404(aid)
    a.status = 'active'
    db.session.commit()
    flash('Khách đã check-in', 'success')
    return redirect(url_for('admin.admin_hoat_dong_list'))


@admin_bp.route('/hoat_dong/<int:aid>/complete', methods=['POST'])
@login_required
def hoat_dong_complete(aid):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    a = HoatDong.query.get_or_404(aid)
    a.status = 'completed'
    # Create invoice from activity
    # If activity linked to a booking and ho_cau has price_per_hour use that
    total = 0.0
    if a.hours and a.ho_cau and a.ho_cau.price_per_hour:
        total = float(a.hours) * float(a.ho_cau.price_per_hour)
    inv = HoaDon(dat_cho_id=a.dat_cho_id, user_id=a.user_id, total=total, status='unpaid', payment_method='')
    db.session.add(inv)
    db.session.commit()
    flash('Hoạt động hoàn thành và tạo hoá đơn', 'success')
    return redirect(url_for('admin.admin_hoat_dong_list'))


@admin_bp.route('/danh_gia')
@login_required
def admin_danh_gia_list():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    reviews = DanhGia.query.order_by(DanhGia.created_at.desc()).all()
    return render_template('admin/danh_gia_list.html', reviews=reviews)


@admin_bp.route('/danh_gia/<int:r_id>/approve', methods=['POST'])
@login_required
def admin_danh_gia_approve(r_id):
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    r = DanhGia.query.get_or_404(r_id)
    r.approved = True
    db.session.commit()
    flash('Đã duyệt đánh giá', 'success')
    return redirect(url_for('admin.admin_danh_gia_list'))


@admin_bp.route('/thong_bao', methods=['GET', 'POST'])
@login_required
def admin_thong_bao():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        tb = ThongBao(user_id=None, title=title, message=message)
        db.session.add(tb)
        db.session.commit()
        flash('Gửi thông báo thành công', 'success')
        return redirect(url_for('admin.admin_thong_bao'))
    notices = ThongBao.query.order_by(ThongBao.created_at.desc()).all()
    return render_template('admin/thong_bao_list.html', notices=notices)


@admin_bp.route('/thong_ke')
@login_required
def admin_thong_ke():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    # Parse period params
    period = request.args.get('period', 'month')  # day, week, month, year, range
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    from datetime import date, datetime, timedelta

    today = date.today()
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        # compute first day next month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
    elif period == 'range' and start_str and end_str:
        try:
            start_date = datetime.fromisoformat(start_str).date()
            end_date = datetime.fromisoformat(end_str).date()
        except Exception:
            start_date = today.replace(day=1)
            end_date = today
    else:
        start_date = today.replace(day=1)
        end_date = today

    # Convert to datetimes for comparisons with DateTime columns
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Overall totals (not limited by timeframe)
    total_ponds = HoCau.query.count()
    total_fish = LoaiCa.query.count()
    total_bookings = DatCho.query.count()
    total_activities = HoatDong.query.count()
    total_invoices = HoaDon.query.count()
    total_reviews = DanhGia.query.count()

    # Totals in period
    bookings_in_period = DatCho.query.filter(DatCho.date >= start_date, DatCho.date <= end_date).count()
    activities_in_period = HoatDong.query.filter(HoatDong.start_time >= start_dt, HoatDong.start_time <= end_dt).count()
    invoices_in_period = HoaDon.query.filter(HoaDon.created_at >= start_dt, HoaDon.created_at <= end_dt).count()
    revenue_in_period = db.session.query(db.func.coalesce(db.func.sum(HoaDon.total), 0.0)).filter(HoaDon.created_at >= start_dt, HoaDon.created_at <= end_dt).scalar() or 0.0

    # Top ponds by bookings in period
    top_q = db.session.query(HoCau.id, HoCau.name, db.func.count(DatCho.id).label('cnt')).join(DatCho, DatCho.ho_cau_id == HoCau.id).filter(DatCho.date >= start_date, DatCho.date <= end_date).group_by(HoCau.id).order_by(db.desc('cnt')).limit(5).all()
    top_ponds = [{'id': r.id, 'name': r.name, 'count': r.cnt} for r in top_q]

    # Revenue per day for chart
    days = []
    revs = []
    cur = start_date
    while cur <= end_date:
        next_day = cur + timedelta(days=1)
        day_start = datetime.combine(cur, datetime.min.time())
        day_end = datetime.combine(cur, datetime.max.time())
        day_rev = db.session.query(db.func.coalesce(db.func.sum(HoaDon.total), 0.0)).filter(HoaDon.created_at >= day_start, HoaDon.created_at <= day_end).scalar() or 0.0
        days.append(cur.strftime('%Y-%m-%d'))
        revs.append(float(day_rev))
        cur = next_day

    return render_template('admin/thong_ke.html', total_ponds=total_ponds, total_fish=total_fish, total_bookings=total_bookings, total_activities=total_activities, total_invoices=total_invoices, total_reviews=total_reviews, total_revenue=revenue_in_period, bookings_in_period=bookings_in_period, activities_in_period=activities_in_period, invoices_in_period=invoices_in_period, days=days, revs=revs, top_ponds=top_ponds, start_date=start_date, end_date=end_date, period=period)


@admin_bp.route('/api/thong_ke')
@login_required
def api_thong_ke():
    if current_user.role not in ('admin','staff'):
        return jsonify({'error': 'no access'}), 403
    # accept same params as admin_thong_ke
    period = request.args.get('period', 'month')
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    from datetime import date, datetime, timedelta
    today = date.today()
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
    elif period == 'range' and start_str and end_str:
        try:
            start_date = datetime.fromisoformat(start_str).date()
            end_date = datetime.fromisoformat(end_str).date()
        except Exception:
            start_date = today.replace(day=1)
            end_date = today
    else:
        start_date = today.replace(day=1)
        end_date = today

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    bookings_in_period = DatCho.query.filter(DatCho.date >= start_date, DatCho.date <= end_date).count()
    activities_in_period = HoatDong.query.filter(HoatDong.start_time >= start_dt, HoatDong.start_time <= end_dt).count()
    invoices_in_period = HoaDon.query.filter(HoaDon.created_at >= start_dt, HoaDon.created_at <= end_dt).count()
    revenue_in_period = float(db.session.query(db.func.coalesce(db.func.sum(HoaDon.total), 0.0)).filter(HoaDon.created_at >= start_dt, HoaDon.created_at <= end_dt).scalar() or 0.0)

    top_q = db.session.query(HoCau.id, HoCau.name, db.func.count(DatCho.id).label('cnt')).join(DatCho, DatCho.ho_cau_id == HoCau.id).filter(DatCho.date >= start_date, DatCho.date <= end_date).group_by(HoCau.id).order_by(db.desc('cnt')).limit(5).all()
    top_ponds = [{'id': r.id, 'name': r.name, 'count': int(r.cnt)} for r in top_q]

    days = []
    revs = []
    cur = start_date
    while cur <= end_date:
        next_day = cur + timedelta(days=1)
        day_start = datetime.combine(cur, datetime.min.time())
        day_end = datetime.combine(cur, datetime.max.time())
        day_rev = float(db.session.query(db.func.coalesce(db.func.sum(HoaDon.total), 0.0)).filter(HoaDon.created_at >= day_start, HoaDon.created_at <= day_end).scalar() or 0.0)
        days.append(cur.strftime('%Y-%m-%d'))
        revs.append(day_rev)
        cur = next_day

    # bookings per day
    cur = start_date
    bookings_days = []
    bookings_counts = []
    while cur <= end_date:
        cnt = DatCho.query.filter(DatCho.date == cur).count()
        bookings_days.append(cur.strftime('%Y-%m-%d'))
        bookings_counts.append(int(cnt))
        cur = cur + timedelta(days=1)

    # top ponds by revenue in period
    # join HoCau <- DatCho <- HoaDon and sum HoaDon.total
    top_rev_q = db.session.query(HoCau.id, HoCau.name, db.func.coalesce(db.func.sum(HoaDon.total), 0.0).label('rev')).join(DatCho, DatCho.ho_cau_id == HoCau.id).join(HoaDon, HoaDon.dat_cho_id == DatCho.id).filter(HoaDon.created_at >= start_dt, HoaDon.created_at <= end_dt).group_by(HoCau.id).order_by(db.desc('rev')).limit(5).all()
    top_revenue = [{'id': r.id, 'name': r.name, 'revenue': float(r.rev)} for r in top_rev_q]

    return jsonify({'bookings': bookings_in_period, 'activities': activities_in_period, 'invoices': invoices_in_period, 'revenue': revenue_in_period, 'days': days, 'revs': revs, 'bookings_days': bookings_days, 'bookings_counts': bookings_counts, 'top_ponds': top_ponds, 'top_revenue': top_revenue, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'period': period})


# REST API for ponds (HoCau)
@main_bp.route('/api/ho_cau', methods=['GET', 'POST'])
def api_ho_cau_list_create():
    if request.method == 'GET':
        ponds = HoCau.query.all()
        return jsonify([{'id': p.id, 'name': p.name, 'address': p.address, 'price_per_hour': p.price_per_hour} for p in ponds])
    # POST - create (require admin/staff)
    if not current_user.is_authenticated or current_user.role not in ('admin','staff'):
        return jsonify({'error': 'no access'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    p = HoCau(name=name, description=data.get('description'), address=data.get('address'), district=data.get('district'), area=data.get('area') or 0.0, price_per_hour=data.get('price_per_hour') or 0.0, status=data.get('status') or 'open')
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name}), 201


@main_bp.route('/api/ho_cau/<int:pid>', methods=['GET', 'PUT', 'DELETE'])
def api_ho_cau_item(pid):
    p = HoCau.query.get_or_404(pid)
    if request.method == 'GET':
        return jsonify({'id': p.id, 'name': p.name, 'address': p.address, 'description': p.description, 'price_per_hour': p.price_per_hour})
    # require admin/staff for PUT/DELETE
    if not current_user.is_authenticated or current_user.role not in ('admin','staff'):
        return jsonify({'error': 'no access'}), 403
    if request.method == 'PUT':
        data = request.get_json() or {}
        p.name = data.get('name', p.name)
        p.description = data.get('description', p.description)
        p.address = data.get('address', p.address)
        p.district = data.get('district', p.district)
        p.area = data.get('area', p.area)
        p.price_per_hour = data.get('price_per_hour', p.price_per_hour)
        p.status = data.get('status', p.status)
        db.session.commit()
        return jsonify({'id': p.id, 'name': p.name})
    # DELETE
    db.session.delete(p)
    db.session.commit()
    return jsonify({'result': 'deleted'})


# REST API for fish types (LoaiCa)
@main_bp.route('/api/loai_ca', methods=['GET', 'POST'])
def api_loai_ca_list_create():
    if request.method == 'GET':
        fishes = LoaiCa.query.all()
        return jsonify([{'id': f.id, 'name': f.name, 'price': f.price} for f in fishes])
    # create
    if not current_user.is_authenticated or current_user.role not in ('admin','staff'):
        return jsonify({'error': 'no access'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    f = LoaiCa(name=name, description=data.get('description'), price=data.get('price') or 0.0)
    db.session.add(f)
    db.session.commit()
    return jsonify({'id': f.id, 'name': f.name}), 201


@main_bp.route('/api/loai_ca/<int:fid>', methods=['GET', 'PUT', 'DELETE'])
def api_loai_ca_item(fid):
    f = LoaiCa.query.get_or_404(fid)
    if request.method == 'GET':
        return jsonify({'id': f.id, 'name': f.name, 'description': f.description, 'price': f.price})
    if not current_user.is_authenticated or current_user.role not in ('admin','staff'):
        return jsonify({'error': 'no access'}), 403
    if request.method == 'PUT':
        data = request.get_json() or {}
        f.name = data.get('name', f.name)
        f.description = data.get('description', f.description)
        f.price = data.get('price', f.price)
        db.session.commit()
        return jsonify({'id': f.id, 'name': f.name})
    db.session.delete(f)
    db.session.commit()
    return jsonify({'result': 'deleted'})


@admin_bp.route('/thong_ke/export')
@login_required
def thong_ke_export():
    if current_user.role not in ('admin','staff'):
        flash('Không có quyền', 'danger')
        return redirect(url_for('main.index'))
    # reuse API logic via internal request building
    args = request.args.to_dict()
    # Build data by calling api_thong_ke (direct call)
    resp = api_thong_ke()
    if resp.status_code != 200:
        flash('Không thể xuất dữ liệu', 'danger')
        return redirect(url_for('admin.admin_thong_ke'))
    data = resp.get_json()
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ngày', 'Doanh thu'])
    for d, r in zip(data['days'], data['revs']):
        writer.writerow([d, r])
    # top ponds
    writer.writerow([])
    writer.writerow(['Top hồ', 'Lượt đặt'])
    for t in data['top_ponds']:
        writer.writerow([t['name'], t['count']])
    csv_data = output.getvalue()
    output.close()
    return Response(csv_data, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename=thong_ke_{data['start_date']}_{data['end_date']}.csv"})
