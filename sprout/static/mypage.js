/* mypage 장바구니 찜 목록 삭제 및 수량 조절 로직 */

function removeFromCart(event, productId) {
    event.preventDefault();

    if (confirm('장바구니에서 삭제하시겠습니까?')) {
        fetch('/cart/remove', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ product_id: productId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('삭제에 실패했습니다.');
            }
        })
        .catch(error => {
            console.error('오류:', error);
            alert('오류가 발생했습니다.');
        });
    }
}

/* 수량 조절 기능 */
document.addEventListener('DOMContentLoaded', function() {
    // 수량 증가
    document.querySelectorAll('.quantity-increase').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            updateQuantity(productId, 'increase');
        });
    });

    // 수량 감소
    document.querySelectorAll('.quantity-decrease').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            updateQuantity(productId, 'decrease');
        });
    });
});

function updateQuantity(productId, action) {
    fetch('/cart/update_quantity', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            product_id: parseInt(productId),
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('수량 변경에 실패했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('오류:', error);
        alert('오류가 발생했습니다.');
    });
}