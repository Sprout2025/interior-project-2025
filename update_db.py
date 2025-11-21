import json
import os
from datetime import datetime
from sqlalchemy import text, inspect
from sprout import create_app, db

app = create_app()

# Flask 앱 컨텍스트 시작
with app.app_context():
    print("\n" + "=" * 70)
    print("🔧 데이터베이스 업데이트 시작")
    print("=" * 70)

    # =================================================================
    # [1단계] User 테이블 업데이트
    # =================================================================
    print("\n[1단계] User 테이블 컬럼 추가")
    print("-" * 70)

    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE user ADD COLUMN phone VARCHAR(20)'))
            conn.commit()
        print("✅ phone 컬럼 추가 완료")
    except Exception as e:
        print("ℹ️  phone 컬럼은 이미 존재합니다")

    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE user ADD COLUMN address VARCHAR(300)'))
            conn.commit()
        print("✅ address 컬럼 추가 완료")
    except Exception as e:
        print("ℹ️  address 컬럼은 이미 존재합니다")

    # =================================================================
    # [2단계] Cart 테이블 생성 및 컬럼 추가
    # =================================================================
    print("\n[2단계] Cart 테이블 확인 및 업데이트")
    print("-" * 70)

    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    # Cart 테이블이 없으면 생성
    if 'cart' not in existing_tables:
        print("ℹ️  Cart 테이블이 없습니다. 새로 생성합니다...")
        db.create_all()
        print("✅ Cart 테이블 생성 완료")
    else:
        print("✅ Cart 테이블이 이미 존재합니다")

        # Cart 테이블에 username 컬럼 추가
        cart_columns = [col['name'] for col in inspector.get_columns('cart')]

        if 'username' not in cart_columns:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE cart ADD COLUMN username VARCHAR(150)'))
                    conn.commit()
                print("✅ Cart에 username 컬럼 추가 완료")
            except Exception as e:
                print(f"⚠️  Cart username 컬럼 추가 실패: {e}")
        else:
            print("ℹ️  Cart username 컬럼은 이미 존재합니다")

    # =================================================================
    # [3단계] CartItem 테이블 구조 변경 (user_id → cart_id)
    # =================================================================
    print("\n[3단계] CartItem 테이블 구조 변경")
    print("-" * 70)

    if 'cart_item' in existing_tables:
        cart_item_columns = [col['name'] for col in inspector.get_columns('cart_item')]

        # 기존 구조(user_id)에서 새 구조(cart_id)로 변경이 필요한지 확인
        has_user_id = 'user_id' in cart_item_columns
        has_cart_id = 'cart_id' in cart_item_columns

        if has_user_id and not has_cart_id:
            print("⚠️  CartItem 구조 변경 필요: user_id → cart_id")
            print("   기존 데이터를 백업하고 테이블을 재생성합니다...")

            # 기존 데이터 백업
            backup_data = []
            with db.engine.connect() as conn:
                result = conn.execute(text('SELECT * FROM cart_item'))
                for row in result:
                    backup_data.append(dict(row._mapping))
            print(f"   ✅ {len(backup_data)}개의 CartItem 백업 완료")

            # 기존 테이블 삭제
            with db.engine.connect() as conn:
                conn.execute(text('DROP TABLE cart_item'))
                conn.commit()
            print("   ✅ 기존 CartItem 테이블 삭제 완료")

            # 새 구조로 테이블 생성
            db.create_all()
            print("   ✅ 새 CartItem 테이블 생성 완료")

            # 데이터 복원
            if backup_data:
                from sprout.models import User, Cart, CartItem

                restored_count = 0
                user_carts = {}  # user_id → cart_id 매핑

                for item in backup_data:
                    try:
                        user_id = item.get('user_id')
                        username = item.get('username')
                        product_id = item.get('product_id')

                        if not user_id or not product_id:
                            continue

                        # User 존재 확인
                        user = db.session.get(User, user_id)
                        if not user:
                            continue

                        # username이 없으면 User에서 가져오기
                        if not username:
                            username = user.username

                        # Cart 생성 또는 조회
                        if user_id not in user_carts:
                            cart = Cart.query.filter_by(user_id=user_id).first()
                            if not cart:
                                cart = Cart(user_id=user_id, username=username)
                                db.session.add(cart)
                                db.session.flush()
                            elif not cart.username:
                                cart.username = username
                            user_carts[user_id] = cart.id

                        cart_id = user_carts[user_id]

                        # CartItem 생성
                        new_cart_item = CartItem(
                            cart_id=cart_id,
                            username=username,
                            product_id=product_id,
                            brand=item.get('brand'),
                            name=item.get('name'),
                            price=item.get('price'),
                            image_url=item.get('image_url'),
                            style=item.get('style'),
                        )
                        db.session.add(new_cart_item)
                        restored_count += 1

                    except Exception as e:
                        print(f"   ⚠️  데이터 복원 오류: {e}")
                        db.session.rollback()
                        continue

                db.session.commit()
                print(f"   ✅ {restored_count}개의 CartItem 복원 완료")

        elif has_cart_id:
            print("✅ CartItem 구조가 이미 최신입니다 (cart_id 사용)")

            # username 컬럼 추가 (없으면)
            if 'username' not in cart_item_columns:
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('ALTER TABLE cart_item ADD COLUMN username VARCHAR(150)'))
                        conn.commit()
                    print("✅ CartItem에 username 컬럼 추가 완료")
                except Exception as e:
                    print(f"⚠️  CartItem username 컬럼 추가 실패: {e}")
    else:
        print("ℹ️  CartItem 테이블이 없습니다. 생성합니다...")
        db.create_all()
        print("✅ CartItem 테이블 생성 완료")

    # =================================================================
    # [4단계] ViewedProduct 테이블 확인 및 username 컬럼 추가
    # =================================================================
    print("\n[4단계] ViewedProduct 테이블 확인 및 업데이트")
    print("-" * 70)

    if 'viewed_product' not in existing_tables:
        print("ℹ️  ViewedProduct 테이블이 없습니다. 새로 생성합니다...")
        db.create_all()
        print("✅ ViewedProduct 테이블 생성 완료")
    else:
        print("✅ ViewedProduct 테이블이 이미 존재합니다")

        # ViewedProduct 테이블에 username 컬럼 추가
        viewed_product_columns = [col['name'] for col in inspector.get_columns('viewed_product')]

        if 'username' not in viewed_product_columns:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE viewed_product ADD COLUMN username VARCHAR(150)'))
                    conn.commit()
                print("✅ ViewedProduct에 username 컬럼 추가 완료")
            except Exception as e:
                print(f"⚠️  ViewedProduct username 컬럼 추가 실패: {e}")
        else:
            print("ℹ️  ViewedProduct username 컬럼은 이미 존재합니다")

    # =================================================================
    # [5단계] 기존 Cart에 username 채우기
    # =================================================================
    print("\n[5단계] 기존 Cart에 username 업데이트")
    print("-" * 70)

    from sprout.models import User, Cart

    carts_without_username = Cart.query.filter(Cart.username == None).all()

    if carts_without_username:
        updated_count = 0
        for cart in carts_without_username:
            user = db.session.get(User, cart.user_id)
            if user:
                cart.username = user.username
                updated_count += 1

        db.session.commit()
        print(f"✅ {updated_count}개의 Cart username 업데이트 완료")
    else:
        print("✅ 모든 Cart에 username이 이미 설정되어 있습니다")

    # =================================================================
    # [6단계] 기존 CartItem에 username 채우기
    # =================================================================
    print("\n[6단계] 기존 CartItem에 username 업데이트")
    print("-" * 70)

    from sprout.models import CartItem

    cart_items_without_username = CartItem.query.filter(CartItem.username == None).all()

    if cart_items_without_username:
        updated_count = 0
        for item in cart_items_without_username:
            cart = db.session.get(Cart, item.cart_id)
            if cart and cart.username:
                item.username = cart.username
                updated_count += 1

        db.session.commit()
        print(f"✅ {updated_count}개의 CartItem username 업데이트 완료")
    else:
        print("✅ 모든 CartItem에 username이 이미 설정되어 있습니다")

    # =================================================================
    # [7단계] 기존 ViewedProduct에 username 채우기
    # =================================================================
    print("\n[7단계] 기존 ViewedProduct에 username 업데이트")
    print("-" * 70)

    from sprout.models import ViewedProduct

    viewed_products_without_username = ViewedProduct.query.filter(ViewedProduct.username == None).all()

    if viewed_products_without_username:
        updated_count = 0
        for viewed_product in viewed_products_without_username:
            user = db.session.get(User, viewed_product.user_id)
            if user:
                viewed_product.username = user.username
                updated_count += 1

        db.session.commit()
        print(f"✅ {updated_count}개의 ViewedProduct username 업데이트 완료")
    else:
        print("✅ 모든 ViewedProduct에 username이 이미 설정되어 있습니다")

    # =================================================================
    # [8단계] Product 테이블 생성 및 데이터 동기화
    # =================================================================
    print("\n[8단계] Product 테이블 업데이트")
    print("-" * 70)

    from sprout.models import Product

    inspector = inspect(db.engine)
    if 'product' not in inspector.get_table_names():
        print("ℹ️  Product 테이블이 없습니다. 생성합니다...")
        db.create_all()
        print("✅ Product 테이블 생성 완료")
    else:
        print("✅ Product 테이블이 이미 존재합니다")

    # JSON 파일에서 상품 데이터 동기화
    json_path = os.path.join('data', 'products.json')

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products = data.get("products", data)
        print(f"ℹ️  JSON에서 {len(products)}개의 상품 데이터 읽음")

        json_ids = [item.get("id") for item in products]

        # JSON → DB 추가
        added = 0
        for item in products:
            product_id = item.get("id")
            existing = db.session.get(Product, product_id)

            if not existing:
                product = Product(
                    id=product_id,
                    brand=item.get("brand"),
                    name=item.get("name"),
                    price=item.get("price"),
                    image_url=item.get("image_url"),
                    style=item.get("style")
                )
                db.session.add(product)
                added += 1

        db.session.commit()
        print(f"✅ {added}개의 새 상품 추가 완료")

        # DB에만 있고 JSON에 없는 상품 삭제
        all_products = Product.query.all()
        deleted = 0

        for product in all_products:
            if product.id not in json_ids:
                db.session.delete(product)
                deleted += 1

        db.session.commit()
        print(f"✅ {deleted}개의 구 상품 삭제 완료")
    else:
        print(f"⚠️  {json_path} 파일을 찾을 수 없습니다")

    # =================================================================
    # [최종 확인] DB 상태 출력
    # =================================================================
    print("\n" + "=" * 70)
    print("📊 최종 DB 상태")
    print("=" * 70)

    from sprout.models import User, Cart, CartItem, Product, ViewedProduct

    user_count = User.query.count()
    cart_count = Cart.query.count()
    cart_item_count = CartItem.query.count()
    product_count = Product.query.count()

    # ViewedProduct count는 try-except로 처리 (컬럼이 없을 수 있음)
    try:
        viewed_product_count = ViewedProduct.query.count()
        print(f"✅ ViewedProduct: {viewed_product_count}개")
    except Exception as e:
        print(f"⚠️ ViewedProduct 조회 실패: {e}")
        viewed_product_count = 0

    print(f"\n✅ User: {user_count}명")
    print(f"✅ Cart: {cart_count}개")
    print(f"✅ CartItem: {cart_item_count}개")
    print(f"✅ Product: {product_count}개")
    print(f"✅ ViewedProduct: {viewed_product_count}개")

    # Cart 상세 정보
    if cart_count > 0:
        print("\n📦 Cart 상세:")
        carts = Cart.query.all()
        for cart in carts:
            items = CartItem.query.filter_by(cart_id=cart.id).all()
            print(f"  - Cart ID {cart.id} ({cart.username}): {len(items)}개 아이템")

    print("\n" + "=" * 70)
    print("✅ 데이터베이스 업데이트 완료!")
    print("=" * 70)
    print("\n이제 서버를 실행하세요: flask run\n")