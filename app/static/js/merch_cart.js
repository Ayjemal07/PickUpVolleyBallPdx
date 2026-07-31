document.addEventListener('DOMContentLoaded', () => {
    const CART_KEY = 'pickup_pdx_merch_cart';
    const MAX_QUANTITY = 10;

    const page = document.querySelector('.merch-cart-page');

    const shippingRate = Number(
        page.dataset.shippingRate
    );

    const cartItems =
        document.getElementById('merchCartItems');

    const emptyPage =
        document.getElementById('merchCartEmptyPage');

    const checkoutLayout =
        document.getElementById('merchCheckoutLayout');

    const checkoutForm =
        document.getElementById('merchCheckoutForm');

    const shippingFields =
        document.getElementById('merchShippingFields');

    const pickupMessage =
        document.getElementById('merchPickupMessage');

    const subtotalElement =
        document.getElementById('merchSubtotal');

    const shippingAmountElement =
        document.getElementById('merchShippingAmount');

    const totalElement =
        document.getElementById('merchTotal');

    const statusElement =
        document.getElementById('merchStatus');

    const successPanel =
        document.getElementById('merchSuccess');

    const orderNumber =
        document.getElementById('merchOrderNumber');

    const successFulfillment =
        document.getElementById(
            'merchSuccessFulfillment'
        );

    let cart = loadCart();
    let paymentInProgress = false;

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

    function money(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }

    function setStatus(message, type = '') {
        statusElement.textContent = message;

        statusElement.className =
            `merch-status ${type ? `is-${type}` : ''}`;
    }

    function selectedFulfillment() {
        return document.querySelector(
            'input[name="fulfillment_method"]:checked'
        ).value;
    }

    function subtotal() {
        return cart.reduce(
            (sum, item) =>
                sum +
                Number(item.unitPrice) * item.quantity,
            0
        );
    }

    function currentShippingAmount() {
        return selectedFulfillment() === 'shipping'
            ? shippingRate
            : 0;
    }

    function renderTotals() {
        const cartSubtotal = subtotal();
        const shipping = currentShippingAmount();

        subtotalElement.textContent =
            money(cartSubtotal);

        shippingAmountElement.textContent =
            shipping > 0 ? money(shipping) : 'Free';

        totalElement.textContent =
            money(cartSubtotal + shipping);
    }

    function setShippingRequirements(enabled) {
        const requiredFieldIds = [
            'merchShippingName',
            'merchAddressLine1',
            'merchCity',
            'merchState',
            'merchPostalCode'
        ];

        requiredFieldIds.forEach(id => {
            document.getElementById(id).required = enabled;
        });
    }

    function updateFulfillmentDisplay() {
        const shippingSelected =
            selectedFulfillment() === 'shipping';

        shippingFields.hidden = !shippingSelected;
        pickupMessage.hidden = shippingSelected;

        setShippingRequirements(shippingSelected);
        renderTotals();
    }

    function updateQuantity(index, quantity) {
        if (quantity < 1) {
            cart.splice(index, 1);
        } else {
            cart[index].quantity = Math.min(
                quantity,
                MAX_QUANTITY
            );
        }

        saveCart();
        renderCart();
    }

    function createQuantityButton(
        label,
        ariaLabel,
        handler
    ) {
        const button = document.createElement('button');

        button.type = 'button';
        button.textContent = label;
        button.setAttribute('aria-label', ariaLabel);
        button.addEventListener('click', handler);

        return button;
    }

    function renderCart() {
        cartItems.replaceChildren();

        emptyPage.hidden = cart.length > 0;
        checkoutLayout.hidden = cart.length === 0;

        cart.forEach((item, index) => {
            const row = document.createElement('article');
            row.className = 'merch-cart-page-item';

            const image = document.createElement('img');
            image.src = item.image;
            image.alt = item.name;

            const details = document.createElement('div');
            details.className = 'merch-cart-page-item-details';

            const name = document.createElement('h3');
            name.textContent = item.name;

            const meta = document.createElement('p');
            meta.textContent =
                `Size: ${item.size} · ${money(item.unitPrice)}`;

            const controls = document.createElement('div');
            controls.className = 'merch-cart-controls';

            const decrease = createQuantityButton(
                '−',
                `Decrease ${item.name}`,
                () => {
                    updateQuantity(
                        index,
                        item.quantity - 1
                    );
                }
            );

            const quantity = document.createElement('span');
            quantity.textContent = item.quantity;

            const increase = createQuantityButton(
                '+',
                `Increase ${item.name}`,
                () => {
                    updateQuantity(
                        index,
                        item.quantity + 1
                    );
                }
            );

            increase.disabled =
                item.quantity >= MAX_QUANTITY;

            const remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'merch-remove-item';
            remove.textContent = 'Remove';

            remove.addEventListener('click', () => {
                cart.splice(index, 1);
                saveCart();
                renderCart();
            });

            controls.append(
                decrease,
                quantity,
                increase,
                remove
            );

            const itemTotal = document.createElement('strong');
            itemTotal.className = 'merch-cart-item-total';

            itemTotal.textContent = money(
                Number(item.unitPrice) * item.quantity
            );

            details.append(name, meta, controls);
            row.append(image, details, itemTotal);
            cartItems.appendChild(row);
        });

        renderTotals();
    }

    document
        .querySelectorAll(
            'input[name="fulfillment_method"]'
        )
        .forEach(input => {
            input.addEventListener(
                'change',
                updateFulfillmentDisplay
            );
        });

    function checkoutPayload() {
        const fulfillmentMethod =
            selectedFulfillment();

        const payload = {
            customer: {
                name: document
                    .getElementById('merchCustomerName')
                    .value
                    .trim(),

                email: document
                    .getElementById('merchCustomerEmail')
                    .value
                    .trim(),

                phone: document
                    .getElementById('merchCustomerPhone')
                    .value
                    .trim(),

                fulfillment_method: fulfillmentMethod
            },

            items: cart.map(item => ({
                product_id: item.productId,
                size: item.size,
                quantity: item.quantity
            }))
        };

        if (fulfillmentMethod === 'shipping') {
            payload.shipping_address = {
                name: document
                    .getElementById('merchShippingName')
                    .value
                    .trim(),

                address_line_1: document
                    .getElementById('merchAddressLine1')
                    .value
                    .trim(),

                address_line_2: document
                    .getElementById('merchAddressLine2')
                    .value
                    .trim(),

                city: document
                    .getElementById('merchCity')
                    .value
                    .trim(),

                state: document
                    .getElementById('merchState')
                    .value
                    .trim(),

                postal_code: document
                    .getElementById('merchPostalCode')
                    .value
                    .trim(),

                country: document
                    .getElementById('merchCountry')
                    .value
            };
        }

        return payload;
    }

    function validateCheckout() {
        if (cart.length === 0) {
            setStatus(
                'Your cart is empty.',
                'error'
            );

            return false;
        }

        if (!checkoutForm.reportValidity()) {
            setStatus(
                'Complete the required checkout information.',
                'error'
            );

            return false;
        }

        return true;
    }

    async function apiRequest(url, options) {
        const response = await fetch(url, options);

        const data = await response
            .json()
            .catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.error ||
                'Something went wrong. Please try again.'
            );
        }

        return data;
    }

    if (window.paypal) {
        window.paypal.Buttons({
            style: {
                layout: 'vertical',
                shape: 'pill',
                label: 'paypal'
            },

            onClick(data, actions) {
                if (
                    paymentInProgress ||
                    !validateCheckout()
                ) {
                    return actions.reject();
                }

                return actions.resolve();
            },

            async createOrder() {
                paymentInProgress = true;

                setStatus(
                    'Starting secure checkout…'
                );

                try {
                    const result = await apiRequest(
                        '/api/merch/orders',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type':
                                    'application/json'
                            },
                            body: JSON.stringify(
                                checkoutPayload()
                            )
                        }
                    );

                    return result.id;
                } catch (error) {
                    paymentInProgress = false;

                    setStatus(
                        error.message,
                        'error'
                    );

                    throw error;
                }
            },

            async onApprove(data) {
                setStatus(
                    'Confirming your payment…'
                );

                const fulfillmentMethod =
                    selectedFulfillment();

                try {
                    const result = await apiRequest(
                        (
                            '/api/merch/orders/' +
                            encodeURIComponent(
                                data.orderID
                            ) +
                            '/capture'
                        ),
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type':
                                    'application/json'
                            }
                        }
                    );

                    cart = [];
                    saveCart();

                    checkoutLayout.hidden = true;
                    emptyPage.hidden = true;

                    orderNumber.textContent =
                        result.order_number;

                    if (
                        fulfillmentMethod ===
                        'event_pickup'
                    ) {
                        successFulfillment.textContent =
                            (
                                'We’ll email you to arrange ' +
                                'pickup at an upcoming event.'
                            );
                    } else {
                        successFulfillment.textContent =
                            (
                                'We’ll email you when your ' +
                                'order has been shipped.'
                            );
                    }

                    successPanel.hidden = false;

                    setStatus(
                        'Payment complete. Your order is confirmed!',
                        'success'
                    );

                    successPanel.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                } catch (error) {
                    setStatus(
                        error.message,
                        'error'
                    );
                } finally {
                    paymentInProgress = false;
                }
            },

            onCancel() {
                paymentInProgress = false;

                setStatus(
                    (
                        'Checkout was canceled. ' +
                        'Your cart is still saved.'
                    )
                );
            },

            onError(error) {
                paymentInProgress = false;

                console.error(
                    'PayPal checkout error:',
                    error
                );

                setStatus(
                    (
                        'PayPal checkout could not be ' +
                        'completed. Your cart is still saved.'
                    ),
                    'error'
                );
            }
        }).render('#merchPaypalButtons');
    } else {
        setStatus(
            (
                'PayPal checkout is unavailable. ' +
                'Confirm that PAYPAL_CLIENT_ID is configured.'
            ),
            'error'
        );
    }

    updateFulfillmentDisplay();
    renderCart();
});