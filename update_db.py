import json
import os
from datetime import datetime
from sqlalchemy import text, inspect
from sprout import create_app, db

app = create_app()

# Flask 앱 컨텍스트 시작
with app.app_context():
    print("데이터베이스 업데이트 중...\n")

    # --- user 테이블 컬럼 추가 ---
    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE user ADD COLUMN phone VARCHAR(20)'))
            conn.commit()
        print("✅ phone 컬럼 추가 완료")
    except Exception as e:
        print("phone 컬럼은 이미 존재합니다")

    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE user ADD COLUMN address VARCHAR(300)'))
            conn.commit()
        print("✅ address 컬럼 추가 완료")
    except Exception as e:
        print("address 컬럼은 이미 존재합니다")

    # --- cart_item 테이블 컬럼 추가 ---
    print("\n🛒 cart_item 테이블 업데이트 중...")
    cart_columns = ['username', 'brand', 'name', 'price', 'description', 'image_url', 'style']
    cart_column_types = {
        'username': 'VARCHAR(150)',  #추가
        'brand': 'VARCHAR(100)',
        'name': 'VARCHAR(150)',
        'price': 'INTEGER',
        'description': 'TEXT',
        'image_url': 'VARCHAR(255)',
        'style': 'VARCHAR(50)'
    }

    inspector = inspect(db.engine)
    existing_cart_columns = [col['name'] for col in inspector.get_columns('cart_item')]

    for col in cart_columns:
        if col not in existing_cart_columns:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text(f'ALTER TABLE cart_item ADD COLUMN {col} {cart_column_types[col]}'))
                    conn.commit()
                print(f"✅ cart_item.{col} 컬럼 추가 완료")
            except Exception as e:
                print(f" cart_item.{col} 컬럼 추가 실패: {e}")
        else:
            print(f" cart_item.{col} 컬럼은 이미 존재합니다")

    # 기존 cart_item 데이터에 username 채우기
    print("\n 기존 장바구니 데이터에 username 업데이트 중...")
    try:
        from sprout.models import CartItem, User

        cart_items = CartItem.query.filter(CartItem.username == None).all()
        updated = 0

        for item in cart_items:
            user = db.session.get(User, item.user_id)
            if user:
                item.username = user.username
                updated += 1

        db.session.commit()
        print(f"✅ {updated}개의 장바구니 아이템에 username 업데이트 완료")
    except Exception as e:
        print(f" username 업데이트 중 오류: {e}")

    # --- product 테이블 생성 및 데이터 삽입 ---
    # models.py에서 Product 모델 import
    from sprout.models import Product

    inspector = inspect(db.engine)
    if 'product' not in inspector.get_table_names():
        print("\n 'product' 테이블을 새로 생성합니다...")
        db.create_all()
        print("✅ 테이블 생성 완료")
    else:
        print("\n 'product' 테이블이 이미 존재합니다")

    # JSON 파일에서 상품 데이터 읽기
    print("\n JSON 파일 읽는 중...")
    json_path = os.path.join('data', 'products.json')

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products = data.get("products", data)
        print(f"\n🛒 JSON에서 {len(products)}개의 상품 데이터를 읽었습니다.")

        json_ids = [item.get("id") for item in products]
        print(f"📊 JSON의 상품 ID: {json_ids}")

        # 1단계: JSON에 있는 상품을 DB에 추가
        print("\n" + "=" * 60)
        print(" [1단계] JSON -> DB 추가")
        print("=" * 60)

        added = 0
        for item in products:
            product_id = item.get("id")
            existing = db.session.get(Product, product_id)

            if existing:
                print(f" 이미 존재: {item.get('name')} (ID: {product_id})")
                continue

            product = Product(
                id=product_id,
                brand=item.get("brand"),
                name=item.get("name"),
                price=item.get("price"),
                description=item.get("description"),
                image_url=item.get("image_url"),
                style=item.get("style")
            )
            db.session.add(product)
            print(f"✅ 추가: {item.get('name')} (ID: {product_id})")
            added += 1

        db.session.commit()
        print(f"\n 총 {added}개의 상품이 DB에 추가되었습니다.")

        # 2단계: DB에만 있고 JSON에 없는 상품 삭제
        print("\n" + "=" * 60)
        print("[2단계] DB에서 삭제 (JSON에 없는 상품)")
        print("=" * 60)

        all_products = Product.query.all()
        deleted = 0

        for product in all_products:
            if product.id not in json_ids:
                print(f"🗑️  삭제: {product.name} (ID: {product.id})")
                db.session.delete(product)
                deleted += 1

        db.session.commit()
        print(f"\n🗑️  총 {deleted}개의 상품이 DB에서 삭제되었습니다.")

        # 최종 상태 확인
        print("=" * 60)
        print("최종 DB 상태")
        print("=" * 60)
        final_count = Product.query.count()
        print(f"✅ 현재 DB에 저장된 상품 수: {final_count}개")

    else:
        print(f"❌ {json_path} 파일을 찾을 수 없습니다. (상품 데이터 추가 생략)")

    print("\n" + "=" * 60)
    print(" 모든 DB 업데이트가 완료되었습니다!")
    print("=" * 60)
    print(" 이제 서버를 실행하세요: flask run\n")