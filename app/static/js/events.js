document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    if (!calendarEl) {
        console.error("Calendar element not found.");
        return;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: eventsData,
        selectable: userRole === 'admin',
        dateClick: function (info) {
            if (userRole === 'admin') {
                openCreateEventModal(info.dateStr);  // Open the modal with the clicked date
            }
        },
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: '',
        },
    });

    calendar.render();

    const addEventButton = document.getElementById('addEventButton');
    if (addEventButton) {
        addEventButton.addEventListener('click', function () {
            openCreateEventModal();  // Open modal for a new event
        });
    }

    // Open the modal for creating events
    function openCreateEventModal(date = null, event = null) {
        const modal = document.getElementById('createEventModal');


        modal.style.display = 'block';
        document.querySelector('#createEventForm h2').textContent = 'Add New Event';
        const submitBtn = document.querySelector('#createEventForm button[type="submit"]');
        submitBtn.textContent = 'Add Event';

        // reset simple fields...
        document.getElementById('eventId').value = '';
        document.getElementById('title').value = '';
        document.getElementById('location').value = '';
        document.getElementById('date').value = date || '';
        document.getElementById('startTime').value = '19:00';
        document.getElementById('endTime').value   = '21:00';  // 


        // reset image pickers (your existing code)…
        existingImageSelect.selectedIndex = 0;
        existingImageSelect.disabled = false;
        previewImage.style.display = 'none';
        fileInput.value = '';

        if (window.quill) {
            window.quill.setContents([]);
        }

        // If editing an existing event, populate the fields
        if (event) {
            eventTitleInput.value = event.title;
            descriptionInput.value = event.description;
            eventLocationInput.value = event.location;
            const eventDate = new Date(event.start);
            eventDateInput.value = eventDate.toISOString().split('T')[0]; // Set date in YYYY-MM-DD format
            eventStartTimeInput.value = event.start.split('T')[1].slice(0, 5) || '12:00';
            eventEndTimeInput.value = event.end.split('T')[1].slice(0, 5) || '12:00';
            eventDateInput.dataset.eventId = event.id;  // Save the event ID for editing
        }

        // Close button should refer to the correct modal
        const closeModalButton = document.getElementById("closeModal");
        if (closeModalButton) {
            closeModalButton.addEventListener("click", function () {
                const modal = document.getElementById("createEventModal");
                modal.style.display = "none";
                document.getElementById("eventId").value = ''; // Clear on close
            });
        }

    }

        // Image option logic
    // Image option logic
    const imageOptionSelect        = document.getElementById('imageOption');
    const existingImageContainer   = document.getElementById('existingImageContainer');
    const uploadImageContainer     = document.getElementById('uploadImageContainer');
    const previewImage             = document.getElementById('previewImage');
    const existingImageSelect      = document.getElementById('existingImage');
    const fileInput                = document.getElementById('eventImage');

    if (imageOptionSelect) {
    imageOptionSelect.addEventListener('change', function () {
        if (this.value === 'upload') {
        // show file upload, hide existing list
        uploadImageContainer.style.display    = 'block';
        existingImageContainer.style.display  = 'none';
        previewImage.style.display            = 'none';

        // disable existing-select, enable file-input
        existingImageSelect.disabled = true;
        fileInput.disabled          = false;
        existingImageSelect.selectedIndex = 0;
        fileInput.value             = '';
        } else {
        // show existing list, hide file upload
        uploadImageContainer.style.display    = 'none';
        existingImageContainer.style.display  = 'block';

        // enable existing-select, disable file-input
        existingImageSelect.disabled = false;
        fileInput.disabled          = true;
        fileInput.value             = '';

        // update preview if one is already selected
        if (existingImageSelect.value) {
            previewImage.src       = `/static/images/${existingImageSelect.value}`;
            previewImage.style.display = 'block';
        } else {
            previewImage.style.display = 'none';
        }
        }
    });
    }

    // When user picks an existing image, disable file-input
    if (existingImageSelect) {
    existingImageSelect.addEventListener('change', function () {
        if (this.value) {
        fileInput.disabled = true;
        previewImage.src   = `/static/images/${this.value}`;
        previewImage.style.display = 'block';
        } else {
        fileInput.disabled = false;
        previewImage.style.display = 'none';
        }
    });
    }

    // When user picks a file, disable existing-select
    if (fileInput) {
    fileInput.addEventListener('change', function () {
        if (this.files.length > 0) {
        existingImageSelect.disabled = true;
        existingImageSelect.selectedIndex = 0;
        previewImage.style.display = 'none';
        } else {
        existingImageSelect.disabled = false;
        }
    });
    }

    // Update preview when selecting an existing image
    if (existingImageSelect) {
        existingImageSelect.addEventListener('change', function () {
            const selected = this.value;
            if (selected) {
                previewImage.src = `/static/images/${selected}`;
                previewImage.style.display = 'block';
            } else {
                previewImage.style.display = 'none';
            }
        });
    }

    // Disable existing dropdown if a new image file is uploaded
    if (fileInput && existingImageSelect) {
        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                existingImageSelect.selectedIndex = 0;
                existingImageSelect.disabled = true;
                previewImage.style.display = 'none';
            } else {
                existingImageSelect.disabled = false;
            }
        });
}


    // Handle event form submission for creating events

    const createForm = document.getElementById('createEventForm');
    if (createForm) {
        // ✅ Initialize Quill
        const quill = new Quill('#quillEditor', {
            theme: 'snow',
            placeholder: 'Write event details here...',
            modules: {
                toolbar: [
                    [{ header: [1, 2, false] }],
                    ['bold', 'italic', 'underline'],
                    [{ list: 'ordered' }, { list: 'bullet' }],
                    ['link'],
                    ['clean']
                ]
            }
        });
        window.quill = quill;


        // ✅ Form submit handler (create or edit)
        createForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const descriptionInput = document.getElementById('descriptionInput');
            if (window.quill) {
                descriptionInput.value = window.quill.root.innerHTML;
            }

            const eventId = document.getElementById('eventId').value;
            const url = eventId ? `/events/edit/${eventId}` : '/events/add';

            const formData = new FormData(createForm);

            try {
                const res = await fetch(url, {
                    method: 'POST',
                    body: formData
                });

                const result = await res.json();

                if (!res.ok) throw new Error(result.message || 'Something went wrong');

                alert(result.message || (eventId ? 'Event updated!' : 'Event created!'));
                document.getElementById('createEventModal').style.display = 'none';
                window.location.reload();
            } catch (err) {
                console.error(err);
                alert('Error: ' + err.message);
            }
        });

    }


    
    // Open the modal for editing an event


    function openEditEventModal(event) {
        const modal = document.getElementById('createEventModal');
        modal.style.display = 'block';

        document.querySelector('#createEventForm h2').textContent = 'Edit Event';
        const submitBtn = document.querySelector('#createEventForm button[type="submit"]');
        submitBtn.textContent = 'Update Event';

        document.getElementById('eventId').value = event.id;
        document.getElementById('title').value = event.title;
        document.getElementById('location').value = event.location;
        document.getElementById('date').value = event.start.split('T')[0];
        document.getElementById('startTime').value = new Date(event.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
        document.getElementById('endTime').value = new Date(event.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
        document.getElementById('guestLimit').value = event.guest_limit || 0;
        document.getElementById('ticketPrice').value = event.ticket_price || 0;
        document.getElementById('maxCapacity').value = event.max_capacity || 28;
        document.getElementById('allowGuests').checked = event.allow_guests;

        // ── NEW: load HTML into Quill AND hidden input
        if (window.quill) {
            window.quill.setContents(
            window.quill.clipboard.convert(event.description || '')
            );
        }
        document.getElementById('descriptionInput').value = event.description;


        fileInput.value = '';
        existingImageSelect.disabled = false;

        if (event.image_filename && ![...existingImageSelect.options].some(opt => opt.value === event.image_filename)) {
            const opt = new Option(event.image_filename, event.image_filename, true, true);
            existingImageSelect.add(opt);
        }


        if (event.image_filename) {
            existingImageSelect.value = event.image_filename;
            previewImage.src = `/static/images/${event.image_filename}`;
            previewImage.style.display = 'block';
        } else {
            existingImageSelect.selectedIndex = 0;
            previewImage.style.display = 'none';
        }

        

        const closeModalButton = document.getElementById("closeModal");
        if (closeModalButton) {
            closeModalButton.addEventListener("click", function () {
                const modal = document.getElementById("createEventModal");
                modal.style.display = "none";
                document.getElementById("eventId").value = '';
            });
        }
    }
    
    

    // Handle event actions (add, edit, delete, cancel)
    function handleEventActions(eventId, action, eventData = null) {
        let url = action === 'add' ? '/events/add' : `/events/${action}/${eventId}`;
        

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
            location.reload();  // Refresh to show changes
        })
        .catch(err => {
            console.error(`Action ${action} failed:`, err); 
            alert(`Error during ${action}: ${err.message}`);
        });
        
    }
    

    // Sort events by date
    function sortEventsByDate(events) {
        return events.sort((a, b) => new Date(a.start) - new Date(b.start));
    }

    // Add event listeners for editing, deleting, and canceling
    function renderEventCards(sortedEvents) {
        const eventsContainer = document.querySelector('.events-container');
        eventsContainer.innerHTML = ''; // Clear existing content
    
        sortedEvents.forEach(event => {
            const formattedDate = event.formatted_date ? event.formatted_date : 'Date Missing';
            const isCanceled = event.status === 'canceled';
            const cancellationReason = event.cancellation_reason ? event.cancellation_reason : 'No reason provided';
            const descriptionPreview = event.description ? event.description.split(' ').slice(0, 2).join(' ') + '...' : 'No description available';
            let eventCardHTML = `
                <div class="event-card ${isCanceled ? 'canceled' : ''}">
                    <div class="event-header">
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
                        
                        <!-- Admin Three-Dot Menu -->
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
                        <p class="event-location"><strong>Where:</strong> ${event.location}</p>
                        <p class="event-description"><strong>Description:</strong> ${descriptionPreview}</p>
                        <button class="see-more-button" data-event-id="${event.id}">See More</button>
                        <div class="full-description" id="desc-${event.id}" style="display: none;">
                            <p>${event.description}</p>
                            <a href="/events/${event.id}" class="btn btn-info">View Details</a>
                        </div>
                        <p class="event-going"><strong>Who's Going:</strong> ${event.rsvp_count || 0} going</p>
                        ${event.is_attending ? `
                            <div class="rsvp-box" style="margin-top: 10px;">
                                <p style="font-weight: bold; color: teal; margin: 0;">You're going!</p>
                                <a href="#" class="edit-rsvp" data-event-id="${event.id}" style="color: teal; text-decoration: underline;">Edit RSVP</a>
                            </div>
                        ` : `
                            <button class="btn btn-success custom-attend-button" data-event-id="${event.id}" ${isCanceled ? 'disabled' : ''}>
                                Attend
                            </button>
                            <div id="paypal-button-container-${event.id}" class="paypal-button-container" style="display: none;"></div>
                        `}
                    </div>
                </div>
            `;
    
            eventsContainer.insertAdjacentHTML('beforeend', eventCardHTML);

        });
        console.log("Event cards rendered successfully.");
    }
    
    if (!userRole) {
        userRole = 'user'; // Ensure it's always "user" after logout
    }
    
    console.log("Updated User Role:", userRole);
    
    

    // Format event date to show "Today", "Tomorrow", or a full date
    function formatEventDate(dateString) {
        const eventDate = new Date(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Normalize to start of today
        const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000); // Normalize to start of tomorrow

        const timeString = eventDate.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        });

        const timeZone = 'PST'; // Add your timezone abbreviation if required

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

    function attachEventListeners() {
        // SEE MORE toggle
        document.querySelectorAll('.see-more-button').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                window.location.href = `/events/${eventId}`;
            });
        });
        
        document.querySelectorAll('.edit-event').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                console.log("Edit button clicked, event ID:", eventId);
    
                const selectedEvent = eventsData.find(e => e.id == Number(eventId));
                if (selectedEvent) {
                    console.log("Editing Event:", selectedEvent);
                    openEditEventModal(selectedEvent);
                } else {
                    console.error("Event not found for ID:", eventId);
                    console.log("Available events:", eventsData);
                }
            });
        });
    
        document.querySelectorAll('.delete-event').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                handleEventActions(eventId, 'delete');
            });
        });

        //Cancellation Event Logic
        document.querySelectorAll('.cancel-event').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                document.getElementById('cancelEventId').value = eventId;
                document.getElementById('cancelEventModal').style.display = 'block';
            });
        });

        // Confirm cancellation with reason
        const confirmCancel = document.getElementById("confirmCancelEvent");
        if (confirmCancel) {
            confirmCancel.addEventListener("click", function () {
                const eventId = document.getElementById("cancelEventId").value;
                const cancellationReason = document.getElementById("cancelReason").value;
        
                fetch(`/events/cancel/${eventId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cancellation_reason: cancellationReason })
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
        
                const cancelModal = document.getElementById('cancelEventModal');
                if (cancelModal) cancelModal.style.display = 'none';
            });
        }
        

        // Close the modal
        const closeCancel = document.getElementById("closeCancelModal");
        if (closeCancel) {
            closeCancel.onclick = function () {
                const cancelModal = document.getElementById("cancelEventModal");
                if (cancelModal) cancelModal.style.display = "none";
            };
        }        

    }
        
    const sortedEvents = sortEventsByDate(eventsData);
    renderEventCards(sortedEvents);
    attachEventListeners();
    setupCustomAttendButtons();
    setupEditRsvpButtons();
});


// after DOMContentLoaded, at top of your script
const closeCreateBtn = document.getElementById('closeModal');
if (closeCreateBtn) {
  closeCreateBtn.onclick = () => {
    document.getElementById('createEventModal').style.display = 'none';
  };
}

const closeEditBtn = document.getElementById('closeEditModal');
if (closeEditBtn) {
  closeEditBtn.onclick = () => {
    document.getElementById('editEventModal').style.display = 'none';
  };
}


// Format event time for display
function formatEventTime(dateString) {
    const eventDate = new Date(dateString);
    return eventDate.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function setupCustomAttendButtons() {
    document.querySelectorAll(".custom-attend-button").forEach(button => {
        button.addEventListener("click", () => {
            const eventId = button.getAttribute("data-event-id");
            const event = eventsData.find(e => e.id == eventId);
            if (!event) return;

            if (event.rsvp_count >= event.max_capacity) {
                alert("Sorry, this event is full.");
                return;
            }
        
            const rsvpModal = document.getElementById("rsvpModal");
            const rsvpEventInfo = document.getElementById("rsvpEventInfo");
            const guestCountSpan = document.getElementById("guestCount");
            const totalPriceSpan = document.getElementById("totalPrice");
        
            let guestCount = 0;
            const ticketPrice = event.ticket_price || 12.00;;
        
            // Fill modal
            rsvpEventInfo.textContent = `${event.title}, ${event.formatted_date} • ${formatEventTime(event.start)}–${formatEventTime(event.end)}`;
            guestCountSpan.textContent = guestCount;
            totalPriceSpan.textContent = `$${ticketPrice}`;
        
            // Show modal
            rsvpModal.style.display = "block";

            if (!event.allow_guests) {
                document.querySelector('.guest-counter').style.display = 'none';
            } else {
                document.querySelector('.guest-counter').style.display = 'flex';
            }
        
            // Guest controls
            document.getElementById("guestIncrement").onclick = () => {
                if (guestCount < event.guest_limit) {
                    guestCount++;
                }
                guestCountSpan.textContent = guestCount;
                totalPriceSpan.textContent = `$${(ticketPrice * (1 + guestCount)).toFixed(2)}`;
            };
        
            document.getElementById("guestDecrement").onclick = () => {
                if (guestCount > 0) {
                    guestCount--;
                    guestCountSpan.textContent = guestCount;
                    totalPriceSpan.textContent = `$${(ticketPrice * (1 + guestCount)).toFixed(2)}`;
                }
            };
        
            // Close button
            document.getElementById("closeRsvpModal").onclick = () => {
                rsvpModal.style.display = "none";
                document.getElementById("paypal-container").innerHTML = ""; // Clear PayPal buttons
            };

            document.getElementById("closeRsvpX").onclick = () => {
                document.getElementById("rsvpModal").style.display = "none";
                document.getElementById("paypal-container").innerHTML = "";
            };
            
        
            // Render PayPal
            const container = document.getElementById("paypal-container");
            container.innerHTML = `<div class="paypal-loading">Loading payment options...</div>`;
            paypal.Buttons({
                createOrder: async function(data, actions) {
                    const response = await fetch("/api/orders", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            cart: [{ id: `event_ticket_${eventId}`, quantity: 1 + guestCount }],
                            event_id: eventId,
                            guest_count: guestCount
                        }),
                    });
                    const orderData = await response.json();
                    return orderData.id;
                },
                onApprove: async function(data, actions) {
                    const response = await fetch(`/api/orders/${data.orderID}/capture`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ event_id: eventId, guest_count: guestCount })
                    });
                    const orderData = await response.json();
                    const transaction = orderData.purchase_units?.[0]?.payments?.captures?.[0];

                    const modal = document.getElementById("rsvpModal");
                    if (modal) modal.style.display = "none";

                    if (transaction?.status === "COMPLETED") {
                        console.log("✅ Payment success - updating UI");

                        const card = document.querySelector(`.event-card .custom-attend-button[data-event-id="${eventId}"]`)?.closest('.event-card');
                        const rsvpArea = card || document.querySelector(".event-rsvp-area");
                        if (rsvpArea) {
                            rsvpArea.scrollIntoView({ behavior: 'smooth', block: 'center' });

                            const successMsg = document.createElement("div");
                            successMsg.className = "rsvp-success-message";
                            successMsg.style = "margin-top: 10px; font-weight: bold; color: green;";
                            successMsg.textContent = "🎉 Thank you! You're confirmed for this event.";
                            rsvpArea.appendChild(successMsg);

                            const attendBtn = rsvpArea.querySelector(".custom-attend-button");
                            if (attendBtn) attendBtn.remove();

                            const paypalDiv = rsvpArea.querySelector(".paypal-button-container");
                            if (paypalDiv) paypalDiv.remove();

                            // If on event_details page, replace content with RSVP box (edit + share)
                            if (!card && rsvpArea.classList.contains("event-rsvp-area")) {
                                const detailsBox = document.createElement("div");
                                detailsBox.className = "rsvp-box";
                                detailsBox.innerHTML = `
                                    <p style="font-weight: bold;">You're going!</p>
                                    <button 
                                        class="btn btn-success edit-rsvp-button"
                                        data-event-id="{{ event.id }}"
                                        data-title="{{ event.title }}"
                                        data-time="{{ event.formatted_date }} {{ event.start_time.strftime('%I:%M %p') }}"
                                        data-ticket-price="{{ '%.2f' % event.ticket_price }}"
                                        data-guest-limit="{{ event.guest_limit if event.allow_guests else 0 }}">
                                        Edit RSVP
                                    </button>
                                `;
                                rsvpArea.appendChild(detailsBox);
                            }

                            // Mini box for event cards (optional to show both on events.html)
                            if (card) {
                                const confirmBox = document.createElement("div");
                                confirmBox.className = "rsvp-box";
                                confirmBox.style = "margin-top: 10px;";
                                confirmBox.innerHTML = `
                                    <p style="font-weight: bold; color: teal; margin: 0;">You're going!</p>
                                    <a href="#" class="edit-rsvp" data-event-id="${eventId}" style="color: teal; text-decoration: underline;">Edit RSVP</a>
                                    <button class="btn btn-outline-info" style="margin-left: 10px;">
                                        Share <i class="bi bi-box-arrow-up"></i>
                                    </button>
                                `;
                                rsvpArea.appendChild(confirmBox);
                            }

                            // Optional RSVP count update
                            const rsvpCountElem = rsvpArea.querySelector(".event-going");
                            if (rsvpCountElem) {
                                let current = parseInt((rsvpCountElem.textContent.match(/\d+/) || [0])[0]);
                                rsvpCountElem.textContent = `Who's Going: ${current + 1 + guestCount} going`;
                            }

                            // Optional: Attendee refresh for event_details.html
                            const attendeeList = document.querySelector(".attendees-list");
                            if (attendeeList) {
                                const reloadButton = document.createElement("button");
                                reloadButton.className = "btn btn-sm btn-outline-secondary";
                                reloadButton.textContent = "↻ Refresh Who's Going";
                                reloadButton.onclick = () => window.location.reload();
                                rsvpArea.appendChild(reloadButton);
                            }
                        }
                    } else {
                        alert("Transaction failed. Please try again.");
                    }
                },
                onInit: function(data, actions) {
                    const loadingMessage = container.querySelector(".paypal-loading");
                    if (loadingMessage) loadingMessage.remove();
                }
            }).render("#paypal-container");
        });        
    });
}

function openAttendModal(eventId, title, time, ticketPrice, guestLimit, isEdit = false) {
    // Open modal
    document.getElementById("rsvpModal").style.display = "block";
    document.getElementById("rsvpTitle").innerText = isEdit ? "You're going!" : "You're booking:";
    document.getElementById("rsvpEventInfo").innerText = `${title} — ${time}`;

    // Reset guest count
    guestCount = 0;
    document.getElementById("guestCount").innerText = guestCount;
    currentEventId = eventId;
    currentTicketPrice = ticketPrice;
    maxGuestsAllowed = guestLimit;

    updatePrice();

    renderPayPalButtons(eventId, ticketPrice);
}


const fileInput = document.getElementById("eventImage");
const existingImageSelect = document.getElementById("existingImage");
const previewImage = document.getElementById("previewImage");
