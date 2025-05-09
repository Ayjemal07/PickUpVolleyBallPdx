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
        const eventDateInput = document.getElementById('date');
        const eventStartTimeInput = document.getElementById('startTime');
        const eventEndTimeInput = document.getElementById('endTime');
        const eventTitleInput = document.getElementById('title');
        const eventDescriptionInput = document.getElementById('description');
        const eventLocationInput = document.getElementById('location');

        modal.style.display = 'block';

        // If it's a new event, populate the date
        if (date) {
            eventDateInput.value = date;
            eventStartTimeInput.value = '12:00';  // Default start time
            eventEndTimeInput.value = '12:00';  // Default end time
        }

        // If editing an existing event, populate the fields
        if (event) {
            eventTitleInput.value = event.title;
            eventDescriptionInput.value = event.description;
            eventLocationInput.value = event.location;
            const eventDate = new Date(event.start);
            eventDateInput.value = eventDate.toISOString().split('T')[0]; // Set date in YYYY-MM-DD format
            eventStartTimeInput.value = event.start.split('T')[1].slice(0, 5) || '12:00';
            eventEndTimeInput.value = event.end.split('T')[1].slice(0, 5) || '12:00';
            eventDateInput.dataset.eventId = event.id;  // Save the event ID for editing
        }

        document.getElementById('closeModal').onclick = function () {
            modal.style.display = 'none';
        };

    }


        // Image option toggle logic
    const imageOptionSelect = document.getElementById('imageOption');
    const existingImageContainer = document.getElementById('existingImageContainer');
    const uploadImageContainer = document.getElementById('uploadImageContainer');
    const previewImage = document.getElementById('previewImage');

    if (imageOptionSelect) {
        imageOptionSelect.addEventListener('change', function () {
            const selected = this.value;
            if (selected === 'upload') {
                uploadImageContainer.style.display = 'block';
                existingImageContainer.style.display = 'none';
                previewImage.style.display = 'none';
            } else {
                uploadImageContainer.style.display = 'none';
                existingImageContainer.style.display = 'block';
                const existingImage = document.getElementById('existingImage').value;
                if (existingImage) {
                    previewImage.src = `/static/images/${existingImage}`;
                    previewImage.style.display = 'block';
                }
            }
        });
    }

    const existingImageSelect = document.getElementById('existingImage');
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


    // Handle event form submission for creating events

    const createForm = document.getElementById('createEventForm');
    if (createForm) {
      createForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const form = e.target;
        const data = new FormData(form);
    
        try {
          const res = await fetch('/events/add', {
            method: 'POST',
            body: data,
          });
    
          if (!res.ok) {
            const err = await res.json().catch(() => ({ message: 'Unknown error' }));
            throw new Error(err.message);
          }
    
          const result = await res.json();
          alert(result.message || 'Event created!');
          form.closest('.modal').style.display = 'none';
          window.location.reload();
        } catch (err) {
          console.error('Upload failed:', err);
          alert('Failed to add event: ' + err.message);
        }
      });
    }
    

    

    // Open the modal for editing an event


    function openEditEventModal(event) {
        const modal = document.getElementById("editEventModal");
    
        document.getElementById("editEventId").value = event.id;
        document.getElementById("editTitle").value = event.title;
        document.getElementById("editDescription").value = event.description;
        document.getElementById("editDate").value = event.start.split("T")[0]; 
    
        // Convert datetime format to HH:MM
        const startTime = new Date(event.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
        const endTime = new Date(event.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
    
        document.getElementById("editStartTime").value = startTime;
        document.getElementById("editEndTime").value = endTime;
        document.getElementById("editLocation").value = event.location;
    
        modal.style.display = "block";
    }
    
    
    // Close the Edit Modal when clicking the close button
    const closeEdit = document.getElementById("closeEditModal");
    if (closeEdit) {
        closeEdit.addEventListener("click", function () {
            const modal = document.getElementById("editEventModal");
            if (modal) modal.style.display = "none";
        });
    }

    const editForm = document.getElementById("editEventForm");
    if (editForm) {
        editForm.addEventListener("submit", function (e) {
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
    
            console.log("Submitting updated event:", updatedEvent); // Debugging
    
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
                        <p class="event-going"><strong>Who's Going:</strong> ${event.going_count || 0} going</p>
                        <button class="btn btn-success custom-attend-button" data-event-id="${event.id}" ${isCanceled ? 'disabled' : ''}>
                            Attend
                        </button>
                        <div id="paypal-button-container-${event.id}" class="paypal-button-container" style="display: none;"></div>
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
});


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
        
            const rsvpModal = document.getElementById("rsvpModal");
            const rsvpEventInfo = document.getElementById("rsvpEventInfo");
            const guestCountSpan = document.getElementById("guestCount");
            const totalPriceSpan = document.getElementById("totalPrice");
        
            let guestCount = 0;
            const ticketPrice = 10; // You can pull from event.ticket_price if needed
        
            // Fill modal
            rsvpEventInfo.textContent = `${event.title}, ${event.formatted_date} • ${formatEventTime(event.start)}–${formatEventTime(event.end)}`;
            guestCountSpan.textContent = guestCount;
            totalPriceSpan.textContent = `$${ticketPrice}`;
        
            // Show modal
            rsvpModal.style.display = "block";
        
            // Guest controls
            document.getElementById("guestIncrement").onclick = () => {
                guestCount++;
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
                            cart: [{ id: `event_ticket_${eventId}`, quantity: 1 + guestCount }]
                        }),
                    });
                    const orderData = await response.json();
                    return orderData.id;
                },
                onApprove: async function(data, actions) {
                    const response = await fetch(`/api/orders/${data.orderID}/capture`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                    });
                    const orderData = await response.json();
                    const transaction = orderData.purchase_units?.[0]?.payments?.captures?.[0];
                    const resultMessage = transaction?.status === "COMPLETED"
                        ? `Transaction completed: ${transaction.id}`
                        : `Transaction failed: ${transaction?.status}`;
                    alert(resultMessage);
                },
                onInit: function(data, actions) {
                    const loadingMessage = container.querySelector(".paypal-loading");
                    if (loadingMessage) loadingMessage.remove();
                }
            }).render("#paypal-container");
        });        
    });
}

