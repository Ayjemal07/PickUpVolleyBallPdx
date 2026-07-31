document.addEventListener('DOMContentLoaded', () => {
    const CART_KEY = 'pickup_pdx_merch_cart';
    const MAX_QUANTITY = 10;

    const statusElement =
        document.getElementById('merchStatus');

    const cartCount =
        document.getElementById('merchHeaderCartCount');

    let cart = loadCart();

    function loadCart() {
        try {
            const saved = JSON.parse(
                localStorage.getItem(CART_KEY)
            );

            if (!Array.isArray(saved)) {
                return [];
            }

            return saved.filter(item =>
                item &&
                typeof item.productId === 'string' &&
                typeof item.name === 'string' &&
                typeof item.size === 'string' &&
                Number.isInteger(item.quantity) &&
                item.quantity >= 1 &&
                item.quantity <= MAX_QUANTITY &&
                Number.isFinite(Number(item.unitPrice))
            );
        } catch (error) {
            return [];
        }
    }

    function saveCart() {
        localStorage.setItem(
            CART_KEY,
            JSON.stringify(cart)
        );
    }

    function updateCartCount() {
        const totalItems = cart.reduce(
            (total, item) => total + item.quantity,
            0
        );

        cartCount.textContent = totalItems;
    }

    function setStatus(message, type = '') {
        statusElement.textContent = message;

        statusElement.className =
            `merch-status ${type ? `is-${type}` : ''}`;
    }

    document
        .querySelectorAll('.merch-add-button')
        .forEach(button => {
            button.addEventListener('click', () => {
                const card = button.closest(
                    '.merch-product-card'
                );

                const sizeSelect = card.querySelector(
                    '.merch-size'
                );

                const quantity = Number(
                    card.querySelector(
                        '.merch-quantity'
                    ).value
                );

                const size = sizeSelect.value;

                if (!size) {
                    sizeSelect.focus();

                    setStatus(
                        'Choose a size before adding this item.',
                        'error'
                    );

                    return;
                }

                const newItem = {
                    productId: card.dataset.productId,
                    name: card.dataset.productName,
                    size,
                    quantity,
                    unitPrice: Number(
                        card.dataset.productPrice
                    ),
                    image: card.dataset.productImage
                };

                const existing = cart.find(item =>
                    item.productId === newItem.productId &&
                    item.size === newItem.size
                );

                if (existing) {
                    if (
                        existing.quantity + quantity >
                        MAX_QUANTITY
                    ) {
                        setStatus(
                            (
                                `Maximum quantity is ` +
                                `${MAX_QUANTITY} per size.`
                            ),
                            'error'
                        );

                        return;
                    }

                    existing.quantity += quantity;
                } else {
                    cart.push(newItem);
                }

                saveCart();
                updateCartCount();

                setStatus(
                    (
                        `${newItem.name} (${newItem.size}) ` +
                        `was added to your cart.`
                    ),
                    'success'
                );

                const originalHtml = button.innerHTML;

                button.innerHTML =
                    '<i class="fa-solid fa-check"></i> Added';

                window.setTimeout(() => {
                    button.innerHTML = originalHtml;
                }, 1200);
            });
        });

    updateCartCount();
});