from sprout import db
from datetime import datetime


# ===============================
# 회원 모델
# ===============================
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 관계: user.cart로 장바구니 조회 가능 (1:1 관계)
    cart = db.relationship('Cart', backref='user', uselist=False, lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'


# ===============================
# 상품 모델 (Product)
# ===============================
class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100))
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255))
    style = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Product {self.name}>'


# ===============================
# 장바구니 모델 (Cart)
# ===============================
class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, unique=True)
    username = db.Column(db.String(150))  # 사용자명 저장 (스냅샷)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 관계: cart.items로 장바구니 아이템 조회 가능
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Cart user={self.username}>'


# ===============================
# 장바구니 아이템 모델 (CartItem)
# ===============================
class CartItem(db.Model):
    __tablename__ = 'cart_item'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(150))
    product_id = db.Column(db.Integer, nullable=False)

    # 상품 정보 컬럼 (스냅샷 방식)
    brand = db.Column(db.String(100))
    name = db.Column(db.String(200))
    price = db.Column(db.Integer)
    image_url = db.Column(db.String(255))
    style = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<CartItem user={self.username} product={self.name}>'