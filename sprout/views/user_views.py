from flask import Blueprint, render_template, request, g, session, redirect, url_for, jsonify
from sprout import db
from sprout.models import Cart, CartItem, Product, ViewedProduct
import math
from datetime import datetime  # datetime import 추가

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
    print(f"마이페이지 조회")
    print(f"{'=' * 60}")
    print(f"사용자: {g.user.username} (ID: {g.user.id})")
    print(f"이메일: {g.user.email}")
    print(f"전화번호: {g.user.phone}")
    print(f"페이지: {page}")

    # 1. 최근 본 상품 조회 (페이지네이션 없이 최대 10개)
    print(f"\n[최근 본 상품 조회]")
    viewed_products_db = ViewedProduct.query.filter_by(user_id=g.user.id).order_by(
        ViewedProduct.viewed_date.desc()).limit(10).all()
    print(f"DB 최근 본 상품: {len(viewed_products_db)}개")

    viewed_items_with_info = []
    for viewed_product in viewed_products_db:
        # ViewedProduct의 캐시된 정보 사용
        if viewed_product.name and viewed_product.price:
            item_data = {
                'id': viewed_product.id,
                'product_id': viewed_product.product_id,
                'brand': viewed_product.brand,
                'name': viewed_product.name,
                'price': viewed_product.price,
                'image_url': viewed_product.image_url,
                'style': viewed_product.style,
                'viewed_date': viewed_product.viewed_date
            }
            viewed_items_with_info.append(item_data)
            print(f"  캐시 매칭: {item_data['name']}")
        else:
            # 캐시가 없으면 Product 테이블에서 조회
            product = Product.query.get(viewed_product.product_id)
            if product:
                item_data = {
                    'id': viewed_product.id,
                    'product_id': product.id,
                    'brand': product.brand,
                    'name': product.name,
                    'price': product.price,
                    'image_url': product.image_url,
                    'style': product.style,
                    'viewed_date': viewed_product.viewed_date
                }
                viewed_items_with_info.append(item_data)
                print(f"  ✅ DB 매칭: {item_data['name']}")
            else:
                print(f"  ❌ 매칭 실패: Product ID {viewed_product.product_id} (상품 삭제됨)")

    print(f"표시 최근 본 상품: {len(viewed_items_with_info)}개")

    # 2. 장바구니 조회
    print(f"\n[장바구니 조회]")
    cart = Cart.query.filter_by(user_id=g.user.id).first()

    if not cart:
        print("Cart가 없습니다")
        cart_items = None
    else:
        print(f"Cart ID: {cart.id}")
        cart_items_db = CartItem.query.filter_by(cart_id=cart.id).order_by(CartItem.created_date.desc()).all()
        print(f"DB 장바구니 아이템: {len(cart_items_db)}개")

        if not cart_items_db:
            print("장바구니가 비어있습니다")
            cart_items = None
        else:
            # CartItem에서 상품 정보 추출
            items_with_info = []

            for cart_item in cart_items_db:
                # CartItem의 캐시된 정보
                if cart_item.name and cart_item.price:
                    item_data = {
                        'id': cart_item.product_id,
                        'brand': cart_item.brand,
                        'name': cart_item.name,
                        'price': cart_item.price,
                        'image_url': cart_item.image_url,
                        'style': cart_item.style,
                        'quantity': cart_item.quantity  # 수량 정보 추가
                    }
                    items_with_info.append(item_data)
                    print(f"  캐시 매칭: {item_data['name']} (수량: {item_data['quantity']})")
                else:
                    # 캐시가 없으면 Product 테이블에서 조회
                    product = Product.query.get(cart_item.product_id)
                    if product:
                        item_data = {
                            'id': product.id,
                            'brand': product.brand,
                            'name': product.name,
                            'price': product.price,
                            'image_url': product.image_url,
                            'style': product.style,
                            'quantity': cart_item.quantity  # 수량 정보 추가
                        }
                        items_with_info.append(item_data)
                        print(f"  ✅ DB 매칭: {item_data['name']} (수량: {item_data['quantity']})")
                    else:
                        print(f"  ❌ 매칭 실패: Product ID {cart_item.product_id} (상품 삭제됨)")

            print(f"최종 매칭: {len(items_with_info)}개")

            if not items_with_info:
                print("표시할 장바구니 항목이 없습니다")
                cart_items = None
            else:
                # 장바구니 페이지네이션
                total = len(items_with_info)
                start = (page - 1) * per_page
                end = start + per_page
                current_items = items_with_info[start:end]

                print(f"현재 페이지: {page}/{math.ceil(total / per_page)}")
                print(f"표시 아이템: {len(current_items)}개")

                cart_items = PaginatedItems(current_items, page, per_page, total)

    print(f"{'=' * 60}\n")

    return render_template('mypage.html',
                           cart_items=cart_items,
                           viewed_products=viewed_items_with_info,
                           current_page=page)


@bp.route('/product/viewed', methods=['POST'])
@login_required
def add_viewed_product():
    data = request.get_json()
    product_id = data.get('product_id')

    print(f"\n최근 본 상품 추가 요청:")
    print(f"  - 사용자: {g.user.username} (ID: {g.user.id})")
    print(f"  - Product ID: {product_id}")

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required'}), 400

    # Product 테이블에서 상품 정보 조회
    product = db.session.get(Product, product_id)

    if not product:
        print(f"  ❌ 상품을 찾을 수 없음 (Product ID: {product_id})")
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    # 이미 최근 본 상품에 있는지 확인
    existing = ViewedProduct.query.filter_by(user_id=g.user.id, product_id=product_id).first()

    if existing:
        # 이미 있으면 viewed_date만 업데이트
        existing.viewed_date = datetime.now()
        print(f"  ✅ 기존 최근 본 상품 시간 업데이트")
    else:
        # 새로 추가 (최대 10개 제한)
        user_viewed_count = ViewedProduct.query.filter_by(user_id=g.user.id).count()

        # 10개 초과 시 가장 오래된 항목 삭제
        if user_viewed_count >= 10:
            oldest_viewed = ViewedProduct.query.filter_by(user_id=g.user.id).order_by(
                ViewedProduct.viewed_date.asc()).first()
            if oldest_viewed:
                db.session.delete(oldest_viewed)
                print(f" 가장 오래된 최근 본 상품 삭제: {oldest_viewed.name}")

        viewed_product = ViewedProduct(
            user_id=g.user.id,
            username=g.user.username,  # username 추가
            product_id=product_id,
            brand=product.brand,
            name=product.name,
            price=product.price,
            image_url=product.image_url,
            style=product.style
        )
        db.session.add(viewed_product)
        print(f"  ✅ 새 최근 본 상품 추가")

    db.session.commit()
    return jsonify({'success': True, 'message': 'Added to viewed products'})


@bp.route('/product/viewed/remove', methods=['POST'])
@login_required
def remove_viewed_product():
    data = request.get_json()
    viewed_product_id = data.get('viewed_product_id')

    print(f"\n최근 본 상품 삭제 요청:")
    print(f"  - 사용자: {g.user.username} (ID: {g.user.id})")
    print(f"  - Viewed Product ID: {viewed_product_id}")

    if not viewed_product_id:
        return jsonify({'success': False, 'message': 'Viewed Product ID is required'}), 400

    # ViewedProduct 조회
    viewed_product = ViewedProduct.query.filter_by(id=viewed_product_id, user_id=g.user.id).first()

    if not viewed_product:
        print(f"  ❌ 최근 본 상품을 찾을 수 없음")
        return jsonify({'success': False, 'message': 'Viewed product not found'}), 404

    # 삭제
    db.session.delete(viewed_product)
    db.session.commit()

    print(f"  ✅ 최근 본 상품 삭제 완료: {viewed_product.name}")
    return jsonify({'success': True, 'message': 'Removed from viewed products'})