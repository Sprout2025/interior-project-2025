from flask import Blueprint, render_template, request, g, session, redirect, url_for
from sprout import db
from sprout.models import CartItem, Product
import math

bp = Blueprint('user', __name__, url_prefix='/')


# 로그인 데코레이터
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


class PaginatedItems:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = math.ceil(total / per_page) if total > 0 else 1

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None

    def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                    (num > self.page - left_current - 1 and num < self.page + right_current) or
                    num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


@bp.route('/mypage')
@login_required
def mypage():
    page = request.args.get('page', 1, type=int)
    per_page = 3  # 페이지당 3개씩 표시

    print(f"\n{'=' * 60}")
    print(f"마이페이지 장바구니 조회")
    print(f"{'=' * 60}")
    print(f"사용자: {g.user.username} (ID: {g.user.id})")
    print(f"이메일: {g.user.email}")
    print(f"전화번호: {g.user.phone}")
    print(f"페이지: {page}")

    # DB에서 장바구니 아이템 조회
    cart_items_db = CartItem.query.filter_by(user_id=g.user.id).order_by(CartItem.created_date.desc()).all()
    print(f"DB 장바구니 아이템: {len(cart_items_db)}개")

    if not cart_items_db:
        print("장바구니가 비어있습니다")
        print(f"{'=' * 60}\n")
        return render_template('mypage.html', cart_items=None)

    # DB에서 상품 정보 조회 (캐시 또는 Product 테이블)
    items_with_info = []

    for cart_item in cart_items_db:
        # 방법 1: CartItem의 캐시된 정보 사용 (빠름)
        if cart_item.name and cart_item.price:
            item_data = {
                'id': cart_item.product_id,
                'brand': cart_item.brand,
                'name': cart_item.name,
                'price': cart_item.price,
                'description': cart_item.description,
                'image_url': cart_item.image_url,
                'style': cart_item.style
            }
            items_with_info.append(item_data)
            print(f"  ✅ 캐시 매칭: {item_data['name']}")
        else:
            # 방법 2: 캐시가 없으면 Product 테이블에서 조회
            product = Product.query.get(cart_item.product_id)
            if product:
                item_data = {
                    'id': product.id,
                    'brand': product.brand,
                    'name': product.name,
                    'price': product.price,
                    'description': product.description,
                    'image_url': product.image_url,
                    'style': product.style
                }
                items_with_info.append(item_data)
                print(f"  ✅ DB 매칭: {item_data['name']}")
            else:
                print(f"  ❌ 매칭 실패: Product ID {cart_item.product_id} (상품 삭제됨)")

    print(f"최종 매칭: {len(items_with_info)}개")

    if not items_with_info:
        print("표시할 장바구니 항목이 없습니다")
        print(f"{'=' * 60}\n")
        return render_template('mypage.html', cart_items=None)

    # 3개의 이미지 이상 페이지네이션
    total = len(items_with_info)
    start = (page - 1) * per_page
    end = start + per_page
    current_items = items_with_info[start:end]

    print(f"현재 페이지: {page}/{math.ceil(total / per_page)}")
    print(f"표시 아이템: {len(current_items)}개")
    print(f"{'=' * 60}\n")

    cart_items = PaginatedItems(current_items, page, per_page, total)

    return render_template('mypage.html', cart_items=cart_items)