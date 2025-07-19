
function sortEventsByDate(events) {
    if (!Array.isArray(events)) return [];
    return events.sort((a, b) => new Date(a.start) - new Date(b.start));
}

// Helper functions for date/time formatting
function formatEventDate(dateString) {
    const eventDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);

    const timeString = eventDate.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
    });

    const timeZone = 'PST';

    if (eventDate.getTime() >= today.getTime() && eventDate.getTime() < tomorrow.getTime()) {
        return `Today • ${timeString} ${timeZone}`;
    }
    if (eventDate.getTime() >= tomorrow.getTime() && eventDate.getTime() < tomorrow.getTime() + 24 * 60 * 60 * 1000) {
        return `Tomorrow • ${timeString} ${timeZone}`;
    }

    return `${eventDate.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
    })} • ${timeString} ${timeZone}`;
}

function formatEventTime(dateString) {
    const eventDate = new Date(dateString);
    return eventDate.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}


document.addEventListener('DOMContentLoaded', function () {

    // Check for a flash message and event ID from sessionStorage
    // Get flash data from session storage
    const flashMessage = sessionStorage.getItem('flashMessage');
    const flashEventId = sessionStorage.getItem('flashEventId');

    // Initial render of event cards, passing any flash message data
    const sortedEvents = sortEventsByDate(eventsData);
    renderEventCards(sortedEvents, flashMessage, flashEventId);

    // Clear the flash data after it has been rendered
    if (flashMessage && flashEventId) {
        sessionStorage.removeItem('flashMessage');
        sessionStorage.removeItem('flashEventId');
    }


    const tabs = document.querySelectorAll('.nav-tabs .nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');
    let calendarInitialized = false;
    let calendar; // Declare calendar variable in a broader scope

    tabs.forEach(tab => {
        tab.addEventListener('click', function (e) {
            e.preventDefault();

            // Deactivate all tabs and panes
            tabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active', 'show'));

            // Activate clicked tab and its corresponding pane
            this.classList.add('active');
            const activePaneId = this.getAttribute('href').substring(1);
            const activePane = document.getElementById(activePaneId);
            activePane.classList.add('active');
            // A short delay to allow the 'display: block' to take effect before adding the fade-in class
            setTimeout(() => activePane.classList.add('show'), 10);


            // Initialize or update calendar on tab view
            if (activePaneId === 'calendar-view') {
                if (!calendarInitialized) {
                    initializeCalendar();
                    calendar.render();
                    calendarInitialized = true;
                } else {
                    calendar.updateSize(); // Adjust calendar size if tab is revisited
                }
            }
        });
    });

    // Set default tab
    const defaultTab = document.querySelector('.nav-tabs .nav-link.active');
    if (defaultTab) {
        const defaultPaneId = defaultTab.getAttribute('href').substring(1);
        document.getElementById(defaultPaneId).classList.add('active', 'show');
    }
    // --- END TAB LOGIC ---

    function initializeCalendar() {
        const calendarEl = document.getElementById('calendar');

        if (!calendarEl) {
            console.error("Calendar element not found.");
            return;
        }

        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            events: eventsData,
            selectable: userRole === 'admin',
            dateClick: function (info) {
                if (userRole === 'admin') {
                    openCreateEventModal(info.dateStr); // Open the modal with the clicked date
                }
            },
            headerToolbar: {
                left: 'prev,next',
                center: 'title',
                right: '',
            },
        });
    }

    // Admin-specific functionality:
    if (userRole === 'admin') {
        const addEventButton = document.getElementById('addEventButton');
        if (addEventButton) {
            addEventButton.addEventListener('click', function () {
                openCreateEventModal(); // Open modal for a new event
            });
        }

        // Open the modal for creating events (Admin functionality)
        function openCreateEventModal(date = null, event = null) {
            const modal = document.getElementById('createEventModal');
            const eventDateInput = document.getElementById('date');
            const eventStartTimeInput = document.getElementById('startTime');
            const eventEndTimeInput = document.getElementById('endTime');
            const eventTitleInput = document.getElementById('title');
            const eventDescriptionInput = document.getElementById('description');
            const eventLocationInput = document.getElementById('location');

            modal.style.display = 'block';

            if (date) {
                eventDateInput.value = date;
                eventStartTimeInput.value = '12:00';
                eventEndTimeInput.value = '12:00';
            }

            if (event) {
                eventTitleInput.value = event.title;
                eventDescriptionInput.value = event.description;
                eventLocationInput.value = event.location;
                const eventDate = new Date(event.start);
                eventDateInput.value = eventDate.toISOString().split('T')[0];
                eventStartTimeInput.value = event.start.split('T')[1].slice(0, 5) || '12:00';
                eventEndTimeInput.value = event.end.split('T')[1].slice(0, 5) || '12:00';
                eventDateInput.dataset.eventId = event.id;
            }

            document.getElementById('closeModal').onclick = function () {
                modal.style.display = 'none';
            };
        }

        // Handle event form submission for creating events (Admin functionality)
        const createEventForm = document.getElementById('createEventForm');
        if (createEventForm) { // Ensure form exists before adding listener
            createEventForm.addEventListener('submit', function (e) {
                e.preventDefault();

                const eventData = {
                    title: document.getElementById('title').value,
                    description: document.getElementById('description').value,
                    location: document.getElementById('location').value,
                    startTime: document.getElementById('startTime').value,
                    endTime: document.getElementById('endTime').value,
                    date: document.getElementById('date').value,
                    start: `${document.getElementById('date').value}T${document.getElementById('startTime').value}`,
                    end: `${document.getElementById('date').value}T${document.getElementById('endTime').value}`,
                };

                fetch('/events/add', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(eventData),
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Error adding event');
                        }
                        return response.json();
                    })
                    .then(data => {
                        alert(data.message);
                        document.getElementById('createEventModal').style.display = 'none';
                        location.reload();
                    })
                    .catch(err => {
                        console.error(err);
                        alert('Failed to add event');
                    });
            });
        }


        // Open the modal for editing an event (Admin functionality)
        function openEditEventModal(event) {
            const modal = document.getElementById("editEventModal");

            document.getElementById("editEventId").value = event.id;
            document.getElementById("editTitle").value = event.title;
            document.getElementById("editDescription").value = event.description;
            document.getElementById("editDate").value = event.start.split("T")[0];

            const startTime = new Date(event.start).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            });
            const endTime = new Date(event.end).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            });

            document.getElementById("editStartTime").value = startTime;
            document.getElementById("editEndTime").value = endTime;
            document.getElementById("editLocation").value = event.location;

            modal.style.display = "block";
        }

        // Close the Edit Modal (Admin functionality)
        const closeEditModalButton = document.getElementById("closeEditModal");
        if (closeEditModalButton) { // Ensure button exists
            closeEditModalButton.addEventListener("click", function () {
                document.getElementById("editEventModal").style.display = "none";
            });
        }


        // Handle event form submission for editing events (Admin functionality)
        const editEventForm = document.getElementById("editEventForm");
        if (editEventForm) { // Ensure form exists
            editEventForm.addEventListener("submit", function (e) {
                e.preventDefault();

                const eventId = document.getElementById("editEventId").value;
                const updatedEvent = {
                    title: document.getElementById("editTitle").value,
                    description: document.getElementById("editDescription").value,
                    date: document.getElementById("editDate").value,
                    start_time: `${document.getElementById("editStartTime").value}`,
                    end_time: `${document.getElementById("editEndTime").value}`,
                    location: document.getElementById("editLocation").value,
                };

                console.log("Submitting updated event:", updatedEvent);

                fetch(`/events/edit/${eventId}`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(updatedEvent),
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert("Event updated successfully!");
                        location.reload();
                    })
                    .catch(err => {
                        console.error("Error updating event:", err);
                        alert(`Error updating event: ${err.message}`);
                    });

                document.getElementById("editEventModal").style.display = "none";
            });
        }

        // Confirm cancellation with reason (Admin functionality)
        const confirmCancelEventButton = document.getElementById('confirmCancelEvent');
        if (confirmCancelEventButton) { // Ensure button exists
            confirmCancelEventButton.addEventListener('click', function () {
                const eventId = document.getElementById('cancelEventId').value;
                const cancellationReason = document.getElementById('cancelReason').value;

                fetch(`/events/cancel/${eventId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            cancellation_reason: cancellationReason
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Event canceled successfully');
                        location.reload();
                    })
                    .catch(err => {
                        console.error('Error canceling event:', err);
                        alert('Failed to cancel event');
                    });

                document.getElementById('cancelEventModal').style.display = 'none';
            });
        }

        // Close the cancel modal (Admin functionality)
        const closeCancelModalButton = document.getElementById('closeCancelModal');
        if (closeCancelModalButton) { // Ensure button exists
            closeCancelModalButton.onclick = function () {
                document.getElementById('cancelEventModal').style.display = 'none';
            };
        }
    } // End of if (userRole === 'admin')

    // General event action handler (Admin functionality for delete/cancel) - moved inside admin block
    function handleEventActions(eventId, action, eventData = null) {
        let url = `/events/${action}/${eventId}`;

        fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: eventData ? JSON.stringify(eventData) : null,
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                alert(`${action.charAt(0).toUpperCase() + action.slice(1)} successful.`);
                location.reload();
            })
            .catch(err => {
                console.error(`Action ${action} failed:`, err);
                alert(`Error during ${action}: ${err.message}`);
            });
    }



function renderEventCards(sortedEvents, flashMessage, flashEventId) { // Added missing parameters
    // Select ALL containers with the class, not just the first one
    const eventsContainers = document.querySelectorAll('.events-container');

    // Loop through each container (one on Upcoming tab, one on Calendar tab)
    eventsContainers.forEach(eventsContainer => {
        eventsContainer.innerHTML = ''; // Clear existing content for this container

        sortedEvents.forEach(event => {
            const formattedDate = event.formatted_date ? event.formatted_date : 'Date Missing';
            const isCanceled = event.status === 'canceled';
            const cancellationReason = event.cancellation_reason ? event.cancellation_reason : 'No reason provided';
            const descriptionPreview = event.description ? event.description.split(' ').slice(0, 20).join(' ') + '...' : 'No description available';

            // Check if this is the card that needs the flash message
            let flashMessageHTML = '';
            if (flashMessage && flashEventId && event.id == flashEventId) {
                flashMessageHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert" style="margin-bottom: 15px;">
                        ${flashMessage}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
            }

            // The rest of your card HTML is perfect. This part generates the card.
            let eventCardHTML = `
            <div class="event-card ${isCanceled ? 'canceled' : ''}">
                ${flashMessageHTML} <div class="event-header">
                    <p class="event-date">
                        ${isCanceled
                            ? `<strong style="color: red;">${formattedDate} - Cancelled: ${cancellationReason}</strong>`
                            : formattedDate}
                    </p>
                    <h2 class="event-title">${event.title}</h2>
                    <p class="event-times">
                        <strong>Time:</strong>
                        ${formatEventTime(event.start)} - ${formatEventTime(event.end)}
                    </p>

                    ${userRole === 'admin' ? `
                        <div class="event-menu">
                            <button class="event-menu-button">⋮</button>
                            <div class="event-menu-options hidden">
                                <button class="edit-event" data-event-id="${event.id}">Edit</button>
                                <button class="delete-event" data-event-id="${event.id}">Delete</button>
                                <button class="cancel-event" data-event-id="${event.id}">Cancel</button>
                            </div>
                        </div>
                    ` : ''}
                </div>

                <div class="event-body">
                    ${event.image_filename ? `
                        <img src="/static/images/${event.image_filename}"
                        alt="Event Image"
                        style="width: 100%; max-height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;">
                    ` : ''}
                    <p class="event-location"><strong>Where:</strong> ${event.location}</p>
                    <p class="event-description"><strong>Description:</strong> ${descriptionPreview}</p>
                    <button class="see-more-button" data-event-id="${event.id}">See More</button>
                    <div class="full-description" id="desc-${event.id}" style="display: none;">
                        <p>${event.description}</p>
                        <a href="/events/${event.id}" class="btn btn-info">View Details</a>
                    </div>
                    <p class="event-going"><strong>Who's Going:</strong> ${event.rsvp_count || 0} going</p>

                    ${event.rsvp_count >= event.max_capacity ? `
                        <button class="btn btn-secondary" disabled>Event Full</button>
                    ` : event.is_attending ? `
                        <div class="rsvp-box" style="margin-top: 10px;">
                            <p style="font-weight: bold; color: teal; margin: 0;">You're going!</p>
                            <a href="#" class="edit-rsvp" data-event-id="${event.id}" style="color: teal; text-decoration: underline;">Edit RSVP</a>
                        </div>
                    ` : `
                        <button
                            class="btn btn-success custom-attend-button"
                            data-event-id="${event.id}"
                            data-title="${event.title}"
                            data-time="${event.formatted_date} ${formatEventTime(event.start)}"
                            data-ticket-price="${event.ticket_price || 0}"
                            data-guest-limit="${event.allow_guests ? (event.guest_limit || 0) : 0}"
                            data-location="${event.location}" 
                            ${isCanceled || event.rsvp_count >= event.max_capacity ? 'disabled' : ''}>
                            Attend
                        </button>
                    `}
                </div>
            </div>
        `;
        
            // Use insertAdjacentHTML for better performance than the old method
            eventsContainer.insertAdjacentHTML('beforeend', eventCardHTML);
        });
    });

    // This must be called after the cards are rendered to make the buttons work
    attachAllEventListeners();
}

    // Central function to attach all event listeners
    function attachAllEventListeners() {
        // "See More" button logic
        document.querySelectorAll('.see-more-button').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                const fullDescription = document.getElementById(`desc-${eventId}`);
                if (fullDescription.style.display === 'none') {
                    fullDescription.style.display = 'block';
                    this.textContent = 'See Less';
                } else {
                    fullDescription.style.display = 'none';
                    this.textContent = 'See More';
                }
            });
        });

        // Admin Edit/Delete/Cancel buttons (only if user is admin)
        if (userRole === 'admin') {
            document.querySelectorAll('.edit-event').forEach(button => {
                button.addEventListener('click', function () {
                    const eventId = this.getAttribute('data-event-id');
                    const selectedEvent = eventsData.find(e => e.id == Number(eventId));
                    if (selectedEvent) {
                        openEditEventModal(selectedEvent);
                    } else {
                        console.error("Event not found for ID:", eventId);
                    }
                });
            });

            document.querySelectorAll('.delete-event').forEach(button => {
                button.addEventListener('click', function () {
                    const eventId = this.getAttribute('data-event-id');
                    handleEventActions(eventId, 'delete');
                });
            });

            document.querySelectorAll('.cancel-event').forEach(button => {
                button.addEventListener('click', function () {
                    const eventId = this.getAttribute('data-event-id');
                    document.getElementById('cancelEventId').value = eventId;
                    document.getElementById('cancelEventModal').style.display = 'block';
                });
            });
        }


        // RSVP Modal Elements
        const rsvpModal = document.getElementById('rsvpModal');
        const rsvpTitle = document.getElementById('rsvpTitle');
        const rsvpEventInfo = document.getElementById('rsvpEventInfo');
        const guestCountSpan = document.getElementById('guestCount');
        const totalPriceSpan = document.getElementById('totalPriceSpan');
        const paypalContainer = document.getElementById('paypal-container');
        const guestDecrementBtn = document.getElementById('guestDecrement');
        const guestIncrementBtn = document.getElementById('guestIncrement');
        const editGuestPrompt = document.getElementById('editGuestPrompt');

        let currentTicketPrice = 0;
        let currentGuestLimit = 0;
        let currentEventId = null; // Store the event ID being processed
        let isEditingRsvp = false; // Flag to differentiate initial RSVP from edit
        let initialGuestCount = 0; // Store the guest count before editing for comparison

        // Function to update total price and re-render PayPal buttons
        function updatePriceAndPayPal(eventId, guestsSelected) {
            let totalAmount;

            if (isEditingRsvp) {
                // For edits, calculate the cost of *additional* guests only.
                const guestDifference = guestsSelected - initialGuestCount;
                totalAmount = currentTicketPrice * guestDifference;
            } else {
                // For new RSVPs, calculate the full price.
                totalAmount = currentTicketPrice * (1 + guestsSelected);
            }
            
            // Ensure the displayed price is never negative. A refund will show as $0.00.
            const displayPrice = Math.max(0, totalAmount);
            totalPriceSpan.textContent = displayPrice.toFixed(2);
            
            // Pass the actual calculated amount to the button renderer.
            renderPayPalButtons(eventId, totalAmount);
        }

        // Function to render PayPal buttons
        function renderPayPalButtons(eventId, totalAmount) {
            paypalContainer.innerHTML = ''; // Clear previous buttons

            // Only render if totalAmount is positive or it's an edit with potential refund
            // For simplicity, we'll render if totalAmount >= 0 (meaning no new payment or a payment of 0 for refund scenario)
            // The backend will handle if a payment is actually needed.
            if (totalAmount >= 0 || isEditingRsvp) {
                paypal.Buttons({
                    createOrder: async function(data, actions) {
                        const guestsSelected = parseInt(guestCountSpan.textContent);
                        const quantity = 1 + guestsSelected; // Attendee + guests

                        try {
                            const response = await fetch("/api/orders", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    event_id: eventId, // Pass event ID
                                    quantity: quantity, // Total number of people (1 + guests)
                                    is_edit: isEditingRsvp, // Tell backend if it's an edit
                                    rsvp_id: isEditingRsvp ? currentRsvpId : null, // Pass RSVP ID if editing
                                    initial_guest_count: isEditingRsvp ? initialGuestCount : 0 // Pass initial guests if editing
                                }),
                            });
                            const orderData = await response.json();
                            if (orderData.error) {
                                alert(orderData.error);
                                throw new Error(orderData.error);
                            }
                            return orderData.id;
                        } catch (error) {
                            console.error("Error creating order:", error);
                            alert("Failed to create PayPal order. Please try again.");
                            return null; // Prevent PayPal from proceeding
                        }
                    },
                    onApprove: async function(data, actions) {
                        try {
                            const response = await fetch(`/api/orders/${data.orderID}/capture`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    event_id: currentEventId, // Use the stored event ID
                                    guest_count: parseInt(guestCountSpan.textContent), // Final guest count
                                    is_edit: isEditingRsvp,
                                    rsvp_id: currentRsvpId,
                                    initial_guest_count: initialGuestCount
                                })
                            });
                            const orderData = await response.json();
                            const transaction = orderData.purchase_units?.[0]?.payments?.captures?.[0];


                            // vvv ADD THIS LOGIC vvv
                            // If a success message exists in the response, store it
                            // If a success message exists, store it AND the event ID
                            if (orderData.success_message) {
                                sessionStorage.setItem('flashMessage', orderData.success_message);
                                sessionStorage.setItem('flashEventId', currentEventId); // <-- ADD THIS LINE
                            }
                            const resultMessage = transaction?.status === "COMPLETED"
                                ? `Transaction completed: ${transaction.id}`
                                : `Transaction failed: ${transaction?.status}`;

                            rsvpModal.style.display = 'none';
                            location.reload(); // Reload to update attendee count and UI
                        } catch (error) {
                            console.error("Error capturing order:", error);
                            alert("Failed to complete PayPal transaction. Please try again.");
                        }
                    },
                    onError: function(err) {
                        console.error("PayPal button error:", err);
                        alert("An error occurred with PayPal. Please try again.");
                    }
                }).render(paypalContainer);
            } else {
        // If there's no cost, show an informational message instead of payment buttons.
                if (isEditingRsvp) {
                    paypalContainer.innerHTML = '<p style="text-align: center; font-weight: bold; color: #333;">Payment is only required for adding guests.</p>';
                }
            }
        }

        // Logic for "Attend" Button (Initial RSVP)
        document.querySelectorAll(".custom-attend-button").forEach(button => {
            button.addEventListener("click", function () {
                currentEventId = this.getAttribute("data-event-id");
                const eventTitle = this.getAttribute("data-title");
                const eventTime = this.getAttribute("data-time");
                const eventLocation = this.getAttribute("data-location"); 

                currentTicketPrice = parseFloat(this.getAttribute("data-ticket-price"));
                currentGuestLimit = parseInt(this.getAttribute("data-guest-limit"));

                isEditingRsvp = false;
                currentRsvpId = null;
                initialGuestCount = 0; // For new RSVP, initial guests is 0

                rsvpTitle.textContent = `You're booking: ${eventTitle}`;
                rsvpEventInfo.innerHTML = `When: ${eventTime}<br>Where: ${eventLocation}`;
                editGuestPrompt.textContent = `Are you bringing someone? (Max: ${currentGuestLimit})`;

                guestCountSpan.textContent = '0';
                totalPriceSpan.textContent = currentTicketPrice.toFixed(2);

                renderPayPalButtons(currentEventId, currentTicketPrice); // Render for initial booking

                rsvpModal.style.display = 'block';
            });
        });

        // Logic for "Edit RSVP" Link
        document.querySelectorAll(".edit-rsvp").forEach(link => {
            link.addEventListener("click", async function (e) {
                e.preventDefault(); // Prevent default link behavior
                currentEventId = this.getAttribute("data-event-id");

                isEditingRsvp = true;

                try {
                    const response = await fetch(`/api/user_rsvp/${currentEventId}`);
                    if (!response.ok) {
                        throw new Error('Failed to fetch RSVP details');
                    }
                    const rsvpData = await response.json();

                    if (rsvpData && rsvpData.rsvp_id) {
                        currentRsvpId = rsvpData.rsvp_id;
                        initialGuestCount = rsvpData.guest_count || 0; // Store initial guest count

                        const event = eventsData.find(e => e.id == currentEventId);
                        if (!event) {
                            console.error("Event data not found for ID:", currentEventId);
                            alert("Event details not available for editing.");
                            return;
                        }

                        currentTicketPrice = parseFloat(event.ticket_price || 0);
                        currentGuestLimit = parseInt(event.allow_guests ? (event.guest_limit || 0) : 0);

                        rsvpTitle.textContent = `Edit RSVP for: ${event.title}`;
                        // Display current user's name and guests
                        rsvpEventInfo.innerHTML = `You (${rsvpData.user_first_name} ${rsvpData.user_last_name}) are already going with <span id="currentGuestsDisplay">${initialGuestCount}</span> guests.`;
                        editGuestPrompt.textContent = `Change number of guests (Max: ${currentGuestLimit}):`;

                        guestCountSpan.textContent = initialGuestCount;
                        updatePriceAndPayPal(currentEventId, initialGuestCount); // Update price and PayPal buttons

                        rsvpModal.style.display = 'block';

                    } else {
                        alert("Could not retrieve your current RSVP. Please try again.");
                        console.error("No RSVP data found for event:", currentEventId);
                    }
                } catch (error) {
                    console.error("Error fetching RSVP for edit:", error);
                    alert("Error loading RSVP for editing. Please try again.");
                }
            });
        });

        // Guest selection logic for the modal (shared by both initial and edit)
        guestDecrementBtn.onclick = function () {
            let count = parseInt(guestCountSpan.textContent);
            if (count > 0) {
                count--;
                guestCountSpan.textContent = count;
                updatePriceAndPayPal(currentEventId, count);
            }
        };

        guestIncrementBtn.onclick = function () {
            let count = parseInt(guestCountSpan.textContent);
            if (currentGuestLimit === 0 || count < currentGuestLimit) {
                count++;
                guestCountSpan.textContent = count;
                updatePriceAndPayPal(currentEventId, count);
            }
        };

        // Close RSVP modal
        document.getElementById('closeRsvpModal').addEventListener('click', function () {
            rsvpModal.style.display = 'none';
        });
        document.getElementById('closeRsvpX').addEventListener('click', function () {
            rsvpModal.style.display = 'none';
        });
    }



    // Initial render and attach listeners when DOM is ready
    if (!userRole) {
        userRole = 'user';
    }
    console.log("Updated User Role:", userRole);
});
