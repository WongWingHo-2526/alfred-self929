// 更新購物車數量
function updateCartQuantity(productId, quantity) {
    fetch(`/cart/update/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    }).then(() => {
        location.reload();
    });
}

// 刪除購物車商品
function removeCartItem(itemId) {
    if (confirm('確定要移除該商品嗎？')) {
        window.location.href = `/cart/remove/${itemId}`;
    }
}

// 自動隱藏alert消息
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 500);
        });
    }, 3000);
});

// 添加到購物車
function addToCart(productId) {
    const quantity = document.getElementById('quantity')?.value || 1;
    fetch(`/cart/add/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    });
}